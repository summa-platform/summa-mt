FROM ubuntu:16.04
MAINTAINER Ulrich Germann <ugermann@inf.ed.ac.uk>
# This is a docker file for BUILDING the marian server
# and eserix. These are then copied over to the
# ENGINE docker image via ../engine/Dockerfile.

# wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB

# Intel MKL is so expensive to install that we install it as on one of the first
# Docker layers
COPY GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB .
RUN apt-get update \
    && apt-get install -y apt-transport-https \
    && apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB \
    && echo deb https://apt.repos.intel.com/mkl all main >/etc/apt/sources.list.d/intel-mkl.list \
    && apt-get update && apt-get install -y  intel-mkl-64bit-2018.2-046

RUN apt-get install -y \
    autoconf \
    automake \
    cmake \
    g++ \
    libssl-dev \
    libtool \
    libboost-all-dev \
    libgoogle-perftools-dev \
    libpcre3-dev \
    unzip \
    wget 

# Install eserix (sentence splitter)
WORKDIR /opt/app
RUN git clone https://github.com/summa-platform/eserix.git --depth 1
RUN mkdir -p eserix/build && cd eserix/build && cmake .. && make -j

# git \
#     python3-pip \
#     gfortran \
#     zlib1g-dev \

# the following packages are probably not needed any more
# libeigen3-dev \
# libopenblas-base \
# libopenblas-dev \


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

#    && rm -rf /var/lib/apt/lists/*
