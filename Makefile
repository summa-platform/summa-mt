# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash
mydir:=$(dir $(lastword ${MAKEFILE_LIST}))
INSTALL_PREFIX=${PWD}/engine

$(foreach s,fa pt,$(foreach t,en,\
$(eval all: image/mt-engine-$s-$t)))

info:
	@echo
	@echo "HOW TO BUILD IMAGES (execute in this order)"
	@echo "- make image/mt-build-environment"
	@echo "  create image for compiling Marian from scratch"
	@echo "- make image/mt-marian-compiled"
	@echo "  compile Marian from scratch"
	@echo "- make image/mt-basic-engine"
	@echo "  copy Marian binaries to fresh image, without the infrastructure"
	@echo "  needed to compile Marian. Also includes Eserix."
	@echo "- make image/mt-engine"
	@echo "  add SUMMA scripts and python wrappers around marian-server"
	@echo "- make image/mt-engine-<language>"
	@echo "  combine mt-engine with model image into an all-in-one container"

# for local install (coming soon):
include ${mydir}/docker/mt-marian-compiled/Makefile

.PHONY: local
local:

GITHASH=$(shell git rev-parse HEAD)
export GITHASH

SITE ?= uedin
include ${SITE}.env

REGISTRY=${LOCAL_REGISTRY}
BUILD_ENVIRONMENT = ${REGISTRY}/mt-build-environment
MARIAN_BUILDER    = ${REGISTRY}/mt-marian-compiled
MARIAN_IMAGE      = ${REGISTRY}/mt-basic-engine
MT_ENGINE_IMAGE   = ${REGISTRY}/mt-engine

# We explicitly list relevant environment variables on the command
# line below (instead of exporting them via the gmake export command),
# so that the settings are visible in the make log and when running
# make -n

define copy_engine_script

engine: engine/$1
engine/$1: ${PWD}/docker/mt-engine/$1
	mkdir -p $${@D}
	cp ${PWD}/docker/mt-engine/$1 $${@D}

endef

ENGINE_SCRIPTS = $(subst ./,,$(shell cd docker/mt-engine && find -type f))

$(foreach f,${ENGINE_SCRIPTS},\
$(eval $(call copy_engine_script,$f)))

ifeq (${from},scratch)
image/mt-marian-compiled: image/mt-build-environment
image/mt-basic-engine: image/mt-marian-compiled
image/mt-engine: image/mt-basic-engine
endif

ifeq (${from},marian-compiled)
image/mt-basic-engine: image/mt-marian-compiled
image/mt-engine: image/mt-basic-engine
endif

ifeq (${from},basic-engine)
image/mt-engine: image/mt-basic-engine
endif

image/mt-build-environment:
	BASE_IMAGE=ubuntu:16.04 \
	TARGET_IMAGE=${BUILD_ENVIRONMENT} \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} ${@F}

image/mt-marian-compiled: 
	BASE_IMAGE=${BUILD_ENVIRONMENT} \
	TARGET_IMAGE=${MARIAN_BUILDER} \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} --no-cache ${@F}

# make sure LICENSE.txt is up to date in the docker container
docker/mt-basic-engine/LICENSE.txt: LICENSE.txt
	cp LICENSE.txt ${@D}

image/mt-basic-engine: docker/mt-basic-engine/LICENSE.txt

image/mt-basic-engine: 
	BASE_IMAGE=${MARIAN_BUILDER} \
	TARGET_IMAGE=${MARIAN_IMAGE} \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} --no-cache ${@F}

image/mt-engine: 
	BASE_IMAGE=${MARIAN_IMAGE} \
	TARGET_IMAGE=${MT_ENGINE_IMAGE} \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} --no-cache ${@F}

define build_engine_with_model

image/mt-model-$1-$2:
	[ ${REGISTRY} != "summaplatform" ] \
	&& docker pull summaplatform/$${@F}:$3 \
	&& docker tag summaplatform/$${@F}:$3 ${REGISTRY}/$${@F}:$3

image/mt-engine-$1-$2: image/mt-engine
	BASE_IMAGE=${MT_ENGINE_IMAGE} \
	MODEL_IMAGE=${REGISTRY}/mt-model-$1-$2:$3 \
	TARGET_IMAGE=${REGISTRY}/mt-engine-$1-$2:$3 \
	REGISTRY=${REGISTRY} SRCLANG=$1 TRGLANG=$2 \
	MAINTAINER="$(shell git config user.name)<$(shell git config user.email)>" \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} mt-engine-with-model
	docker tag ${REGISTRY}/mt-engine-$1-$2:$3 ${REGISTRY}/mt-engine-$1-$2:latest

endef

$(eval $(call build_engine_with_model,fa,en,20181017))
$(eval $(call build_engine_with_model,pt,en,20180622))


# NOTE: to build and tag model containers, cd into the respective model directory,
# and run a command like this:
# (echo FROM scratch; echo COPY . /model) \
# | docker build -t summaplatform/mt-model-fa-en:20180712 . -f-
