ARG BASE_IMAGE
FROM ${BASE_IMAGE} as marian
FROM ubuntu:16.04
WORKDIR /opt/app/engine
ARG GITHASH
RUN apt-get update \
    && apt-get install -y \
       libtcmalloc-minimal4 \
       perl-doc \
       python3-gdbm \
       python3-regex \
       python3-yaml \
       python3-websocket \
       libpcrecpp0v5

COPY --from=marian /opt/app/engine .
RUN dpkg -i 3rd-party.deb && rm 3rd-party.deb \
    && ldd summa_mt/bin/eserix \
       | awk '/not found/ { print $1 }' \
       | sed 's/\.so\.//;s/_/-/g'\
       | xargs apt-get install -y  \
    && ldd summa_mt/bin/marian-server \
       | awk '/not found/ { print $1 }' \
       | sed 's/\.so\.//;s/_/-/g'\
       | xargs apt-get install -y 

LABEL GITHASH=${GITHASH}
