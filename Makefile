# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL   = bash
mydir  := $(dir $(lastword ${MAKEFILE_LIST}))

LOCAL_REGISTRY=summaplatform
GITHASH = $(shell git rev-parse HEAD)
REGISTRY=${LOCAL_REGISTRY}
BUILD_ENVIRONMENT = ${REGISTRY}/mt-build-environment
MARIAN_BUILDER    = ${REGISTRY}/mt-marian-compiled
MARIAN_IMAGE      = ${REGISTRY}/mt-basic-engine
MT_ENGINE_IMAGE   = ${REGISTRY}/mt-engine
MT_ENGINE_IMAGE_TAG = v2.0.0

export GITHASH

#include ${mydir}/make/local_install.make

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

# We explicitly list relevant environment variables on the command
# line below (instead of exporting them via the gmake export command),
# so that the settings are visible in the make log and when running
# make -n

# if run with from=scratch, re-build all images from scratch
ifeq (${from},scratch)
image/mt-marian-compiled: image/mt-build-environment
image/mt-basic-engine: image/mt-marian-compiled
image/mt-engine: image/mt-basic-engine
endif

# if run with from=marian-compiled, re-build all images from
# the compiled marian image
ifeq (${from},marian-compiled)
image/mt-basic-engine: image/mt-marian-compiled
image/mt-engine: image/mt-basic-engine
endif

# if run with from=marian-compiled, re-build all images from
# the basic mt imgage (without scripts). This is what you
# want to run after updating scripts.
ifeq (${from},basic-engine)
image/mt-engine: image/mt-basic-engine
endif

# make sure LICENSE.txt is up to date in the docker container
docker/mt-basic-engine/LICENSE.txt: LICENSE.txt
	cp LICENSE.txt ${@D}

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

image/mt-basic-engine: docker/mt-basic-engine/LICENSE.txt
image/mt-basic-engine: 
	BASE_IMAGE=${MARIAN_BUILDER} \
	TARGET_IMAGE=${MARIAN_IMAGE} \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} --no-cache ${@F}

image/mt-engine: 
	BASE_IMAGE=${MARIAN_IMAGE} \
	TARGET_IMAGE=${MT_ENGINE_IMAGE}:${MT_ENGINE_IMAGE_TAG} \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} --no-cache ${@F}
	docker tag ${MT_ENGINE_IMAGE}:${MT_ENGINE_IMAGE_TAG} ${MT_ENGINE_IMAGE}:latest 

define build_engine_with_model

model-images: image/mt-model-$1-$2
image/mt-model-$1-$2:
	docker build -t ${REGISTRY}/$${@F}:$4 models/mt/$1-$2/$3
	docker tag ${REGISTRY}/$${@F}:$4 ${REGISTRY}/$${@F}:latest

engine-images: image/mt-engine-$1-$2
image/mt-engine-$1-$2: image/mt-engine
	BASE_IMAGE=${MT_ENGINE_IMAGE} \
	MODEL_IMAGE=${REGISTRY}/mt-model-$1-$2:$4 \
	TARGET_IMAGE=${REGISTRY}/mt-engine-$1-$2:$4 \
	REGISTRY=${REGISTRY} SRCLANG=$1 TRGLANG=$2 \
	MAINTAINER="$(shell git config user.name)<$(shell git config user.email)>" \
	docker-compose -f docker/compose/build.yml build \
	${EXTRA_BUILD_OPTIONS} mt-engine-with-model
	docker tag ${REGISTRY}/mt-engine-$1-$2:$4 ${REGISTRY}/mt-engine-$1-$2:latest

endef

MT_MODEL_CATALOG=docker/mt-engine/catalog.yml
download_mt_model = docker/mt-engine/download_model.py -c ${MT_MODEL_CATALOG}


.PHONY += models

models:

# $1: language pair
# $2: model version
define download_model

models: models/mt/$1/$2/model_info.yml
models: models/mt/$1/$2/Dockerfile

models/mt/$1/$2/Dockerfile:
	mkdir -p $${@D}
	echo FROM scratch >> $$@_
	echo COPY . /model >> $$@_
	mv $$@_ $$@

models/mt/$1/$2/model_info.yml:
	${download_mt_model} $1 $2

endef

$(eval $(call download_model,de-en,20181023))
$(eval $(call download_model,es-en,v2.0))
$(eval $(call download_model,fa-en,20181017))
$(eval $(call download_model,lv-en,20181217))
$(eval $(call download_model,pt-en,20181207))
$(eval $(call download_model,ru-en,20181207))
$(eval $(call download_model,uk-en,20181207))

$(eval $(call build_engine_with_model,de,en,20181023,v2.0.0))
$(eval $(call build_engine_with_model,es,en,v2.0,v2.0.1))
$(eval $(call build_engine_with_model,fa,en,20181017,v2.0.0))
$(eval $(call build_engine_with_model,lv,en,20181217,v2.0.0))
$(eval $(call build_engine_with_model,pt,en,20181207,v2.0.0))
$(eval $(call build_engine_with_model,ru,en,20181207,v2.0.0))
$(eval $(call build_engine_with_model,uk,en,20181207,v2.0.0))


# NOTE: to build and tag model containers, cd into the respective model directory,
# and run a command like this:
# (echo FROM scratch; echo COPY . /model) \
# | docker build -t summaplatform/mt-model-fa-en:20180712 . -f-
