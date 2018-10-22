ARG BUILD_ENVIRONMENT=summaplatform/mt-build-environment
FROM ${BUILD_ENVIRONMENT} as builder
WORKDIR /opt/app
COPY . .
ARG GITHASH
RUN make engine
