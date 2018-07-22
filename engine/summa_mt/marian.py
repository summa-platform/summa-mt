#!/usr/bin/env python3

"""
Process wrapper for marian server.
"""
import sys, time, argparse, logging, asyncio, signal
import multiprocessing
from websocket import create_connection
from asyncio.subprocess import create_subprocess_exec as subprocess, PIPE, STDOUT

logger = logging.getLogger(__name__)

async def read_from_stream(stream,callback):
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break
        

class MarianServer(object):
    def __init__(self,
                 executable="./marian-server",
                 config="./model/marian/decoder.yml",
                 port=8080):
        self.server = None
        self.config = config
        self.executable = executable
        self.port = port
        self.running_monitor = None
        pass

    async def monitor(self):
        def log(msg):
            logger.info("[marian-server] %s"%msg.decode())
            pass
        await asyncio.wait([read_from_stream(self.server.stdout,log),
                            read_from_stream(self.server.stderr,log)])
    
    async def _start(self):
        cmd = [self.executable,
               "-c", self.config,
               "--log-level", "critical",
               "--cpu-threads", "%d"%multiprocessing.cpu_count(),
               "--optimize",
               "--mini-batch", "64"]
        logger.info("starting marian-server ... ")
        
        self.server = await subprocess(*cmd,stderr=PIPE,stdout=PIPE,loop=self.loop)
        # wait until the server is ready
        retries = 30
        while retries:
            await asyncio.sleep(1)
            try:
                conn = create_connection("ws://localhost:%d/translate"%self.port)
                break
            except:
                retries -= 1
                pass
            pass
            
        # while True:
        #     line = await self.server.stderr.readline()
        #     line = line.decode()
        # logger.info("[marian-server]: %s"%line)
        #     if line.find("Server is listening on port ") >= 0:
        logger.info("marian-server started")
        #         break
        #     pass
        # let monitoring take over
        self.running_monitor = asyncio.ensure_future(self.monitor())
        return

    def start(self,loop):
        self.loop = loop
        return self.loop.run_until_complete(self._start())

    async def _translate_single_line(self,conn,batch):
        conn.send(line)
        result = conn.recv()
        return conn.recv()

    async def _translate(self,batch):
        # TO DO:
        # - retry connection if it fails
        # - split large batches into smaller ones and send a heart beat for each
        #   batch
        
        try:
            conn = create_connection("ws://localhost:%d/translate"%self.port)
        except:
            logger.critical("No connection to server at port %d"%self.port)
            return None
            pass
        # logger.debug("got batch"+batch)
        conn.send(batch)
        result = conn.recv()
        conn.close()
        return result.rstrip()

    def translate(self,batch):
        # translation = [asyncio.ensure_future(self._translate("\n".join(batch)))]
        # for line in batch]
        # translation = self.loop.run_until_complete(asyncio.gather(*translation))
        translation = self.loop.run_until_complete(self._translate("\n".join(batch)))
        return translation

    async def _stop(self):
        if self.server:
            try:
                self.server.kill()
            except:
                pass
            pass
        # loog all trailing output of the server
        if self.running_monitor:
            await asyncio.gather(self.running_monitor)
        logger.info("Server stopped")
        self.server = None
        try:
            asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Got Cancelled Error")
            pass
        return
    
    def stop(self):
        self.loop.run_until_complete(self._stop())
        return

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--batch-size", type=int, default=1)
    parser.add_argument("-p", "--port", type=int, default=8080)
    return parser.parse_args()


def shutdown():
    # loop.run_until_complete(asyncio.gather(self.running_monitor))
    asyncio.ensure_future(asyncio.get_event_loop.stop())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(levelname)s:  %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")
    exe = "/home/shared/germann/code/marian-dev/build/marian-server"
    cfg = "/home/shared/germann/code/marian-dev/models/uedin-wmt18-de-en-run5/marian/decoder.yml"
    M = MarianServer(exe,cfg)
    loop = asyncio.get_event_loop()
    
    # loop.run_until_complete(M.start(loop))
    M.start(loop)
    # M.translate
    # loop.run_until_
    # while True:
    #     await asyncio.sleep(3)
    #     pass
    for i in range(20):
        print(M.translate(["oh wie schön ist Panama ."]))
        time.sleep(.5)
        pass
    try:
        # trans = M.translate(['auch diese Woche war wichtig .']*100)
        trans = M.translate(['auch diese Woche war wichtig .']*5)
        print(trans)
    except:
        pass
    # M.stop()
    # M.start(loop)
    # pass
    M.stop()
    # shutdown()
    # loop.run_until_complete(asyncio.sleep(10))
    # loop.close()
    
    # loop.run_forever()
    # loop.run_until_complete(M.stop())
    
    # monitor.cancel()
    loop.close()
    
    # asyncio.wait(monitor)
    
    # args = parse_args()

    # count = 0
    # batch = ""
    # for line in sys.stdin:
    #     count += 1
    #     batch += line.decode('utf-8') if sys.version_info < (3, 0) else line
    #     if count == args.batch_size:
    #         translate(batch, port=args.port)
    #         count = 0
    #         batch = ""

    # if count:
    #     translate(batch, port=args.port)
