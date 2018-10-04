#!/usr/bin/env python3

# TO DO:
# - check if marian is already running
# - allow connection to remote marian server

import regex, time, sys, os, logging, yaml
from prepostprocess import PrePostProcessor
from websocket import create_connection
from argparse import ArgumentParser
from subprocess import Popen, PIPE

logger = logging.getLogger(__name__)
basedir  = os.path.dirname(__file__)

# find the marian executable
marian = None
for guess in [os.environ.get('MARIAN_SERVER_EXE',None),
              "%s/bin/marian-server"%basedir,
              "/usr/bin/marian-server"]:
    if guess and os.path.exists(guess):
        marian = guess
        break
    pass
if not marian:
    raise Exception("Cannot find marian server executable.")

class MarianServer:
    def __init__(self,config):
        self.config = config
        self.marian = None
        return

    def start(self,loglevel='critical'):
        # marian = os.environ.get('MARIAN_SERVER_EXE',
        cmd = [marian, "-c", self.config, "--log-level", loglevel]
        self.marian = Popen(cmd)
        return
    
    def stop(self):
        if self.marian: self.marian.kill()
        return

    def __del__(self):
        self.stop()

class MarianClient:
    def __init__(self,remote):
        # host should be a full spec: protocol://host:port/path
        pattern = regex.compile(r"""(?P<protocol>.*?://)?(?P<host>.*?)
        (?P<port>:[0-9]+)?(?P<path>/.*)?$""",regex.VERBOSE)
        if remote:
            m = pattern.match(remote)

            # default protocol is (for the time being)
            self.prot = m.group('protocol') if m.group('protocol') else "ws://"
            self.host = m.group('host') if m.group('host') else 'localhost'
            self.port = m.group('port') if m.group('port') else ''
            self.path = m.group('path') if m.group('path') else ''
            self.url = "%s%s%s%s"%(self.prot, self.host, self.port, self.path)
        else:
            self.url = "ws://localhost:8080/translate"
        return

    def connect(self):
        if self.prot == "ws://": # web socket server
            return create_connection(self.url)
        elif self.prot == "amqp://":
            # not implemented yet
            return None
        elif self.prot.startswith("http"):
            # no permanent connection needed
            return None
        
    def reconnect(self):
        max_tries  = 60
        sleep_time = 1
        for attempt in range(max_tries):
            try:
                self.conn = self.connect()
                break
            except:
                if attempt + 1 < max_tries:
                    logger.info("Could not connect to translation server at %s. "
                                "%d tries left"%(self.url, max_tries - attempt - 1))
                    time.sleep(sleep_time)
                else:
                    logger.error("Fatal error: could not connect for "
                                 "%d seconds."%(sleep_time * max_tries))
                    raise "Connection Error"
                pass
            pass
        pass

    def translate(self,line):
        retries = 3
        while retries:
            try:
                self.conn.send(line)
                translation = self.conn.recv()
                break
            except:
                retries -= 1
                if not retries:
                    logger.error("Cannot communicate with server. Giving up.")
                    raise
                else: conn = self.reconnect()
                pass
            pass
        return translation
    pass # end of class definition of MarianClient

class Translator:
    def __init__(self, model_dir, marian = None):
        # marian should None for the time being
        # eventually it should be an optional specification of
        # host, port, and protocol of a connection to a marian service
        # (http(s), ws, amqp, etc.)
        self.model_info = yaml.load(open(model_dir+"/model_info.yml"))
        self.srclang = self.model_info['source-language']
        self.trglang = self.model_info['target-language']
        
        self.preprocess  = PrePostProcessor(model_dir+"/preprocess.yml")
        self.postprocess = PrePostProcessor(model_dir+"/postprocess.yml")
        if not marian:
            info = yaml.load(open(model_dir+"/decoder.yml"))
            marian = "ws://localhost:%d/translate"%info.get('port',8080)
            # print("MARIAN",marian)
            self.marian_server = MarianServer(model_dir+"/decoder.yml")
        else:
            self.marian_server = None
            pass
        self.marian_client = MarianClient(marian)
        self.start()
        return

    def start(self):
        if self.marian_server: self.marian_server.start()
        self.marian_client.reconnect()
        return

    def stop(self):
        if self.marian_server:
            self.marian_server.stop()
            pass
        return
    
    def __call__(self,paragraph):
        sentences = self.preprocess(paragraph)
        translation = self.marian_client.translate("\n".join(sentences))
        postprocessed = self.postprocess(translation.strip().split('\n'))
        return postprocessed
    
    pass # end of class definition

def parse_arguments(args=sys.argv[1:]):
    p = ArgumentParser()
    p.add_argument("-v", "--verbose", const='INFO', default='WARN',nargs='?')
    p.add_argument("-m", "--model", help="path to model directory")
    return p.parse_args()
    
if __name__ == "__main__":
    opts = parse_arguments()
    logging.basicConfig(level=opts.verbose,format="%(levelname)s %(message)s")
    translate = Translator(opts.model)
    try:
        for line in sys.stdin:
            logger.info("IN: %s"%line)
            if line.strip() == '': print()
            else:
                translation = translate(line)
                if type(translation).__name__ == 'str':
                    print(translation.strip())
                else:
                    for line in translation:
                        print(line)
                        pass
                    pass
                pass
            pass
    except KeyboardInterrupt:
        translate.stop()
        sys.exit(1)
