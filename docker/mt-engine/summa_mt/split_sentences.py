#!/usr/bin/env python3
"""
Sentence splitting module. Wraps around ESERIX for some languages,
?uses custom hacks for others.

TO DO: Eserix rules are actually just regular expressions. Consider implementing the sentence splitting directly in python
"""

import sys, os, logging, regex
from subprocess import Popen, PIPE

global ESERIX_CMD, ESERIX_RULES

logger = logging.getLogger(__name__)
basedir  = os.path.dirname(__file__)

ESERIX_RULES = None
guesses = [os.environ.get('ESERIX_RULES',
                          "%s/srx/rules.srx"%basedir),
           "%s/srx/rules.srx"%os.path.dirname(basedir)]

for guess in guesses:
    if guess and os.path.exists(guess):
        ESERIX_RULES = guess
        break
    else:
        logger.info("No Eserix rules found at %s:"%guess)
    pass

if not ESERIX_RULES:
    raise Exception("Cannot find Eserix rules within [%s]!"\
                    %(", ".join(guesses)))

ESERIX_CMD = None
for guess in [os.environ.get('ESERIX_CMD', '%s/bin/eserix'%basedir)]:
    if guess and os.path.exists(guess):
        ESERIX_CMD = guess
        break
    pass
if not ESERIX_CMD:
    raise Exception("Cannot find Eserix executable.")

# languages that Eserix can deal with
eserix_languages = ["ar", "de", "en", "es", "fr", "hr", "pl", "ru", "zh"]

# languages supported by nltk
nltk_languages = ["pt"]

# Other 
supported_languages = eserix_languages + ["fa"] 

class Eserix:
    def __init__(self,lang,cmd=ESERIX_CMD,rules=ESERIX_RULES):
        self.lang = lang
        self.cmd = [cmd, "-l", lang, "-r", rules, '-t']
        return

    def __call__(self,line):
        p = Popen(self.cmd, stdin=PIPE, stdout=PIPE, bufsize=1)
        out,err = p.communicate(line.encode('utf8'))
        return out.decode('utf8').strip().split('\n')
    pass

class NLTK_SentenceSplitter:
    def __init__(self, lang):
        D = { "pt" : "portuguese" }
        L = D[lang]
        self.ssplit = nltk.data.load('tokenizers/punkt/%s.pickle'%L)
        pass
    def __call__(self,line):
        return [regex.sub('\s+',' ',s).strip()
                for x in self.ssplit.tokenize(line)]
        
    pass

class SimpleSentenceSplitter:
    
    def __init__(self,language):
        self.sentpat = regex.compile(r'.*?(?:[.!?][\p{Pf}\p{Pe}]*|$)')
        pass

    def __call__(self,text):
        if not type(text).__name__ == 'str':
            text = text.decode('utf8')
        text = regex.sub(r'\s+',' ',text).strip()
        return [x.group(0).strip()
                for x in self.sentpat.finditer(text)
                if len(x.group(0))]
    pass
    
def force_split_long_sentences(sents,maxlen):
    """Brute-force splitting of long sentences"""
    sents = [s.strip().split() for s in sents]
    return [" ".join(s[i:i+maxlen]) for s in sents for i in range(0,len(s),maxlen)]

class SentenceSplitter:

    def __init__(self,lang,maxlen=0):
        if lang in eserix_languages: self.ssplit = Eserix(lang)
        elif lang in nltk_languages: self.ssplit = NLTK_SentenceSplitter(lang)
        else: self.ssplit = SimpleSentenceSplitter(lang)
        self.maxlen = maxlen
        return

    def __call__(self, text):
        sents = self.ssplit(text)
        if self.maxlen:
            sents = force_split_long_sentences(sents, self.maxlen)
        return  sents
            
if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser()

    p.add_argument("-l",dest="lang", default='en', choices=supported_languages,
                   help="language: one of %s"%(", ".join(supported_languages)))

    p.add_argument("--cmd", help = "Eserix command (full path)",
                   default=ESERIX_CMD)

    p.add_argument("--rules", help = "Eserix rules (full path)",
                   default=ESERIX_RULES)

    p.add_argument("-p", action='store_true', dest="one_par_per_line",
                   help = "one paragraph per line "
                   "(default is blank line between paragraphs)")
    
    p.add_argument("--flush", action='store_true',
                   help="flush after each paragraph")

    p.add_argument("--maxlen", type=int, default=0, help="maximum sentence length")

    opts = p.parse_args()

    ESERIX_CMD = opts.cmd
    ESERIX_RULES = opts.rules
    
    ssplit = SentenceSplitter(opts.lang)

    if opts.one_par_per_line:
        for line in sys.stdin:
            sents = ssplit(line)
            if opts.maxlen: sents = force_split_long_sentences(sents,opts.maxlen)
            print('\n'.join(sents), end='\n\n',flush=opts.flush)
    else:
        buffer = []
        for line in sys.stdin:
            line = line.strip()
            if len(line):
                buffer.append(line)
            elif len(buffer):
                sents = ssplit(' '.join(buffer))
                if opts.maxlen:
                    sents = force_split_long_sentences(sents,opts.maxlen)
                print('\n'.join(sents), end='\n\n',flush=opts.flush)
                buffer = []
                pass
            pass
        if len(buffer):
                sents = ssplit(' '.join(buffer))
                if opts.maxlen:
                    sents = force_split_long_sentences(sents,opts.maxlen)
                print('\n'.join(sents), end='\n\n',flush=opts.flush)
                pass
        pass
    
    
