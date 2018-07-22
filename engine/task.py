#!/usr/bin/env python3

import sys, os, asyncio, traceback, time, json
from concurrent.futures import ThreadPoolExecutor as Executor   \
    # or ProcessPoolExecutor as Executor

from worker_pool import WorkerProcessPool, ErrorMessage

from translate import translate_document, init as init_mt, \
    model_source_language, MODEL_DIR, shutdown as shutdown_mt


class RejectError(Exception): pass
class RejectRequeueError(Exception): pass
class ErrorMessage(Exception): pass
class NoReply(Exception): pass

name = 'SUMMA-MT' # required by rabbitmq module

collect_test_data = False
test_data_dir = 'test'


def init(args=None):
    global pool, model_src_lang, collect_test_data
    model_src_lang = args.model.split('-')[0]
    collect_test_data = args.collect_test_data
    if collect_test_data:
        print('Only test data collecting')
    pool = WorkerProcessPool(worker_run, init_module, count=args.PARALLEL,
                             heartbeat_pause=args.heartbeat_pause,
                             init_args=(args,))
    pool.start()
    # give some time for workers to start
    time.sleep(5)
    pool.watch_heartbeats(args.restart_timeout, args.refresh, args.max_retries_per_job)


def setup_argparser(parser):
    env = os.environ
    parser.add_argument('--model-dir', type=str, default=env.get('MODEL_DIR', MODEL_DIR), help='model directory (env MODEL_DIR)')
    parser.add_argument('--model', type=str, default=env.get('MODEL'), help='model (env MODEL)')
    parser.add_argument('--heartbeat-pause', type=int, default=env.get('HEARTBEAT_PAUSE', 10),
            help='pause in seconds between heartbeats (or set env variable HEARTBEAT_PAUSE)')
    parser.add_argument('--refresh', type=int, default=env.get('REFRESH', 5),
            help='seconds between pulse checks (or set env variable REFRESH)')
    parser.add_argument('--restart-timeout', type=int, default=env.get('RESTART_TIMEOUT', 5*60),
            help='max allowed seconds between heartbeats, will restart worker if exceeded (or set env variable RESTART_TIMEOUT)')
    parser.add_argument('--max-retries-per-job', type=int,
                        default=env.get('MAX_RETRIES_PER_JOB', 3),
            help='maximum retries per job (or set env variable MAX_RETRIES_PER_JOB)')
    parser.add_argument('--test-data-dir', type=str, default='test', help='test data directory')
    parser.add_argument('--collect-test-data', action='store_true', help='collect test data only and write to test data directory')


def shutdown():
    global pool
    shutdown_mt()
    return pool.terminate()


def reset():
    global pool
    pool.reset()


async def process_message(task_data, loop=None, send_reply=None, metadata=None, reject=None, **kwargs):
    global collect_test_data, test_data_dir

    if collect_test_data:
        item = metadata.get('itemId', 'unknown')
        filename = os.path.join(test_data_dir, '%s.json' % item)
        print('Writing to %s' % filename)
        with open(filename, 'w') as f:
            json.dump(task_data, f, indent=2)
        # print('Requeueing item.')
        # reject(requeue=True)
        print('Waiting 5 seconds')
        await asyncio.sleep(5)
        # try:
        #     time.sleep(5)   # wait 5 seconds blocking main thread intentionally so no new messages are received
        # except KeyboardInterrupt:
        #     loop.stop()
        # raise NoReply('just took a look, requeued')
        raise RejectError('data collected, rejecting')

    src_lang = metadata['taskSpecificMetadata']['contentDetectedLangCode']
    if src_lang != model_src_lang:
        raise RejectError('wrong model: loaded model for source language %s, got request for %s' % (model_src_lang, src_lang))

    global pool
    async with pool.acquire() as worker:
        return await worker(task_data, send_reply)


# --- private ---

async def worker_run(document, partial_result_callback=None,
                     loop=None, heartbeat=None,
                     *args, **kwargs):
    return await translate_document(document, loop=loop)


def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def init_module(args):
    log('Initialize MT ...')
    init_mt(args.model, args.model_dir)
    log('MT worker initialized!')
    pass


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='Machine Translation Task', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--parallel', '-n', dest='PARALLEL', metavar='PORT', type=int, default=os.environ.get('PARALLEL',1),
            help='messages to process in parallel (or set env variable PARALLEL)')
    parser.add_argument('filename', type=str, default='test.json', nargs='?', help='JSON file with task data')

    setup_argparser(parser)

    args = parser.parse_args()

    init(args)

    print('Reading', args.filename)
    with open(args.filename, 'r') as f:
        task_data = json.load(f)
    metadata = dict(taskSpecificMetadata=dict(contentDetectedLangCode=args.model.split('-')[0]))

    async def print_partial(partial_result):
        print('Partial result:')
        print(partial_result)

    try:
        loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        result = loop.run_until_complete(process_message(task_data, loop=loop, send_reply=print_partial, metadata=metadata))
        print('Result:')
        print(result)
    except KeyboardInterrupt:
        print('INTERRUPTED')
    except:
        print('EXCEPTION')
        traceback.print_exc()
        # raise
    finally:
        shutdown()
