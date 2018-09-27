# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-
SHELL = bash

MODULE_NAME = summa-mt
MODULE_VERSION = 1.0.0

all: marian debfile eserix

marian: CMAKE_FLAGS  =-DUSE_STATIC_LIBS=on 
marian: CMAKE_FLAGS +=-DCMAKE_BUILD_TYPE=Nonative 
marian: CMAKE_FLAGS +=-DCOMPILE_CUDA=off
marian: CMAKE_FLAGS +=-DCMAKE_INSTALL_PREFIX=${PWD}/engine
marian: engine/bin/marian-server

engine/bin/marian-server: marian/build/marian-server
	mkdir -p ${@D}
	cp $(addprefix marian/build/marian-, server decoder scorer) ${@D}

marian/build/marian-server: marian/CMakeLists.txt
	mkdir -p ${@D} && rm -rf ${@D}/* 
	cd marian/build && cmake ${CMAKE_FLAGS} .. && make -j

marian/CMakeLists.txt:
	git submodule update --init marian 

# Installing pip3 on a production image adds about 250MB to the image size.
# To avoid this overhead, we create a .deb file that installs all packaged that
# normally would have to be installed through pip3.
engine/3rd-party.deb: package_name = 3rd-party
engine/3rd-party.deb: tmpdir = engine/${package_name}
engine/3rd-party.deb: control = ${tmpdir}/DEBIAN/control
engine/3rd-party.deb: python_packages  = retry pika requests PyYAML 
engine/3rd-party.deb: python_packages += aiohttp aio-pika
engine/3rd-party.deb:
	mkdir -p $(dir ${control})
	pip3 install ${python_packages} --root ${tmpdir}
	for f in $$(find ${tmpdir} -name '*.so'); do strip -S $$f; done 
	echo "Package: summa-mt-pip" > ${control}
	echo "Version: ${MODULE_VERSION}" >> ${control}
	echo 'Maintainer: SUMMA Consortium' >> ${control}
	echo 'Description: MT engine for the SUMMA Platform' >> ${control}
	echo 'Architecture: amd64' >> ${control}
	dpkg-deb --build ${tmpdir}
	rm -rf ${tmpdir}

debfile: engine/3rd-party.deb
eserix: engine/bin/eserix engine/srx/rules.srx

engine/srx/rules.srx: eserix/srx/rules.srx
	mkdir -p ${@D}
	cp $< $@

engine/bin/eserix:| eserix/srx/rules.srx
	mkdir -p eserix/build && cd eserix/build && cmake .. && make -j
	cp eserix/build/bin/eserix $@

eserix/srx/rules.srx:
	git submodule update --init eserix

reset-engine-image:
	-rm -rf engine/bin engine/3rd-party*
