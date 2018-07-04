FROM ubuntu:16.04
MAINTAINER Ulrich Germann <ugermann@inf.ed.ac.uk>
# This is a docker file for BUILDING the marian server
# and eserix. These are then copied over to the
# ENGINE docker image via ../engine/Dockerfile.

RUN apt-get update && apt-get install -y \
    git \
    libeigen3-dev \
    libopenblas-base \
    libopenblas-dev \
    python3-pip \
    gfortran \
    zlib1g-dev \
    g++ \
    automake \
    autoconf \
    libtool \
    libboost-all-dev \
    libgoogle-perftools-dev \
    libpcre3-dev \
    unzip \
    wget
    
#    && rm -rf /var/lib/apt/lists/*

# we need a newer version of cmake (>= 3.6) to find openblas 
WORKDIR /opt/app
RUN wget -q https://cmake.org/files/v3.11/cmake-3.11.4-Linux-x86_64.sh
RUN bash ./cmake-3.11.4-Linux-x86_64.sh --skip-license

# Build Marian
ARG MARIAN_VERSION=1.5.0
RUN wget -qO- https://github.com/marian-nmt/marian-dev/archive/${MARIAN_VERSION}.tar.gz | tar xzf -
WORKDIR /opt/app/marian.build
RUN apt-get install -y libssl-dev cmake
RUN rm -r * || true

# cmake currently doesn't find the static openblas library, so we have to use the dynamic build
# RUN ../bin/cmake -DCOMPILE_CUDA=off -DUSE_STATIC_LIBS=on -DCMAKE_BUILD_TYPE=Release \
#     ../marian-dev-${MARIAN_VERSION}
RUN ../bin/cmake -DCOMPILE_CUDA=off -DCMAKE_BUILD_TYPE=Release ../marian-dev-${MARIAN_VERSION}
RUN make -j

# Install eserix (sentence splitter)
WORKDIR /opt/app
RUN git clone https://github.com/emjotde/eserix.git --depth 1
RUN mkdir -p eserix/build && cd eserix/build && ../../bin/cmake .. && make -j


