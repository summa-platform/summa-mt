#!/usr/bin/env python3
import logging, pika
from marian import Translator

def setup_argparser(ap):
    ap.add_argument("-m", "--model-path", default = "model",
                    help = "path to directory where models reside")

class MessageHandler(object):
    def __init__(self, opts = None):
        self.exchange = getattr(opts,'response_exchange','')
        mpath = getattr(opts,'model_path','model')
        self.translate = Translator(mpath)
        return
    
    def __call__(self, ch, method, properties, body):
        # print(" [x] Received %r" % body)
        # print(" [x] Properties ", properties)
        
        # TO DO: unpack task json structure from body and transform to
        # list of strings
        
        translation = self.translate(body.decode('utf8'))
        if type(translation).__name__ == 'list':
            translation = "\n".join(translation)
            pass

        # TO DO: pack result into SUMMA json response structure
        
        if len(self.exchange): ch.exchange_declare(self.exchange)
        ch.basic_publish\
            (exchange = self.exchange, body = translation.encode('utf8'),
             routing_key = properties.reply_to,
             properties = pika.BasicProperties(
                 correlation_id = properties.correlation_id,
             ))
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
        if type(translation).__name__ == 'list':
            translation = "\n".join(translation)
            pass
        ch.exchange_declare(self.exchange)
        ch.basic_publish\
            (exchange = self.exchange, body = translation.encode('utf8'),
             routing_key = properties.reply_to,
             properties = pika.BasicProperties(
                 correlation_id = properties.correlation_id,
             ))
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
    pass # end of class definition for MessageHandler
