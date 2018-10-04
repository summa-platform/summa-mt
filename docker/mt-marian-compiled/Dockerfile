FROM summaplatform/mt-build-environment as builder
WORKDIR /opt/app
COPY . .
ARG GITHASH
RUN make engine
