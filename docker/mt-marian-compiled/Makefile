# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash
mydir:=$(dir $(lastword ${MAKEFILE_LIST}))
INSTALL_PREFIX=${PWD}/engine/summa_mt
include ${mydir}/make/marian.make
include ${mydir}/make/eserix.make
include ${mydir}/make/pip-packages.make

engine: eserix marian
engine: $(addprefix ${INSTALL_PREFIX}/bin/marian-,server decoder scorer)
engine: ${INSTALL_PREFIX}/bin/eserix
engine: ${INSTALL_PREFIX}/srx/rules.srx
ifeq ("${CONTEXT}","docker")
engine: debfile
endif

