# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-

# build eserix

# NOTE: ESERIX_COMMIT is used only with newly cloned repositories.
# For existing repositories, we use whatever the current state of the
# respective repository is at the time.
ESERIX_COMMIT=master
ESERIX_REPO_ROOT=${PWD}/eserix
ESERIX_BUILD_DIR=${PWD}/build/eserix
ESERIX_GITHUB_URL=http://github.com/summa-platform/eserix.git

eserix: pdir=$(dir ${ESERIX_REPO_ROOT})
eserix: repo=$(notdir ${ESERIX_REPO_ROOT})
eserix: ${ESERIX_BUILD_DIR}/bin/eserix

${ESERIX_REPO_ROOT}/srx/rules.srx:
	mkdir -p ${pdir}
	[ -d ${ESERIX_REPO_ROOT} ] || git clone ${ESERIX_GITHUB_URL} ${ESERIX_REPO_ROOT}

${ESERIX_BUILD_DIR}/bin/eserix: ${ESERIX_REPO_ROOT}/srx/rules.srx
	mkdir -p ${ESERIX_BUILD_DIR}
	rm -rf ${ESERIX_BUILD_DIR}/*
	cd ${ESERIX_BUILD_DIR} && cmake ${ESERIX_REPO_ROOT} && make -j

${INSTALL_PREFIX}/bin/eserix: ${ESERIX_BUILD_DIR}/bin/eserix
	mkdir -p ${@D}
	cp $< $@

${INSTALL_PREFIX}/srx/rules.srx: ${ESERIX_REPO_ROOT}/srx/rules.srx
	mkdir -p ${@D}
	cp $< $@
