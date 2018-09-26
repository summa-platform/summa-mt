#!/usr/bin/env python3
"""
Very simple script to test the interaction with the 
translation worker.
"""

import pika, sys, threading, time

def on_message(ch, method, properties, body):
    id = int(properties.correlation_id)
    print(" [%s] Received: '%s'"%(id,body.decode('utf8').strip()))
    ch.basic_ack(delivery_tag = method.delivery_tag)
    pass

def print_translations(channel,queue_name):
    channel.basic_consume(on_message, queue=queue_name)
    channel.start_consuming()
    
params = pika.ConnectionParameters(host='localhost')
connection = pika.BlockingConnection()
channel = connection.channel()

q = channel.queue_declare(queue='requests')#,durable=True)
channel.exchange_declare('foo')
r = channel.queue_declare('',exclusive=True,auto_delete=True)
channel.queue_bind(exchange='foo',queue=r.method.queue)
result_printer = threading.Thread(target=print_translations,
                                  args = (channel, r.method.queue,))
# result_printer.daemon = True
result_printer.start()

i = 0
for line in sys.stdin:
    channel.basic_publish(exchange='', routing_key='requests',
                          body=line, properties = pika.BasicProperties(
                              reply_to=r.method.queue,
                              correlation_id="%d"%i,))
    i += 1
    pass

