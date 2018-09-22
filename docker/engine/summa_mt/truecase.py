#!/usr/bin/env python3
"""
Simple re-implementation of truecase.perl.
Currently doesn't handle XML.
"""

import sys, os, dbm, shelve
from collections import defaultdict

class Truecaser:

    def __init__(self, model=None):
        self.db = None
        if model: self.load_model(model)
        self.sentence_end = dict([(x,1) for x in ".:?!"])
        self.delayed_sentence_start  \
            = dict([(x,1) \
                    for x in ["(","[",'"',"&apos;","&quot;","&#91;","&#93;"]])
        return

    def load_model(self,model):
        if model[-4:] == ".dbm":
            model = model[:-4]
            pass
    
        if os.path.exists(model+".dbm"):
            self.db = dbm.open(model+".dbm",'r')
            return
    
        self.db = dbm.open(model+".dbm",'c')
        for line in open(model):
            x = line.strip().split(' ')
            for i in range(0,len(x),2):
                self.db[x[i]] = ""
                pass
            self.db[x[0].lower()] = x[0]
            pass
        self.db.close() # make sure things get written to disk
        self.db = dbm.open(model+".dbm",'r')
        return 

    def __call__(self,line,asr=False):
        sos = True # start of sentence
        ret = []
        for w in line.strip().split():
            if sos or asr or w not in self.db:
                # At the start of a sentence or when dealing with ASR output,
                # always use the most frequent form:
                x = self.db.get(w.lower(),b'').decode('utf8')
                ret.append(x if len(x) else w)
            else: ret.append(w)
            if w in self.sentence_end:
                sos = True
            elif w not in self.delayed_sentence_start:
                sos = False
                pass
            pass
        return " ".join(ret)

    def __del__(self):
        pass
    pass

if __name__ == "__main__":
    truecase = Truecaser(sys.argv[1])
    for line in sys.stdin:
        print(truecase(line,asr=True))
        pass
    
    
    


