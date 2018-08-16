FROM ubuntu:16.04
MAINTAINER Ulrich Germann <ugermann@inf.ed.ac.uk>
# This is a docker file for BUILDING the marian server
# and eserix. These are then copied over to the
# ENGINE docker image via ../engine/Dockerfile.

# wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB
RUN apt-get update 
RUN apt-get install -y git \
    apt-transport-https \
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

COPY GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB .
RUN apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB \
    && echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mkl.list 
RUN apt-get update && apt-get install -y  intel-mkl-64bit-2018.2-046 

    
#    && rm -rf /var/lib/apt/lists/*

# we need a newer version of cmake (>= 3.6) to find openblas 
WORKDIR /opt/app
# We don't need cmake > 3.6 if we are using MKL
# RUN wget -q https://cmake.org/files/v3.11/cmake-3.11.4-Linux-x86_64.sh
# RUN bash ./cmake-3.11.4-Linux-x86_64.sh --skip-license

RUN apt-get install -y libssl-dev cmake

# Install eserix (sentence splitter)
WORKDIR /opt/app
RUN git clone https://github.com/emjotde/eserix.git --depth 1
RUN mkdir -p eserix/build && cd eserix/build && cmake .. && make -j

# Build Marian
# We replace -march=native by -march=x86-64 for maximum portability.
# I suspect that some of the crashes we've observed are due to incompatibility
# between the CPU architecture of the host that compiled Marian for the
# image and the hosts that eventually run the container.

ARG MARIAN_VERSION=1.6.0
RUN wget -qO- https://github.com/marian-nmt/marian-dev/archive/${MARIAN_VERSION}.tar.gz | tar xzf - 
RUN grep -rl 'march=native' . | xargs sed -i 's/march=native/march=x86-64 -mavx/'

WORKDIR /opt/app/marian.build
# RUN rm -r * || true

# # cmake currently doesn't find the static openblas library, so we have to use the dynamic build
# RUN cmake -DCOMPILE_CUDA=off -DUSE_STATIC_LIBS=on -DCMAKE_BUILD_TYPE=Release ../marian-dev-${MARIAN_VERSION}
# RUN cmake -DCOMPILE_CUDA=off -DUSE_STATIC_LIBS=on -DCMAKE_BUILD_TYPE=Release \
#     ../marian-dev-${MARIAN_VERSION}
RUN cmake -DCOMPILE_CUDA=off -DUSE_STATIC_LIBS=on -DCMAKE_BUILD_TYPE=Release ../marian-dev-${MARIAN_VERSION}
RUN make -j


# TO DO
# - clean up the installed packages. We probably  don't need openblas and eigen any more.
# - compile marian staticly
