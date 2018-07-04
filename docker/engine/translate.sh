#!/bin/bash
export MARIAN_SERVER_EXECUTABLE="/home/shared/germann/code/marian-dev/build/marian-server"
export MODEL_DIR="/home/shared/germann/code/marian-dev/models/uedin-wmt18-de-en-run5/marian/"
export MODEL="de-en"

export SUMMA_ESERIX_COMMAND="/home/shared/germann/code/eserix/build/bin/eserix"
export SUMMA_ESERIX_RULES="/home/shared/germann/code/eserix/srx/rules.srx"

$(dirname $0)/translate.py $@
