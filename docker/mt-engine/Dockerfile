# Set BUILDER_IMAGE to summaplatform/build-environment below if you
# want to build within docker; otherwise, set it to ubuntu:16.04.
ARG MARIAN_IMAGE
FROM ${MARIAN_IMAGE}
ARG GITHASH
LABEL maintainer="Ulrich Germann <ugermann@inf.ed.ac.uk>"
LABEL GITHASH=${GITHASH}

ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED y
ENV MARIAN_SERVER_EXE=/opt/app/engine/summa_mt/bin/marian-server
ENV ESERIX_CMD=/opt/app/engine/summa_mt/bin/eserix
ENV ESERIX_RULES=/opt/app/engine/summa_mt/srx/rules.srx

WORKDIR /opt/app/engine
ADD . .
