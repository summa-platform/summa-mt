FROM summaplatform/mt-builder as builder
FROM ubuntu:16.04
MAINTAINER Ulrich Germann <ugermann@inf.ed.ac.uk>

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

WORKDIR /opt/app

# Install BPE
# RUN git clone https://github.com/rsennrich/subword-nmt.git --depth 1
# now included in this repo

# eserix sentence splitter
RUN mkdir -p eserix/bin eserix/srx
COPY --from=builder /opt/app/eserix/build/bin/eserix eserix/bin
COPY --from=builder /opt/app/eserix/srx/rules.srx eserix/srx

# marian server
COPY --from=builder /opt/app/marian.build/marian-server .
COPY --from=builder /opt/app/marian.build/marian-decoder .
COPY --from=builder /opt/app/marian.build/marian-scorer .

# install only those boost libraries that are needed
RUN ldd marian-server \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 

# install only those boost libraries that are needed
RUN ldd eserix/bin/eserix \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 

# Install server scripts and binaries
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
