#!/usr/bin/env python3

import sys, os, asyncio, traceback, logging, re, copy
from asyncio.subprocess import create_subprocess_exec, create_subprocess_shell, PIPE
from os.path import join as pjoin
from summa_mt import marian
from summa_mt.marian import MarianServer

logger = logging.getLogger(__name__)
basedir = os.path.realpath(os.path.dirname(__file__))

MAX_SENT_LEN = 40

# environment variables are for testing outside Docker containers

MODEL_DIR = os.environ.get('SUMMA_MT_MODEL_DIR', pjoin(basedir, "model"))

ESERIX_COMMAND = os.environ.get('SUMMA_ESERIX_COMMAND',
                                pjoin(basedir, 'eserix/bin/eserix'))
ESERIX_RULES = os.environ.get('SUMMA_ESERIX_RULES',
                              pjoin(basedir, 'eserix/srx/rules.srx'))

scriptdir = pjoin(basedir, 'summa_mt')

TOK_COMMAND = '%s -q -threads 4' % pjoin(scriptdir, 'tokenizer/tokenizer.perl')
TRUE_COMMAND = '%s --model ' % pjoin(scriptdir, 'recaser/truecase.perl')

APPLY_BPE = pjoin(basedir, "subword-nmt/subword_nmt/apply_bpe.py")

NORMALIZER_COMMAND = pjoin(scriptdir, 'tokenizer/replace-unicode-punctuation.perl')
DETOK_COMMAND = '%s -penn -q -l' % pjoin(scriptdir, 'tokenizer/detokenizer.perl')
DETRUE_COMMAND = pjoin(scriptdir, 'recaser/detruecase.perl')

DE_BPE = "sed -r 's/(@@ )|(@@ ?$)//g'"
BPE2_LANGS = ["de", "lv", "ru", "es", "fa", "pt"]
BPE_VOCAB_THRESHOLD = int(os.environ.get('SUMMA_BPE_VOCAB_THRESHOLD',50))

MODEL = None
MODEL_PATH = None
SOURCE_LANGUAGE = None
TARGET_LANGUAGE = None

MARIAN_SERVER_EXECUTABLE \
    = os.environ.get('MARIAN_SERVER_EXECUTABLE',
                     pjoin(basedir,'marian-server'))

MyMarianServer = None

def model_source_language():
    return MODEL.split('-')[0]

def model_target_language():
    return MODEL.split('-')[1]


def init(model, modeldir=MODEL_DIR,loop=None):
    global MODEL, MODEL_DIR, MODEL_PATH, SOURCE_LANGUAGE, TARGET_LANGUAGE
    global MyMarianServer
    MODEL = model
    MODEL_DIR = modeldir or MODEL_DIR
    MODEL_PATH = pjoin(MODEL_DIR, MODEL)
    SOURCE_LANGUAGE, TARGET_LANGUAGE = MODEL.split('-')
    loop = loop or asyncio.get_event_loop()
    MyMarianServer = MarianServer(MARIAN_SERVER_EXECUTABLE,
                                  pjoin(MODEL_PATH,"decoder.yml"))
    MyMarianServer.start(loop)
    # nmt.init('-c %s' % pjoin(MODEL_PATH, 'config.yaml'))

def shutdown():
    if MyMarianServer:
        MyMarianServer.stop()
        
async def split_sentences(sentences, src, loop=None):
    logger.debug("Splitting sentences.")
    plain = ' '.join(sentences)
    command = "{} -r {} -l {} -t ".format(ESERIX_COMMAND, ESERIX_RULES, src)
    #print ("SPLIT CMD: " + command)
    splitter = await create_subprocess_shell(command, stdin=PIPE, stdout=PIPE, loop=loop)
    #print ("SPLIT TEXT: " + plain)
    out, err = await splitter.communicate(plain.encode('utf8'))
    return out.decode('utf8').split('\n')


def slice_it(line, cols=2):
    start = 0
    for i in range(cols):
        stop = start + len(line[i::cols])
        yield line[start:stop]
        start = stop

