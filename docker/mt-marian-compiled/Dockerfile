ARG BASE_IMAGE=summaplatform/mt-build-environment
FROM ${BASE_IMAGE} as builder
WORKDIR /opt/app
COPY . .
ARG GITHASH
RUN make eserix CONTEXT=docker
RUN make debfile CONTEXT=docker
RUN make marian CONTEXT=docker
RUN make engine CONTEXT=docker
