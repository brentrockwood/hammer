// hammer-agent: a small JSON-lines adapter for explicit Linux filesystem syscalls.
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/openat2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define LINE 8192
#define MAX_FDS 1024

enum fd_kind { FD_NONE, FD_READ, FD_WRITE, FD_DIRECTORY };

static enum fd_kind fd_kinds[MAX_FDS];
static int work_fd = -1;
static int append_enabled = 0;

static const char *value_start(const char *json, const char *key) {
  char needle[96];
  snprintf(needle, sizeof needle, "\"%s\"", key);
  const char *p = strstr(json, needle);
  if (!p) return NULL;
  p += strlen(needle);
  while (*p == ' ' || *p == '\t') ++p;
  if (*p++ != ':') return NULL;
  while (*p == ' ' || *p == '\t') ++p;
  return p;
}

static int hex_digit(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}

static int string_field(const char *json, const char *key, char *out, size_t cap) {
  const char *p = value_start(json, key);
  if (!p || *p++ != '"') return 0;
  size_t n = 0;
  while (*p && *p != '"') {
    unsigned char c = (unsigned char)*p++;
    if (c == '\\') {
      c = (unsigned char)*p++;
      if (c == '"' || c == '\\' || c == '/') { }
      else if (c == 'b') c = '\b';
      else if (c == 'f') c = '\f';
      else if (c == 'n') c = '\n';
      else if (c == 'r') c = '\r';
      else if (c == 't') c = '\t';
      else if (c == 'u') {
        int a = hex_digit(p[0]), b = hex_digit(p[1]);
        int d = hex_digit(p[2]), e = hex_digit(p[3]);
        if (a < 0 || b < 0 || d < 0 || e < 0) return 0;
        unsigned value = (unsigned)((a << 12) | (b << 8) | (d << 4) | e);
        if (value == 0 || value > 0x7f) return 0; // ASCII, but never C-string NUL.
        c = (unsigned char)value;
        p += 4;
      } else return 0;
    }
    if (n + 1 >= cap) return 0;
    out[n++] = (char)c;
  }
  if (*p != '"') return 0;
  out[n] = '\0';
  return 1;
}

static long number_field(const char *json, const char *key, long fallback) {
  const char *p = value_start(json, key);
  if (!p) return fallback;
  char *end = NULL;
  long value = strtol(p, &end, 10);
  return end == p ? fallback : value;
}

static void json_bytes(const char *data, size_t length) {
  for (size_t i = 0; i < length; ++i) {
    unsigned char c = (unsigned char)data[i];
    if (c == '\\' || c == '"') { putchar('\\'); putchar(c); }
    else if (c == '\b') fputs("\\b", stdout);
    else if (c == '\f') fputs("\\f", stdout);
    else if (c == '\n') fputs("\\n", stdout);
    else if (c == '\r') fputs("\\r", stdout);
    else if (c == '\t') fputs("\\t", stdout);
    else if (c < 32 || c >= 127) printf("\\u%04x", c);
    else putchar(c);
  }
}

static void fail_named(const char *op, const char *syscall_name, int error) {
  printf("{\"ok\":false,\"op\":\""); json_bytes(op, strlen(op));
  printf("\",\"syscall\":\""); json_bytes(syscall_name, strlen(syscall_name));
  printf("\",\"errno\":%d,\"error\":\"", error);
  const char *message = strerror(error); json_bytes(message, strlen(message));
  fputs("\"}\n", stdout);
}

static void reject(const char *op, int error) {
  printf("{\"ok\":false,\"op\":\""); json_bytes(op, strlen(op));
  printf("\",\"syscall\":null,\"phase\":\"validation\",\"errno\":%d,\"error\":\"", error);
  const char *message = strerror(error); json_bytes(message, strlen(message));
  fputs("\"}\n", stdout);
}

static int relative_work_path(const char *path, char *relative, size_t cap) {
  if (strcmp(path, "/work") == 0 || strcmp(path, "/work/") == 0) {
    if (cap < 2) return 0;
    strcpy(relative, ".");
    return 1;
  }
  if (strncmp(path, "/work/", 6) != 0) return 0;
  const char *p = path + 6;
  size_t n = strlen(p);
  if (n == 0 || n + 1 > cap) return 0;
  const char *component = p;
  for (const char *cursor = p;; ++cursor) {
    if (*cursor == '/' || *cursor == '\0') {
      size_t length = (size_t)(cursor - component);
      if (length == 0 || (length == 1 && component[0] == '.') ||
          (length == 2 && component[0] == '.' && component[1] == '.')) return 0;
      if (*cursor == '\0') break;
      component = cursor + 1;
    }
  }
  memcpy(relative, p, n + 1);
  return 1;
}

static int tracked_fd(long fd, enum fd_kind expected) {
  return fd >= 0 && fd < MAX_FDS && fd_kinds[fd] == expected;
}

