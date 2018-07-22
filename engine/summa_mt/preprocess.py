#!/usr/bin/env python3
# coding: utf-8
import sys, os, logging, regex as re, asyncio
from asyncio.subprocess import create_subprocess_shell as subprocess, PIPE

logger = logging.getLogger(__name__)
whitespace = re.compile(r'\s+', re.U)

# the date hack below is truely horrible!
# Left in for backwards compatibility [UG]
dates = re.compile(r'(\d+)\.(\d+)\.(\d+)', re.U)

MAX_SENT_LEN = 40

MODEL_DIR = None
srclang = None
trglang = None

basedir    = os.path.realpath(os.path.dirname(__file__))

ESERIX_ROOT  = os.environ.get('ESERIX_ROOT','/opt/eserix')
ESERIX_RULES = os.environ.get('ESERIX_RULES','%s/srx/rules.srx'%ESERIX_ROOT)
ESERIX_CMD   = os.environ.get('ESERIX_CMD','%s/bin/eserix'%ESERIX_ROOT)

BPE2_LANGS = ["de", "lv", "ru", "es", "fa", "pt"]
bpe_vthresh = int(os.environ.get('BPE_THRESHOLD',50))

# preprocessing
ssplit_cmd = "%s -r %s -l {lang} -t "%(ESERIX_CMD, ESERIX_RULES) 
norm_cmd   = "%s/tokenizer/replace-unicode-punctuation.perl"%basedir
tok_cmd    = "%s/tokenizer/tokenizer.perl -q -threads 4 -l {lang}"%basedir
true_cmd   = "%s/recaser/truecase.perl --model {mdir}/truecase-model.{lang}"\
             %(basedir)
bpe_cmd    = "%s/subword-nmt/subword_nmt/apply_bpe.py" % os.path.dirname(basedir)
bpe_cmd   += " --codes {mdir}/{srclang}{trglang}.bpe"
if bpe_vthresh:
    bpe_cmd += " --vocabulary {mdir}/vocab.{srclang}"
    bpe_cmd += " --vocabulary-threshold %d"%bpe_vthresh

# post-processing
detok_cmd  = "%s/tokenizer/detokenizer.perl -penn -q -l {trglang}"%basedir
detrue_cmd = "%s/recaser/detruecase.perl"%basedir

# def ssplit_fa(text):
#     pattern = re.compile(r'([!\.\?⸮؟]+)[ \n]+')
#     text = pattern.sub(r'\1\n\n', text)

def init(model_dir,srclang,trglang):
    global ssplit_cmd,tok_cmd,true_cmd,bpe_cmd,detok_cmd
    MODEL_DIR = model_dir
    srclang = srclang
    trglang = trglang

    mdir = "%s/%s-%s"%(model_dir,srclang,trglang)
    ssplit_cmd = ssplit_cmd.format(lang=srclang)
    tok_cmd = tok_cmd.format(lang=srclang)
    true_cmd = true_cmd.format(lang=srclang, mdir=mdir)
    bpe_cmd = bpe_cmd.format(srclang=srclang, trglang=trglang, mdir=mdir)
    detok_cmd = detok_cmd.format(trglang=trglang)
    
def split_long_sentences(sents, maxlen):
    return [s[i:i+maxlen] for s in sents
            for i in range(0,len(sents),maxlen)]

async def apply_step(cmd,text,loop):
    logger.debug('Applying command: %s'%cmd)
    try:
        proc = await subprocess(cmd,stdin=PIPE,stdout=PIPE,loop=loop)
    except:
        logger.error("Could not create process: %s" % cmd)
        raise
    try:
        out,err = await proc.communicate(text)
        # we need to check return codes here
    except:
        logger.error("Processing failed: %s"%cmd)
        raise
    logger.debug('Success: %s'%cmd)
    logger.debug(out.decode('utf8'))
    return out

async def preprocess(sents, loop=None):
    global logger,whitespace
    logger.debug("Starting preprocessing.")

    sents = [whitespace.sub(' ', sentence).strip() for sentence in sents]
    # I *HATE* the date hack below. Why is this happening here? [UG]
    # I'd prefer not to have it at all, but maybe eserix needs it.
    sents = [dates.sub(r'\1 . \2 . \3', sentence).strip() for sentence in sents]
    
    text = "\n".join(sents).encode('utf8')

    for step in [norm_cmd,   # normalize_punctuation
                 ssplit_cmd, # split sentences
                 tok_cmd,    # tokenize 
                 true_cmd,   # truecase
                 bpe_cmd]:   # apply bpe
        text = await apply_step(step,text,loop)

    logger.debug("PREPROCESSED INPUT:")
    for t in text.decode('utf8').split('\n'): logger.debug(t)
    logger.debug("Preprocessing finished.")

    return text.decode('utf8').split('\n')

if __name__ == "__main__":
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument("--debug",action='store_true')
    ap.add_argument("modeldir")
    ap.add_argument("src")
    ap.add_argument("trg")
    opts = ap.parse_args(sys.argv[1:])
    print(opts)

    logfmt = '[%(lineno)d in %(pathname)s] %(asctime)s: %(levelname)s: %(message)s'
    loglevel = logging.DEBUG if opts.debug else logging.INFO
    logging.basicConfig(level=loglevel, format=logfmt)

    init(opts.modeldir, opts.src, opts.trg)
    loop = asyncio.get_event_loop()
    text = sys.stdin.read().split('\n')
    sents = loop.run_until_complete(preprocess(text,loop))
    print("\n".join(sents))
    loop.close()
