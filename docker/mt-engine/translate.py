#!/usr/bin/env python3
import sys, os, logging
logger = logging.getLogger(__name__)

mydir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(mydir,"summa_mt"))
from marian import Translator
from argparse import ArgumentParser

def parse_arguments(args=sys.argv[1:]):
    p = ArgumentParser()
    p.add_argument("-v", "--verbose", const='INFO', default='WARN',nargs='?')
    p.add_argument("-m", "--model", default=os.environ.get('MT_MODEL_PATH','/model'),
                   help="path to model directory")
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
        sys.exit(0)
