# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash

LPAIRS = de-en

# define model versions here
de-en.MODEL = 20180712

# YOU SHOULD NOT HAVE TO CHANGE ANYTHING BELOW THIS LINE
# TO ADD MORE MODELS

.PHONY: builder engine

# build the builder image that compiles everything
builder:
	docker build -t summaplatform/mt-builder --pull builder

# build a blank engine image without models
engine: 
	docker build -t summaplatform/mt-engine engine

define prepare_engine_image_with_model

prepare: models/$1/$2/Dockerfile
models/$1/$2/model/$1/model_info.yaml:
	mkdir -p $${@D}
	MARIAN_MODEL=$2	\
	docker/engine/summa_mt/download_summa_models.py -w $${@D} -m $1

models/$1/$2/Dockerfile: models/$1/$2/model/$1/model_info.yaml
models/$1/$2/Dockerfile: docker/engine_with_model/Dockerfile
	cp $$< $$@
endef

define build_image

build: models/$1/$2/Dockerfile
	docker build -t summaplatform/mt-$1-$2 --build-arg LANG_PAIR=$1 models/$1/$2

endef

LPAIRS = de-en
# Very compact, but does a lot!
$(foreach P,${LPAIRS},\
$(eval $(call prepare_engine_image_with_model,$P,${$P.MODEL}))\
$(eval $(call build_image,$P,${$P.MODEL})))


