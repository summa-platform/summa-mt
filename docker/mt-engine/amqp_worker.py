#!/usr/bin/env python3
# This is a pika-based worker. It's not the most effective way of interacting
# with an AMQP broker, but the easiest to understand.

import sys, os, amqp, pika, time, logging, json
import task_handler
from task_handler import MessageHandler, DocumentTranslator
from argparse import ArgumentParser
from pika.exceptions import *
from retry import retry

from amqp.async_worker import AMQP_Worker as BasicWorker
logger = logging.getLogger(__name__)

class Worker(BasicWorker):
    def __init__(self, opts):
        url = opts.url
        queue = opts.request_queue
        exchange = opts.request_exchange
        exchange_type='topic'
        prefetch_count = getattr(opts,'prefetch_count',1)
        routing_key = '' # what is this used for when consuming messages?
        super().__init__(url,queue,exchange,exchange_type,
                         routing_key,prefetch_count)
        reply_headers = dict(resultProducerName='SUMMA-MT')
        self.reply_properties = pika.BasicProperties(headers=reply_headers)
        self.translate = DocumentTranslator(opts)
        return

    def send_reply(self, ch, properties, metadata, translation):
        rkeys = properties.headers['replyToRoutingKeys']
        exchange = properties.headers['replyToExchange']
        reply = { 'resultData' : translation,
                  'resultType' : 'finalResult',
                  'taskMetadata': metadata }
        try: # sending the reply
            ch.basic_publish(exchange=exchange,routing_key=rkeys['finalResult'],
                             properties=self.reply_properties,
                             body=json.dumps(reply,'utf8'))
            logger.info("Published result to %s:%s"%
                        (exchange,rkeys['finalResult']))
        except: # annouce failure and raise
            logger.info("Exception: %r"%sys.exc_info()[0])
            logger.info("Could not deliver results.")
            raise
        
        return
            
    def on_message(self, ch, basic_deliver, properties, body):
        logger.info("Got message: #%s"%basic_deliver.delivery_tag)
        msg_body = json.loads(body.decode('utf8'))
        payload = msg_body['taskData']
        metadata = msg_body['taskMetadata']
        start = time.time()
        translation = self.translate(payload)
        logger.info("Translation took %.2f sec."%(time.time()-start))
        self.send_reply(ch, properties, metadata, translation)

        try: # acknowledge the message
            self.acknowledge_message(basic_deliver.delivery_tag)
            logger.info("Acknowledged message #%r"%basic_deliver.delivery_tag)
        except Exception:
            logger.info("Exception: %r"%sys.exc_info()[0])
            logger.info("Could not acknowledge message.")
            raise
        return
    pass

def parse_args():
    p = ArgumentParser()
    if hasattr(amqp,'setup_argparser_common'):
        amqp.setup_argparser_common(p)
        pass
    if hasattr(task_handler,'setup_argparser'):
        task_handler.setup_argparser(p)
        pass
    return p.parse_args()

if __name__ == "__main__":
    opts = parse_args()
    logging.basicConfig(level=opts.verbose,format="[MT WORKER] %(levelname)s %(message)s")
    W = Worker(opts)
    try:
        W.run()
    except KeyboardInterrupt:
        W.stop()

# logger = logging.getLogger(__name__)


# def on_connection_closed(ch, reply_code:int, reply_text:str):
#     logger.error("Connection closed [%d]: %s"%(reply_code,reply_text))
#     return


# if __name__ == "__main__":
#     opts = parse_args()
#     logging.basicConfig(level=opts.verbose,format="%(levelname)s %(message)s")
#     retry_delay = int(getattr(opts,'retry_delay','5'))
#     startup_delay = int(getattr(opts,'startup_delay','0'))

#     on_message = MessageHandler(opts)
    
#     # the @retry decoration makes python retry if the
#     # listed Exceptions are raised, after the delay specified
#     @retry(AMQPConnectionError, delay=retry_delay)
#     def consume():
#         param = pika.URLParameters(opts.url)
#         connection = pika.BlockingConnection(param)
#         logger.info("Connected with %s"%opts.url)
#         channel = connection.channel()
#         channel.add_on_close_callback(on_connection_closed)
#         channel.basic_qos(prefetch_count=opts.parallel)
#         queue_in = channel.queue_declare(opts.request_queue)
#         logger.info("Input Queue: %r"%queue_in.method.queue)
#         if len(opts.request_exchange):
#             channel.exchange_declare(opts.request_exchange)
#             channel.queue_bind(exchange=opts.request_exchange, queue=queue_in)
#         if len(opts.response_exchange):
#             channel.exchange_declare(opts.response_exchange)
        
#         channel.basic_consume(on_message, queue=queue_in.method.queue)
#         try:
#             channel.start_consuming()
#         except KeyboardInterrupt:
#             channel.stop_consuming()
#             connection.close()
#             return
#         return
#     consume()
    
