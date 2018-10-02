FROM summaplatform/mt-build-environment as builder
WORKDIR /opt/app
COPY . .
RUN make engine

FROM ubuntu:16.04
WORKDIR /opt/app
COPY --from=builder /opt/app/engine .
RUN apt-get update \
    && apt-get install -y \
       libtcmalloc-minimal4 \
       python3-regex \
       python3-websocket \
       libpcrecpp0v5 \
    && dpkg -i 3rd-party.deb && rm 3rd-party.deb \
    && ldd bin/eserix \
       | awk '/not found/ { print $1 }' \
       | sed 's/\.so\.//;s/_/-/g'\
       | xargs apt-get install -y  \
    && ldd bin/marian-server \
       | awk '/not found/ { print $1 }' \
       | sed 's/\.so\.//;s/_/-/g'\
       | xargs apt-get install -y 
