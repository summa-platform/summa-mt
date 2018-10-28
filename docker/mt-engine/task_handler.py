#!/usr/bin/env python3
import logging, pika, regex, sys, os, json, copy, yaml
import threading, time

name = 'SUMMA-MT' # required for responses

logger = logging.getLogger(__name__)

mydir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(mydir,"summa_mt"))

from marian import Translator
import marian

def setup_argparser(ap):
    if hasattr(marian,"setup_argparser"):
        marian.setup_argparser(ap)
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
            if len(paragraphs[-1]): paragraphs.append([])
        else:
            paragraphs[-1].append(t)
        pass
    return [" ".join(p) for p in paragraphs]

class DocumentTranslator(object):

    def __init__(self, opts):
        #mpath = getattr(opts,'model','model')
        self.translate = Translator(opts)
        self.trglang = self.translate.trglang
        return

    def __call__(self,document):
        jobs = [copy.deepcopy(i) for i in document['instances']
                if i['metadata']['language'] == self.trglang]
        for j in jobs:
            pars = [extract_text(s) for s in j['body']['sentences']]
            sents = [s for p in pars for s in p]
            ready = []
            # for i in range(len(sents)):
            #     logger.info("[%d] %s"%(i,sents[i]))
            translated = self.translate(sents)
            for t in translated:
                # logger.info(t)
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

    def wait_for_translation(self,done,ch,q,delay=5):
        """
        Wait for translation job running in the background to be /done/.
        Send a heart beat to the message broker every /delay/ seconds by 
        passively declaring queue /q/ on channel /ch/. The heart beat is 
        necessary to tell RabbitMQ not to close the connection for being 
        idle for too long.
        """
        start = time.clock()
        done.wait(delay)
        while not done.is_set():
            try:
                ch.queue_declare(queue=q,passive=True)
            except:
                logging.warn("Can't declare queue '%s'!."%q)
                raise
            logging.info("Waiting ... (%.2f sec.)"%(time.clock()-start))
            done.wait(delay)
            pass
        logging.info("Done after %.2f sec."%(time.clock()-start))
        return
    
    def __call__(self, ch, method, properties, body):

        print(method)
        
        
        msg_body = json.loads(body.decode('utf8'))

        routing_keys = properties.headers['replyToRoutingKeys']
        reply_to_exchange = properties.headers['replyToExchange']
        props = pika.BasicProperties(headers=dict(resultProducerName='SUMMA-MT'))

        done = threading.Event() # will be set when we're done
        translation = None
        def run_translation():
            translation = self.translate(msg_body['taskData'])
            done.set()

        # we run the translation in the background, because apparently
        # accessing connections from different threads doesn't really work
        bgjob = threading.Thread(target=run_translation)
        bgjob.daemon = True # exit when this script crashes 
        bgjob.start()
        self.wait_for_translation(done,ch,routing_keys['partialResult'])
        bgjob.join()

        # report final result
        reply = dict(resultData=translation,
                     resultType='finalResult',
                     taskMetadata=msg_body['taskMetadata'])
        try:
            ch.basic_publish(exchange = reply_to_exchange,
                             routing_key = routing_keys['finalResult'],
                             properties = props,
                             body = json.dumps(reply, 'utf8'))
            logger.info("Published result to %s:%s"%(reply_to_exchange,routing_keys['finalResult']))
        except Exception:
            logger.info("Exception: %r"%sys.exc_info()[0])
            logger.info("Could not deliver results.")

        try:
            ch.basic_ack(delivery_tag = method.delivery_tag)
            logger.info("Acknowledged message #%r"%method.delivery_tag)
        except Exception:
            logger.info("Exception: %r"%sys.exc_info()[0])
            logger.info("Could not deliver ack msg.")
            pass
        return
    pass # end of class definition for MessageHandler
