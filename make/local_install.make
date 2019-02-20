# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
# Make rules for local install of marian etc. (outside docker).
# In a separate file just to keep things tidy.

# for local install (coming soon):

INSTALL_PREFIX=${PWD}/engine
include ${mydir}/docker/mt-marian-compiled/Makefile
.PHONY: local
local:

# copy_engine_script is for local installs (outside docker)
define copy_engine_script

engine: engine/$1
engine/$1: ${PWD}/docker/mt-engine/$1
	mkdir -p $${@D}
	cp ${PWD}/docker/mt-engine/$1 $${@D}

endef

ENGINE_SCRIPTS = $(subst ./,,$(shell cd docker/mt-engine && find -type f))

$(foreach f,${ENGINE_SCRIPTS},\
$(eval $(call copy_engine_script,$f)))
