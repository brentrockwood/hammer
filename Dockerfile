# The compiler exists only in this build stage, never in the experimental image.
FROM alpine:3.22 AS build
RUN apk add --no-cache build-base musl-dev linux-headers
WORKDIR /src
COPY agent.c .
RUN gcc -static -Os -s -Wall -Wextra -Werror -o agent agent.c

# Intentionally no shell, libc userspace, package manager, or compiler.
FROM scratch
COPY --from=build /src/agent /agent
COPY fixtures/work /work
ENTRYPOINT ["/agent"]