def split_long_sentences(sentences):
    out = []
    for sent in sentences:
        #print ("SENT: " + sent)
        if not sent:
            break
        words = sent.split(' ')
        if (len(words) > MAX_SENT_LEN):
            #print ("LEN words" + str(len(words)))
            npieces = len(words) / MAX_SENT_LEN
            npieces = int(npieces) + (not npieces.is_integer()) #round up
            #print ("NUM PIECE" + str(npieces))
            slices = slice_it(words, npieces)  
            for piece in slices:
                #print ("PIECE" + " ".join(piece)) 
                out.append(" ".join(piece))
        else: 
            #print ("Else " + sent)
            out.append(sent)
    return out


async def preprocess(sentences, loop=None):
    logger.debug("Starting preprocessing.")
    # src, trg = MODEL.split('-')
    src, trg = SOURCE_LANGUAGE, TARGET_LANGUAGE

    whitespace = re.compile(r'\s+', re.U)
    dates = re.compile(r'(\d+)\.(\d+)\.(\d+)', re.U)
    # import regex  # pip install regex==2017.07.28
    # whitespace = regex.compile(u"[[:space:]]+", regex.U)
    # [:space:] in https://en.wikibooks.org/wiki/Regular_Expressions/POSIX-Extended_Regular_Expressions#Character_classes
    # \s in https://docs.python.org/3.5/library/re.html#regular-expression-syntax

    sentences = [whitespace.sub(' ', sentence).strip()
                 for sentence in sentences]

    sentences = [dates.sub(r'\1 . \2 . \3', sentence).strip()
                 for sentence in sentences]
    sentences = await split_sentences(sentences, src, loop=loop)
    
    sentences = split_long_sentences(sentences)

    tok_command = '%s -l %s' % (TOK_COMMAND, src)
    true_command = '%s %s' % (TRUE_COMMAND, pjoin(MODEL_PATH, 'truecase-model.%s' % src))

    logger.debug("Normalization")
    normalizer = await create_subprocess_shell(NORMALIZER_COMMAND, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await normalizer.communicate(('\n'.join(sentences) + '\n').encode('utf8'))

    logger.debug("Tokenizarion")
    tok = await create_subprocess_shell(tok_command, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await tok.communicate(out)

    logger.debug("Truecasing")
    true = await create_subprocess_shell(true_command, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await true.communicate(out)


    if src in BPE2_LANGS:
        bpe  = pjoin(MODEL_PATH, "%s%s.bpe" % (src, trg))
        vcb  = pjoin(MODEL_PATH, "vocab.%s" % src)
        cmd  = "%s -c %s --vocabulary %s --vocabulary-threshold %d" \
               % (APPLY_BPE, bpe, vcb, BPE_VOCAB_THRESHOLD)
        bpe = await create_subprocess_shell(cmd, stdin=PIPE, stdout=PIPE, loop=loop)
        out, err = await bpe.communicate(out)

    logger.debug("OUTPUT:")
    logger.debug(out)
    logger.debug("Preprocessing finished.")

    return out.decode('utf8').split('\n')


async def postprocess(sentences, loop=None):
    logger.debug("Starting postprocessing")
    # src, trg = MODEL.split('-')
    src, trg = SOURCE_LANGUAGE, TARGET_LANGUAGE

    if SOURCE_LANGUAGE != 'ar':
        # find ' .nextsent'
        punct_fix = re.compile(r'(\s)([.!?](?:\s*&quot;)?)\s*(\w+)', re.U)

        # replace ' .new-sentence' with '. Nextsent'
        # and ' ." new-sentence' with '. " Nextsent'
        def punct_fix_repl(m):
            w = m.group(3)
            w = w[0].upper() + w[1:]
            punct = m.group(2)
            if punct[-1] == '"':
                w = punct[-1] + ' ' + w
                punct = punct[:-1].strip()
            return '%s%s%s' % (punct, m.group(1), w)

        sentences = (punct_fix.sub(punct_fix_repl, s) for s in sentences)

    out = ('\n'.join(sentences) + '\n').encode('utf8')

    if src in BPE2_LANGS:
        logger.debug("De-BPE.")
        debpe = await create_subprocess_shell(DE_BPE, stdin=PIPE, stdout=PIPE, loop=loop)
        out, err = await debpe.communicate(out)

    detok_command = '%s %s' % (DETOK_COMMAND, trg)

    logger.debug("Detokenization: {}".format(detok_command))
    detok = await create_subprocess_shell(detok_command, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await detok.communicate(out)

    logger.debug("Detruecasing: {}".format(DETRUE_COMMAND))
    detrue = await create_subprocess_shell(DETRUE_COMMAND, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await detrue.communicate(out)

    logger.debug("Postprocessing finished.")
    return out.decode('utf8').split('\n')


async def translate(sentences, loop=None):
    logger.debug("Start translating: {} sentences".format(len(sentences)))
    if sentences and not sentences[-1]:
        sentences.pop()
        pass
    translation = await MyMarianServer._translate(sentences)
    return translation


# --- default_controller ---

def collect_sentences(instance):
    sentences = []
    word_to_clean = [u'&nbsp;', u'<p>', u'</p>']
    for sentence in instance['body']['sentences']:
        sentences.append(' '.join([token['token']['token']
                                   for token in sentence['tokens']
                                   if token not in word_to_clean]))
    return sentences


async def process_sentences(sentences, loop=None):
    preprocessed = [sen for sen in (await preprocess(sentences, loop=loop)) if len(sen) > 0]
    translated = await translate("\n".join(preprocessed), loop=loop)
    post = await postprocess(translated.split('\n'), loop=loop)
    return [sentence for sentence in post if sentence]


def encode_sentences(sentences):
    encoded_sentences = []
    for sentence in sentences:
        encoded_words = []
        for index, word in enumerate(sentence.strip().split(' ')):
            encoded_words.append({'token': {'offset': index,
                                            'token': word},
                                  'features': []})
        encoded_sentences.append({'tokens':  encoded_words})
    return encoded_sentences


async def translate_document(document, loop=None):

    logger.debug(document)

    new_instances = []
    for instance in document['instances']:
        if instance['metadata']['language'] == TARGET_LANGUAGE:
            translated_instance = copy.deepcopy(instance)
            translated_instance['metadata']['language'] = TARGET_LANGUAGE

            sentences = collect_sentences(instance)
            translated = await process_sentences(sentences, loop=loop)

            translated_instance['body']['sentences'] = encode_sentences(translated)
            new_instances.append(translated_instance)

    for new_instance in new_instances:
        document['instances'].append(new_instance)

    return document



if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s:  %(message)s')

    import argparse, json

    parser = argparse.ArgumentParser(description='Machine Translation', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='asyncio debug mode')
    parser.add_argument('--model-dir', '-d', type=str, default=os.environ.get('MODEL_DIR', MODEL_DIR), help='model directory')
    parser.add_argument('--model', '-m', type=str, default=os.environ.get('MODEL'), help='model name')
    parser.add_argument('--lines', '-l', action='store_true', help='Translate each line as separate document')
    parser.add_argument('filename', nargs='+', type=str, help='text or JSON file with translation data')
    args = parser.parse_args()

    if not args.model:
        print('error: specify model', file=sys.stderr)
        sys.exit(1)

    init(args.model, args.model_dir)

    loop = asyncio.get_event_loop()
    loop.set_debug(args.debug)

    for filename in args.filename:
        if filename.endswith('json'):
            with open(filename, 'r') as f:
                task_data = json.load(f)
            output = loop.run_until_complete(translate_document(task_data, loop=loop))
        elif filename == "-":
            text = sys.stdin.read()
            print(text)
            output = loop.run_until_complete(process_sentences([text], loop=loop))
            print("\n".join(output))
        else:
            with open(filename, 'r') as f:
                text = f.read()
            if args.lines:
                lines = text.splitlines()
                for line in lines:
                    output = loop.run_until_complete(process_sentences([line], loop=loop))
                    print("\n".join(output))
            else:     
                output = loop.run_until_complete(process_sentences([text], loop=loop))
                print(output)

    # try/except to oppress this error: https://github.com/python/asyncio/issues/396
    try:
        loop.close()
    except:
        pass
