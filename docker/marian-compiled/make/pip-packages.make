# -*- mode: makefile-gmake; indent-tabs-mode: true; tab-width: 4 -*-

pip_requirements  = aio-pika
pip_requirements += aiohttp
pip_requirements += nltk
pip_requirements += pika
pip_requirements += PyYAML
pip_requirements += requests
pip_requirements += retry
pip_requirements += websocket
pip_requirements += websocket-client

debfile: engine/3rd-party.deb
# Installing pip3 on a production image adds about 250MB to the image size.
# To avoid this overhead, we create a .deb file that installs all packaged that
# normally would have to be installed through pip3.
engine/3rd-party.deb: package_name = 3rd-party
engine/3rd-party.deb: tmpdir = engine/${package_name}
engine/3rd-party.deb: control = ${tmpdir}/DEBIAN/control
engine/3rd-party.deb: python_packages = ${pip_requirements}
engine/3rd-party.deb:
	mkdir -p $(dir ${control})
	pip3 install ${python_packages} --root ${tmpdir}
	for f in $$(find ${tmpdir} -name '*.so'); do strip -S $$f; done 
	echo "Package: summa-mt-pip" > ${control}
	echo "Version: 0.0.0" >> ${control}
	echo 'Maintainer: SUMMA Consortium' >> ${control}
	echo 'Description: MT engine for the SUMMA Platform' >> ${control}
	echo 'Architecture: amd64' >> ${control}
	dpkg-deb --build ${tmpdir}
	rm -rf ${tmpdir}
