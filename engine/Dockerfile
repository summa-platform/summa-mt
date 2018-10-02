# Set BUILDER_IMAGE to summaplatform/build-environment below if you
# want to build within docker; otherwise, set it to ubuntu:16.04.
ARG BUILDER_IMAGE=summaplatform/mt-build-environment
FROM ${BUILDER_IMAGE} as builder
WORKDIR /opt/app
COPY Makefile .
COPY make .

# run make only if we are building on Docker
RUN mkdir -p engine
RUN [[ ${BUILDER_IMAGE} == "summaplatform/mt-build-environment" ]] \
    && make engine
    
FROM ubuntu:16.04
LABEL maintainer="Ulrich Germann <ugermann@inf.ed.ac.uk>"

ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED y
ENV MARIAN_SERVER_EXE

RUN apt-get update 
RUN apt-get install -y libtcmalloc-minimal4 
RUN apt-get install -y python3-regex 
RUN apt-get install -y python3-websocket
RUN apt-get install -y libpcrecpp0v5

WORKDIR /opt/app
COPY --from=builder /engine .
ADD . .
RUN dpkg -i 3rd-party.deb && rm 3rd-party.deb
RUN ldd bin/eserix \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 

RUN ldd bin/marian-server \
    | awk '/not found/ { print $1 }' \
    | sed 's/\.so\.//;s/_/-/g'\
    | xargs apt-get install -y 


#     # curl \
#     # git \
#     # wget 

# WORKDIR /opt/summa
# ADD . .
# # If you build components in a docker container, use with --from=builder.




# RUN mkdir -p /opt/eserix/bin /opt/eserix/srx /opt/marian 
# COPY --from=builder /opt/app/eserix/build/bin/eserix /opt/eserix/bin
# COPY --from=builder /opt/app/eserix/srx/rules.srx /opt/eserix/srx
# # install libraries needed by eserix:

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
