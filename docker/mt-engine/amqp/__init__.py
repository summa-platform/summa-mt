#!/usr/bin/env python3
import os

def setup_argparser_common(p):
    """Add options common to both worker and client"""
    # job queue parameters:
    p.add_argument('--reconnect-delay', type=int,
                   default=os.environ.get('RECONNECT_DELAY', 5),
                   help = 'number of seconds to wait before reconnect '
                   'attempt (or set env variable RECONNECT_DELAY)')

    p.add_argument('--reconnect-max-tries', type=int,
                   default=os.environ.get('RECONNECT_MAX_TRIES', 720),
                   help = 'max. number of attempts to reconnect '
                   'with message broker (or set env variable RECONNECT_MAX_TRIES)')

    p.add_argument('--startup-delay', type=int,
                   default=os.environ.get('STARTUP_DELAY', 0),
                   help='number of seconds to wait before starting '
                   'RabbitMQ client (or set env variable STARTUP_DELAY)')

    p.add_argument('--response-exchange', type=str,
                   default=os.environ.get('EXCHANGE_OUT',
                                          os.environ.get('RESPONSE_EXCHANGE','')),
                   help='exchange for responses (or set env variable RESPONSE_EXCHANGE)')

    p.add_argument('--request-exchange', type=str,
                   default=os.environ.get('REQUEST_EXCHANGE',''),
                   help='exchange for requests (or set env variable REQUEST_EXCHANGE)')

    p.add_argument('--request-queue', '-Q', type=str,
                   default=os.environ.get('QUEUE_IN',
                                          os.environ.get('REQUEST_QUEUE','requests')),
                   help='request queue (or set env variable REQUEST_QUEUE)')
    
    p.add_argument('--broker',dest='url', type=str,
                   default=os.environ.get('RABBITMQ_URL',
                                          os.environ.get('MESSAGE_BROKER_URL',
                                                         'amqp://localhost:5672')),
                   help='AMQP Broker URL (or set env variable MESSAGE_BROKER_URL)')

    p.add_argument("-v", "--verbose", nargs='?', const='INFO', default='WARN',
                   help = "level of verbosity (INFO, WARN, ERROR, CRITICAL)") 
    
    p.add_argument('--parallel', '-n', dest='parallel', type=int,
                   default=os.environ.get('PARALLEL',1),
                   help="messages to process in parallel "
                   "(or set env variable PARALLEL)")
    
