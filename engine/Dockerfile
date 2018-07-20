FROM summaplatform/mt-builder as builder
FROM ubuntu:16.04
MAINTAINER Ulrich Germann <ugermann@inf.ed.ac.uk>

# TO DO: install pip packages on the builder and create a .deb file there
# that then can be used to install only the files needed in production
# on the engine, instead of the whole pip infrastructure

RUN apt-get update && apt-get install -y \
    curl \
    git \
    libopenblas-base \
    libpcre3-dev \
    libtcmalloc-minimal4 \
    python3-websocket \
    python3-pip \
    wget 

# Notes: Once Issue #1 is resolved (Compile with MKL), we
# won't need OpenBLAS any more, may have to install MKL instead
# see http://dirk.eddelbuettel.com/blog/2018/04/15/.

RUN pip3 install --upgrade pip setuptools && hash -r && pip3 install \
    PyYAML==3.12 requests==2.18.4 aio-pika==0.21.0

# Install BPE
# RUN git clone https://github.com/rsennrich/subword-nmt.git --depth 1
# now included in this repo

# eserix sentence splitter, marian, etc.
RUN mkdir -p /opt/eserix/bin /opt/eserix/srx /opt/marian 
COPY --from=builder /opt/app/eserix/build/bin/eserix /opt/eserix/bin
COPY --from=builder /opt/app/eserix/srx/rules.srx /opt/eserix/srx
# install libraries needed by eserix:
RUN ldd eserix/bin/eserix \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 

# marian server
# strictly speaking, we need only the marian server
COPY --from=builder /opt/app/marian.build/marian-server /opt/marian/
COPY --from=builder /opt/app/marian.build/marian-decoder /opt/marian/
COPY --from=builder /opt/app/marian.build/marian-scorer /opt/marian/

# install only libraries needed by marian
RUN ldd /opt/marian/marian-server \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 

# Install summa scripts; Dockerfiles currently don't seem to support wildcards,
# so it's easer to add all to the working directory and then move them
WORKDIR /opt/app
ADD . .


# clean up
# RUN rm -rf /var/lib/apt/lists/* && apt-get purge -y python3-pip

# # Build arguments
# ARG MARIAN_MODEL
# ARG LANG_PAIR

# # Download model at build time
# COPY summa_mt/download_summa_models.py ./
# RUN python3 download_summa_models.py -w model/${LANG_PAIR} -m ${LANG_PAIR}


# # Set model to load at runtime
# ENV MODEL $LANG_PAIR

# # support for unicode in docker
# # https://github.com/docker-library/python/issues/13#issue-43852823
# ENV LANG C.UTF-8
# # for unbuffered stdout
# ENV PYTHONUNBUFFERED y

# ENTRYPOINT ["/opt/app/rabbitmq.py"]
