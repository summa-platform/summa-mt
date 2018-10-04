# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash
mydir:=$(dir $(lastword ${MAKEFILE_LIST}))
INSTALL_PREFIX=${PWD}/engine
all:
	@echo "Please specify the target:"
	@echo "- make local to build locally on the host"
	@echo "- make image to build the docker image"

# for local install (coming soon):
# include ${mydir}/docker/mt-marian-compiled/Makefile

.PHONY: local
local:

GITHASH=$(shell git rev-parse HEAD)
export GITHASH

image/mt-build-environment:
	docker-compose -f docker/compose/build.yml build ${@F}

image/mt-marian-compiled: # image/mt-build-environment
	docker-compose -f docker/compose/build.yml build ${@F}

image/mt-basic-engine: # image/mt-marian-compiled
	docker-compose -f docker/compose/build.yml build --no-cache ${@F}

image/mt-engine: # image/mt-basic-engine
	docker-compose -f docker/compose/build.yml build ${@F}

export MT_MODEL_VERSION
image/mt-engine-fa-en: MT_MODEL_VERSION=20180712
image/mt-engine-fa-en: image/mt-engine
	docker-compose -f docker/compose/build.yml build ${@F}
	docker tag summaplatform/mt-engine-fa-en:${MT_MODEL_VERSION} \
	summaplatform/mt-engine-fa-en:latest


# NOTE: to build and tag model containers, cd into the respective model directory,
# and run a command like this:
# (echo FROM scratch; echo COPY . /model) \
# | docker build -t summaplatform/mt-model-fa-en:20180712 . -f-
