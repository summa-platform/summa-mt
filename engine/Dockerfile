#FROM summaplatform/mt-builder as builder
FROM ubuntu:16.04
LABEL maintainer="Ulrich Germann <ugermann@inf.ed.ac.uk>"

RUN apt-get update && \
    apt-get install -y \
    libpcre3 \
    libtcmalloc-minimal4 \
    python3-regex \
    python3-websocket

    # curl \
    # git \
    # wget 

WORKDIR /opt/summa
ADD . .
RUN dpkg -i 3rd-party.deb
RUN ldd bin/eserix \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 

RUN ldd bin/marian-server \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 



# RUN mkdir -p /opt/eserix/bin /opt/eserix/srx /opt/marian 
# COPY --from=builder /opt/app/eserix/build/bin/eserix /opt/eserix/bin
# COPY --from=builder /opt/app/eserix/srx/rules.srx /opt/eserix/srx
# # install libraries needed by eserix:
# RUN ldd /opt/eserix/bin/eserix \
#     | awk '/not found/ { print $1 }' \
#     | sed 's/\.so\.//;s/_/-/g'\
#     | xargs apt-get install -y 

# # install shared libraries needed by marian
# RUN ldd /opt/marian/marian-server \
#     | awk '/not found/ { print $1 }' \
#     | sed 's/\.so\.//;s/_/-/g'\
#     | xargs apt-get install -y 

# WORKDIR /opt/app
# ADD . .


# # clean up
# # RUN rm -rf /var/lib/apt/lists/* && apt-get purge -y python3-pip

# # # Build arguments
# # ARG MARIAN_MODEL
# # ARG LANG_PAIR

# # # Download model at build time
# # COPY summa_mt/download_summa_models.py ./
# # RUN python3 download_summa_models.py -w model/${LANG_PAIR} -m ${LANG_PAIR}


# # # Set model to load at runtime
# # ENV MODEL $LANG_PAIR

# # # support for unicode in docker
# # # https://github.com/docker-library/python/issues/13#issue-43852823
# # ENV LANG C.UTF-8
# # # for unbuffered stdout
# # ENV PYTHONUNBUFFERED y

# # ENTRYPOINT ["/opt/app/rabbitmq.py"]
