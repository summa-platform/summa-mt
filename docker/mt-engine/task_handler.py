#!/usr/bin/env python3
import logging, pika, regex, sys, os, json, copy, yaml

name = 'SUMMA-MT' # required for responses

logger = logging.getLogger(__name__)

mydir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(mydir,"summa_mt"))

from marian import Translator

def setup_argparser(ap):
    ap.add_argument("--model-path", "-m",
                    default = os.environ.get('MT_MODEL_PATH','/model'),
                    help = "path to directory where models reside")
    return

def encode_sentence(s):
    return { 'tokens' : 
             [ {'token': { 'offset' : i, 'token': w }, 'features' : [] }
               for i,w in enumerate(s.strip().split()) ] }

ptag = regex.compile(r'^</?[pP]>$')

def extract_text(blob):
    tokens = [ x['token']['token'] for x in blob['tokens'] ]
    paragraphs = [[]]
    for t in tokens:
        if ptag.match(t):
            if len(pars[-1]): pars.append([])
        else:
            paragraphs[-1].append(t)
        pass
    return [" ".join(p) for p in paragraphs]

class DocumentTranslator(object):

    def __init__(self, opts):
        mpath = getattr(opts,'model_path','model')
        self.translate = Translator(mpath)
        self.trglang = self.translate.trglang
        return

    def __call__(self,document):
        jobs = [copy.deepcopy(i) for i in document['instances']
                if i['metadata']['language'] == self.trglang]
        for j in jobs:
            pars = [extract_text(s) for s in j['body']['sentences']]
            sents = [s for p in pars for s in p]
            ready = []
            translated = self.translate(sents)
            for t in translated:
                logger.info(t)
                if type(t).__name__ == 'str':
                    ready.append(encode_sentence(t))
                else:
                    ready.extend([encode_sentence(s) for s in t])
                    pass
                pass
            j['body']['sentences'] = ready
            pass
        document['instances'].extend(jobs)
        return document
    pass

class MessageHandler(object):
    def __init__(self, opts = None):
        self.exchange = getattr(opts,'response_exchange','')
        self.translate = DocumentTranslator(opts)
        return
    
    def __call__(self, ch, method, properties, body):
        msg_body = json.loads(body.decode('utf8'))

        routing_keys = properties.headers['replyToRoutingKeys']
        reply_to_exchange = properties.headers['replyToExchange']
        
        doc_in = msg_body['taskData']
        translation = self.translate(doc_in)
        reply = dict(resultData=translation,
                     resultType='finalResult',
                     taskMetadata=msg_body['taskMetadata'])

        props = pika.BasicProperties(headers=dict(resultProducerName='SUMMA-MT'))
        ch.basic_publish(exchange = reply_to_exchange,
                         routing_key = routing_keys['finalResult'],
                         properties = props,
                         body = json.dumps(reply, 'utf8'))
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
    pass # end of class definition for MessageHandler
