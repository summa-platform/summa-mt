#!/usr/bin/env python3
# This is a pika-based worker. It's not the most effective way of interacting
# with an AMQP broker, but the easiest to understand.

import sys, os, amqp, pika, time, logging
import task_handler
from task_handler import MessageHandler
from argparse import ArgumentParser
from pika.exceptions import *
from retry import retry

logger = logging.getLogger(__name__)

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
    logging.basicConfig(level=opts.verbose,format="%(levelname)s %(message)s")

    retry_delay = int(getattr(opts,'retry_delay','5'))
    startup_delay = int(getattr(opts,'startup_delay','0'))
    
    on_message = MessageHandler(opts)
    
    # the @retry decoration makes python retry if the
    # listed Exceptions are raised, after the delay specified
    @retry(AMQPConnectionError, delay=retry_delay)
    def consume():
        param = pika.URLParameters(opts.url)
        connection = pika.BlockingConnection(param)
        logger.info("Connected with %s"%opts.url)
        channel = connection.channel()
        channel.basic_qos(prefetch_count=opts.parallel)
        queue_in = channel.queue_declare(opts.request_queue)
        if len(opts.request_exchange):
            channel.exchange_declare(opts.request_exchange)
            channel.queue_bind(exchange=opts.request_exchange, queue=queue_in)
        if len(opts.response_exchange):
            channel.exchange_declare(opts.response_exchange)
        
        channel.basic_consume(on_message, queue=queue_in.method.queue)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            connection.close()
            return
        return
    consume()
    
