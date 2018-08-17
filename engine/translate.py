#!/usr/bin/env python3

import sys, os, asyncio, traceback, logging, regex, copy, time
from asyncio.subprocess import create_subprocess_exec, create_subprocess_shell, PIPE
from os.path import join as pjoin
from summa_mt import marian
from summa_mt.marian import MarianServer
from summa_mt.preprocess import preprocess, init as init_preprocessor

logger = logging.getLogger(__name__)
basedir = os.path.realpath(os.path.dirname(__file__))

# environment variables are for testing outside Docker containers
MODEL_DIR = os.environ.get('MODEL_DIR', "/opt/model")
MODEL = None
MODEL_PATH = None
SOURCE_LANGUAGE = None
TARGET_LANGUAGE = None

BPE2_LANGS = ["de", "lv", "ru", "es", "fa", "pt"]

MARIAN_SERVER_EXECUTABLE \
    = os.environ.get('MARIAN_SERVER_EXECUTABLE',
                     pjoin('/opt/marian/marian-server'))

detok_cmd = None
detrue_cmd = None

MyMarianServer = None

def model_source_language():
    return MODEL.split('-')[0]

def model_target_language():
    return MODEL.split('-')[1]


def init(model, modeldir=MODEL_DIR,loop=None):
    global MODEL, MODEL_DIR, MODEL_PATH, SOURCE_LANGUAGE, TARGET_LANGUAGE
    global MyMarianServer, detok_cmd, detrue_cmd
    MODEL = model
    MODEL_DIR = modeldir or MODEL_DIR
    MODEL_PATH = pjoin(MODEL_DIR, MODEL)
    SOURCE_LANGUAGE, TARGET_LANGUAGE = MODEL.split('-')
    init_preprocessor(MODEL_DIR,SOURCE_LANGUAGE,TARGET_LANGUAGE)
    
    loop = loop or asyncio.get_event_loop()
    MyMarianServer = MarianServer(MARIAN_SERVER_EXECUTABLE,
                                  pjoin(MODEL_PATH,"decoder.yml"))
    MyMarianServer.start(loop)
    
    detok_cmd  = "%s/summa_mt/tokenizer/detokenizer.perl -penn -q -l %s"%(basedir,TARGET_LANGUAGE)
    detrue_cmd = "%s/summa_mt/recaser/detruecase.perl"%basedir


def shutdown():
    if MyMarianServer:
        MyMarianServer.stop()
        


async def postprocess(sentences, loop=None):
    logger.debug("Starting postprocessing")
    # src, trg = MODEL.split('-')
    src, trg = SOURCE_LANGUAGE, TARGET_LANGUAGE

    if SOURCE_LANGUAGE != 'ar':
        # find ' .nextsent'
        punct_fix = regex.compile(r'(\s)([.!?](?:\s*&quot;)?)\s*(\w+)', regex.U)

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

    if src in BPE2_LANGS:
        sentences = [regex.sub(r'@@(?: +|$)','',s) for s in sentences]
        # logger.debug("De-BPE.")
        # debpe = await create_subprocess_shell(DE_BPE, stdin=PIPE, stdout=PIPE, loop=loop)
        # out, err = await debpe.communicate(out)
        pass
    
    out = ('\n'.join(sentences) + '\n').encode('utf8')

    logger.debug("Detokenization: {}".format(detok_cmd))
    detok = await create_subprocess_shell(detok_cmd, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await detok.communicate(out)

    logger.debug("Detruecasing: {}".format(detrue_cmd))
    detrue = await create_subprocess_shell(detrue_cmd, stdin=PIPE, stdout=PIPE, loop=loop)
    out, err = await detrue.communicate(out)

    logger.debug("Postprocessing finished.")
    return out.decode('utf8').split('\n')


async def translate(sentences, loop=None):
    logger.debug("Start translating: {} sentences".format(len(sentences)))#.split('\n'))))
    if sentences and not sentences[-1]:
        sentences.pop()
        pass
    start = time.time()
    translation = await MyMarianServer._translate("\n".join(sentences))
    stop = time.time()
    logger.debug("Pure translation time: %.1f"%(stop-start))
    # print(translation,flush=True)
    # t = [MyMarianServer._translate(s) for s in sentences]
    # translation = await asyncio.gather(*t)
    return translation.split('\n')


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
    preprocessed = [sen for sen in (await preprocess(sentences, SOURCE_LANGUAGE, loop=loop)) if len(sen) > 0]
    translated = await translate(preprocessed, loop=loop)
    post = await postprocess(translated, loop=loop)
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

    # logger.debug(document)

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

    import argparse, json
    from argparse import ArgumentDefaultsHelpFormatter as ArgHelpFormatter
    parser = argparse.ArgumentParser(description='Machine Translation',
                                     formatter_class=ArgHelpFormatter)
    parser.add_argument('--debug', action='store_true',
                        help='debug mode')
    parser.add_argument('--debug-asyncio', action='store_true',
                        help='asyncio debug mode')
    parser.add_argument('--model-dir', '-d', type=str,
                        default=os.environ.get('MODEL_DIR', MODEL_DIR),
                        help='model directory')
    parser.add_argument('--model', '-m', type=str,
                        default=os.environ.get('MODEL'),
                        help='model name')
    parser.add_argument('--lines', '-l', action='store_true',
                        help='Translate each line as separate document')
    parser.add_argument('filename', nargs='+', type=str,
                        help='text or JSON file with translation data')
    args = parser.parse_args()

    logfmt  = '[%(lineno)d in %(pathname)s] %(asctime)s: '
    logfmt += '%(levelname)s: %(message)s'

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=logfmt)
    else:
        logging.basicConfig(level=logging.INFO, format=logfmt)
        pass
        
    if not args.model:
        print('error: specify model', file=sys.stderr)
        sys.exit(1)

    init(args.model, args.model_dir)

    loop = asyncio.get_event_loop()
    loop.set_debug(args.debug_asyncio)

    for filename in args.filename:
        if filename.endswith('json'):
            with open(filename, 'r') as f:
                task_data = json.load(f)
                pass
            output = loop.run_until_complete(
                translate_document(task_data, loop=loop))
        elif filename == "-":
            text = sys.stdin.read()
            text = text.split('\n\n')
            if args.debug:
                for t in text:
                    print(t)
                    pass
                pass
            start = time.time()
            output = loop.run_until_complete(
                process_sentences(text, loop=loop))
            stop = time.time()
            print("\n".join(output))
            print("%.1f sec. total translation time."%(stop-start),file=sys.stderr)
        else:
            with open(filename, 'r') as f:
                text = f.read()
            if args.lines:
                lines = text.splitlines()
                for line in lines:
                    output = loop.run_until_complete(
                        process_sentences([line], loop=loop))
                    print("\n".join(output))
            else:     
                output = loop.run_until_complete(
                    process_sentences([text], loop=loop))
                print(output)

    # try/except to oppress this error: https://github.com/python/asyncio/issues/396
    try:
        shutdown()
        loop.run_until_complete(asyncio.sleep(.1))
        loop.close()
    except:
        pass
