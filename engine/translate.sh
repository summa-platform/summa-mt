#!/bin/bash
#export MARIAN_SERVER_EXECUTABLE="/home/germann/code/marian-dev/build/marian-server"
#export MODEL_DIR="/home/germann/code/marian-dev/models/uedin-wmt18-de-en-run5/marian/"

export MARIAN_SERVER_EXECUTABLE="/home/shared/germann/code/marian-dev/build/marian-server"
export MODEL_DIR="/home/shared/germann/code/summa-mt/models/fa-en/20180712/model/"
export MODEL=fa-en

export ESERIX_CMD="/home/shared/germann/code/eserix/build/bin/eserix"
export ESERIX_RULES="/home/shared/germann/code/eserix/srx/rules.srx"

export BPE_THRESHOLD=0
$(dirname $0)/translate.py -m ${MODEL} - --debug
# $(dirname $0)/summa_mt/preprocess.py $@
