ARG BASE_IMAGE=summaplatform/mt-build-environment
FROM ${BASE_IMAGE} as builder
WORKDIR /opt/app
COPY . .
ARG GITHASH
RUN make engine CONTEXT=docker
