# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash
mydir:=$(dir $(lastword ${MAKEFILE_LIST}))
include ${mydir}/make/marian.make
include ${mydir}/make/eserix.make
include ${mydir}/make/pip-packages.make

INSTALL_PREFIX=${PWD}/engine

engine: $(addprefix ${INSTALL_PREFIX}/bin/marian-,server decoder scorer)
engine: ${INSTALL_PREFIX}/bin/eserix
engine: ${INSTALL_PREFIX}/srx/rules.srx
engine: debfile


pip-requirements:
	for r in ${pip_requirements}; do pip3 install $$r; done