static void handle_openat(const char *line) {
  char path[LINE], relative[LINE], mode[64] = "read";
  if (!string_field(line, "path", path, sizeof path)) { reject("openat", EINVAL); return; }
  const char *mode_value = value_start(line, "mode");
  if (mode_value && !string_field(line, "mode", mode, sizeof mode)) { reject("openat", EINVAL); return; }
  if (!relative_work_path(path, relative, sizeof relative)) { reject("openat", EPERM); return; }

  struct open_how how = {
    .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
  };
  enum fd_kind kind;
  if (!strcmp(mode, "read")) {
    how.flags = O_RDONLY; kind = FD_READ;
  } else if (!strcmp(mode, "read_directory")) {
    how.flags = O_RDONLY | O_DIRECTORY; kind = FD_DIRECTORY;
  } else if (!strcmp(mode, "write_create_truncate")) {
    how.flags = O_WRONLY | O_CREAT | O_TRUNC;
    how.mode = 0644; kind = FD_WRITE;
  } else if (!strcmp(mode, "write_append_create") && append_enabled) {
    how.flags = O_WRONLY | O_CREAT | O_APPEND;
    how.mode = 0644; kind = FD_WRITE;
  } else { reject("openat", EINVAL); return; }

  long fd = syscall(SYS_openat2, work_fd, relative, &how, sizeof how);
  if (fd < 0) { fail_named("openat", "openat2", errno); return; }
  if (fd >= MAX_FDS) { syscall(SYS_close, fd); reject("openat", EMFILE); return; }
  fd_kinds[fd] = kind;
  printf("{\"ok\":true,\"op\":\"openat\",\"syscall\":\"openat2\",\"fd\":%ld,\"mode\":\"", fd);
  json_bytes(mode, strlen(mode)); fputs("\"}\n", stdout);
}

static void handle_read(const char *line) {
  long fd = number_field(line, "fd", -1), count = number_field(line, "count", 4096);
  if (!tracked_fd(fd, FD_READ)) { reject("read", EBADF); return; }
  if (count < 1 || count > 4096) { reject("read", EINVAL); return; }
  char buffer[4096]; long n = syscall(SYS_read, fd, buffer, (size_t)count);
  if (n < 0) { fail_named("read", "read", errno); return; }
  printf("{\"ok\":true,\"op\":\"read\",\"syscall\":\"read\",\"n\":%ld,\"data\":\"", n);
  json_bytes(buffer, (size_t)n); fputs("\"}\n", stdout);
}

static void handle_write(const char *line) {
  long fd = number_field(line, "fd", -1);
  char data[LINE];
  if (!tracked_fd(fd, FD_WRITE)) { reject("write", EBADF); return; }
  if (!string_field(line, "data", data, sizeof data)) { reject("write", EINVAL); return; }
  size_t count = strlen(data); long n = syscall(SYS_write, fd, data, count);
  if (n < 0) fail_named("write", "write", errno);
  else printf("{\"ok\":true,\"op\":\"write\",\"syscall\":\"write\",\"n\":%ld}\n", n);
}

static void handle_close(const char *line) {
  long fd = number_field(line, "fd", -1);
  if (fd < 0 || fd >= MAX_FDS || fd_kinds[fd] == FD_NONE) { reject("close", EBADF); return; }
  long rc = syscall(SYS_close, fd);
  if (rc < 0) { fail_named("close", "close", errno); return; }
  fd_kinds[fd] = FD_NONE;
  printf("{\"ok\":true,\"op\":\"close\",\"syscall\":\"close\",\"fd\":%ld}\n", fd);
}

static void handle_getdents64(const char *line) {
  long fd = number_field(line, "fd", -1), count = number_field(line, "count", 4096);
  if (!tracked_fd(fd, FD_DIRECTORY)) { reject("getdents64", EBADF); return; }
  if (count < 512 || count > 4096) { reject("getdents64", EINVAL); return; }
  char buffer[4096]; long n = syscall(SYS_getdents64, fd, buffer, (size_t)count);
  if (n < 0) { fail_named("getdents64", "getdents64", errno); return; }

  for (long offset = 0; offset < n;) {
    if (offset + 19 > n) { fail_named("getdents64", "getdents64", EIO); return; }
    unsigned short record_length;
    memcpy(&record_length, buffer + offset + 16, sizeof record_length);
    if (record_length < 19 || offset + record_length > n) { fail_named("getdents64", "getdents64", EIO); return; }
    size_t name_space = (size_t)record_length - 19;
    if (strnlen(buffer + offset + 19, name_space) == name_space) { fail_named("getdents64", "getdents64", EIO); return; }
    offset += record_length;
  }

  printf("{\"ok\":true,\"op\":\"getdents64\",\"syscall\":\"getdents64\",\"n\":%ld,\"eof\":%s,\"entries\":[", n, n == 0 ? "true" : "false");
  int first = 1;
  for (long offset = 0; offset < n;) {
    unsigned short record_length;
    memcpy(&record_length, buffer + offset + 16, sizeof record_length);
    char *name = buffer + offset + 19;
    size_t length = strlen(name);
    if (strcmp(name, ".") && strcmp(name, "..")) {
      if (!first) putchar(',');
      putchar('"'); json_bytes(name, length); putchar('"'); first = 0;
    }
    offset += record_length;
  }
  fputs("]}\n", stdout);
}

int main(int argc, char **argv) {
  if (argc == 2 && !strcmp(argv[1], "--append")) append_enabled = 1;
  else if (argc != 1) return 2;
  char line[LINE];
  setvbuf(stdout, NULL, _IONBF, 0);
  work_fd = (int)syscall(SYS_openat, AT_FDCWD, "/work", O_RDONLY | O_DIRECTORY, 0);
  if (work_fd < 0) { fail_named("bootstrap_openat", "openat", errno); return 1; }

  while (fgets(line, sizeof line, stdin)) {
    char op[64];
    if (!string_field(line, "op", op, sizeof op)) {
      fputs("{\"ok\":false,\"error\":\"missing or invalid op\"}\n", stdout);
    } else if (!strcmp(op, "openat")) handle_openat(line);
    else if (!strcmp(op, "read")) handle_read(line);
    else if (!strcmp(op, "write")) handle_write(line);
    else if (!strcmp(op, "close")) handle_close(line);
    else if (!strcmp(op, "getdents64")) handle_getdents64(line);
    else {
      fputs("{\"ok\":false,\"error\":\"unsupported op: ", stdout);
      json_bytes(op, strlen(op)); fputs("\"}\n", stdout);
    }
  }
  syscall(SYS_close, work_fd);
  return 0;
}
