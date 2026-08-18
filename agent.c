// hammer-agent: a deliberately tiny JSON-lines syscall adapter for a scratch image.
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define LINE 8192

static char fields[8][LINE];
static unsigned next_field;

static char *field(const char *s, const char *key) {
  char needle[96];
  snprintf(needle, sizeof needle, "\"%s\"", key);
  const char *p = strstr(s, needle);
  if (!p) return NULL;
  p += strlen(needle);
  while (*p == ' ' || *p == '\t') ++p;
  if (*p++ != ':') return NULL;
  while (*p == ' ' || *p == '\t') ++p;
  if (*p++ != '\"') return NULL;
  const char *e = strchr(p, '\"');
  if (!e) return NULL;
  size_t n = (size_t)(e - p);
  if (n >= LINE) return NULL;
  char *out = fields[next_field++ % 8];
  memcpy(out, p, n);
  out[n] = '\0';
  return out;
}

static long number(char *s, const char *key, long fallback) {
  char needle[96];
  snprintf(needle, sizeof needle, "\"%s\"", key);
  char *p = strstr(s, needle);
  if (!p) return fallback;
  p += strlen(needle);
  while (*p == ' ' || *p == '\t') ++p;
  if (*p++ != ':') return fallback;
  while (*p == ' ' || *p == '\t') ++p;
  return strtol(p, NULL, 10);
}

static void json_string(const char *s) {
  for (; *s; ++s) {
    unsigned char c = (unsigned char)*s;
    if (c == '\\' || c == '\"') { putchar('\\'); putchar(c); }
    else if (c == '\n') fputs("\\n", stdout);
    else if (c == '\r') fputs("\\r", stdout);
    else if (c == '\t') fputs("\\t", stdout);
    else if (c < 32) printf("\\u%04x", c);
    else putchar(c);
  }
}

static void fail(const char *op, int e) {
  printf("{\"ok\":false,\"op\":\""); json_string(op);
  printf("\",\"syscall\":\""); json_string(op);
  printf("\",\"errno\":%d,\"error\":\"%s\"}\n", e, strerror(e));
}

int main(void) {
  char line[LINE];
  setvbuf(stdout, NULL, _IONBF, 0);
  while (fgets(line, sizeof line, stdin)) {
    next_field = 0;
    char *op = field(line, "op");
    if (!op) { fputs("{\"ok\":false,\"error\":\"missing op\"}\n", stdout); continue; }
    if (!strcmp(op, "openat")) {
      char *path = field(line, "path");
      char *mode = field(line, "mode");
      if (!path) { fail("openat", EINVAL); continue; }
      int flags = O_RDONLY;
      mode_t permissions = 0;
      if (mode && !strcmp(mode, "write_create_truncate")) {
        flags = O_WRONLY | O_CREAT | O_TRUNC;
        permissions = 0644;
      } else if (mode && strcmp(mode, "read")) {
        fail("openat", EINVAL); continue;
      }
      long fd = syscall(SYS_openat, AT_FDCWD, path, flags, permissions);
      if (fd < 0) fail("openat", errno);
      else printf("{\"ok\":true,\"op\":\"openat\",\"syscall\":\"openat\",\"fd\":%ld,\"mode\":\"%s\"}\n", fd, mode ? mode : "read");
    } else if (!strcmp(op, "read")) {
      long fd = number(line, "fd", -1), count = number(line, "count", 4096);
      if (count < 1 || count > 4096) { fail("read", EINVAL); continue; }
      char buf[4097]; long n = syscall(SYS_read, fd, buf, (size_t)count);
      if (n < 0) fail("read", errno);
      else { buf[n] = 0; printf("{\"ok\":true,\"op\":\"read\",\"syscall\":\"read\",\"n\":%ld,\"data\":\"", n); json_string(buf); fputs("\"}\n", stdout); }
    } else if (!strcmp(op, "write")) {
      long fd = number(line, "fd", -1);
      char *data = field(line, "data");
      if (!data) { fail("write", EINVAL); continue; }
      size_t count = strlen(data);
      long n = syscall(SYS_write, fd, data, count);
      if (n < 0) fail("write", errno);
      else printf("{\"ok\":true,\"op\":\"write\",\"syscall\":\"write\",\"n\":%ld}\n", n);
    } else if (!strcmp(op, "close")) {
      long fd = number(line, "fd", -1), rc = syscall(SYS_close, fd);
      if (rc < 0) fail("close", errno);
      else printf("{\"ok\":true,\"op\":\"close\",\"syscall\":\"close\",\"fd\":%ld}\n", fd);
    } else if (!strcmp(op, "getdents64")) {
      char *path = field(line, "path");
      if (!path) { fail("getdents64", EINVAL); continue; }
      long fd = syscall(SYS_openat, AT_FDCWD, path, O_RDONLY | O_DIRECTORY, 0);
      if (fd < 0) { fail("openat", errno); continue; }
      char buf[4096]; long n = syscall(SYS_getdents64, fd, buf, sizeof buf); int saved = errno;
      syscall(SYS_close, fd);
      if (n < 0) { fail("getdents64", saved); continue; }
      printf("{\"ok\":true,\"op\":\"getdents64\",\"syscall\":\"getdents64\",\"n\":%ld,\"entries\":[", n);
      int first = 1; for (long i = 0; i < n;) { unsigned short reclen = *(unsigned short *)(buf + i + 16); char *name = buf + i + 19; if (strcmp(name, ".") && strcmp(name, "..")) { if (!first) putchar(','); putchar('\"'); json_string(name); putchar('\"'); first = 0; } if (!reclen) break; i += reclen; }
      fputs("]}\n", stdout);
    } else {
      printf("{\"ok\":false,\"error\":\"unsupported op: "); json_string(op); fputs("\"}\n", stdout);
    }
  }
  return 0;
}
