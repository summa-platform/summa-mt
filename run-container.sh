#!/bin/bash

if [[ "$1" == "bash" ]]; then
    docker run --rm -it -v ${PWD}/test:/test -v ${PWD}/engine/:/opt/app/ summaplatform/mt-fa-en-20180712 $@
else
    docker run --rm -i -v ${PWD}/test:/test -v ${PWD}/engine/:/opt/app/ summaplatform/mt-fa-en-20180712 $@
fi
#--debug
