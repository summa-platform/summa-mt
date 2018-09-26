# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash

LPAIRS = de-en fa-en

# define model versions here
de-en.VERSION = 20180712
de-en.BPE_THRESHOLD = 50
fa-en.VERSION = 20180712
fa-en.BPE_THRESHOLD = 0

# YOU SHOULD NOT HAVE TO CHANGE ANYTHING BELOW THIS LINE
# TO ADD MORE MODELS

.PHONY: builder engine

# build the builder image that compiles everything
builder:
	docker build -t summaplatform/mt-builder --pull builder

# build a blank engine image without models
engine: 
	docker build -t summaplatform/mt-engine engine --no-cache

.PHONY: download-models

define download_model

download-models: models/mt/$1/$2/model_info.yaml
models/mt/$1/$2/model_info.yaml: URL=http://data.statmt.org/summa/mt/models/$1/$2
models/mt/$1/$2/model_info.yaml:
	mkdir -p $${@D}
	./scripts/download_model.py $${URL} $${@D}

endef

# define prepare_engine_image_with_model

# prepare: models/$1/$2/Dockerfile
# models/$1/$2/model/$1/model_info.yaml:
# 	mkdir -p $${@D}
# 	MARIAN_MODEL=$2	\
# 	docker/engine/summa_mt/download_summa_models.py -w $${@D} -m $1

# models/$1/$2/Dockerfile: models/$1/$2/model/$1/model_info.yaml
# models/$1/$2/Dockerfile: engine_with_model/Dockerfile
# 	cp $$< $$@
# endef

# define build_image

# build: build-$1
# build-$1: models/$1/$2/Dockerfile
# 	docker build -t summaplatform/mt-$1-$2 --build-arg LANG_PAIR=$1 --build-arg BPE_THRESHOLD=$${$1.BPE_THRESHOLD} models/$1/$2 

# endef

marian: marian-dev/build/marian-decoder
marian-dev/build/marian-decoder: CMAKE_FLAGS  = -DUSE_STATIC_LIBS=on 
marian-dev/build/marian-decoder: CMAKE_FLAGS  = -DCMAKE_BUILD_TYPE=Nonative 
marian-dev/build/marian-decoder: CMAKE_FLAGS  = -DCOMPILE_CUDA=off
marian-dev/build/marian-decoder:
	git submodule update --init marian-dev
	mkdir ${@D} && cd ${@D} && cmake ${CMAKE_FLAGS} .. && make -j

eserix: eserix/build/eserix
eserix/build/eserix:
	git submodule update --init eserix
	mkdir ${@D} && cd ${@D} && cmake .. && make -j



# Very compact, but does a lot!
# $(foreach P,${LPAIRS},\
# $(eval $(call prepare_engine_image_with_model,$P,${$P.MODEL}))\
# $(eval $(call build_image,$P,${$P.MODEL})))

$(foreach P,${LPAIRS},\
$(eval $(call download_model,$P,${$P.VERSION})))

export settings
local.env: Makefile
	echo -e $$settings | sed 's/^ *//' > $@

define settings

ESERIX_CMD=${PWD}/eserix/build/bin/eserix\n
ESERIX_RULES=${PWD}/eserix/srx/rules.srx\n
NORMPUNCT_CMD=${PWD}/docker/engine/summa_mt/tokenizer/normalize-punctuation.perl\n
export ESERIX_CMD\n
export ESERIX_RULES\n
export NORMPUNCT_CMD
endef
