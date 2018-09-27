#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, regex as re, unicodedata

# Moses nomalize-punctuation-style rules. Kept for backwards compatibility.

# Some rules are overly agressive and should be revised. They also don't cut it
# for Unicode, as they leave much punctuation ambiguous (e.g., quotation marks).
# - UG

class Normalizer:
    def __init__(self,language,penn=False):
        rules = [(r'\r',''),
                 
                 (r'，', r','),
                 (r'。 *', r'. '),
                 (r'、', r','),
                 (r'”', r'"'),
                 (r'“', r'"'),
                 (r'∶', r':'),
                 (r'：', r':'),
                 (r'？', r'\?'),
                 (r'《', r'"'),
                 (r'》', r'"'),
                 (r'）', r'\)'),
                 (r'！', r'\!'),
                 (r'（', r'\('),
                 (r'；', r';'),
                 (r'１', r'"'),
                 (r'」', r'"'),
                 (r'「', r'"'),
                 (r'０', r'0'),
                 (r'３', r'3'),
                 (r'２', r'2'),
                 (r'５', r'5'),
                 (r'６', r'6'),
                 (r'９', r'9'),
                 (r'７', r'7'),
                 (r'８', r'8'),
                 (r'４', r'4'),
                 (r'． *', r'. '),
                 (r'～', r'\~'),
                 (r'’', r'\''),
                 (r'…', r'\.\.\.'),
                 (r'━', r'\-'),
                 (r'〈', r'\<'),
                 (r'〉', r'\>'),
                 (r'【', r'\['),
                 (r'】', r'\]'),
                 (r'％', r'\%'),

                 # Combining several rules from the Moses perl script
                 # here to deal with whitespacing around parentheses.
                 # This is actually something that should be dealt
                 # with in tokenization, not here. [UG]

                 # opening parenthesis:
                 (r' *\( *',' ('),
                 
                 # closing parenthesis:
                 (r' *\) *(?![.!:?;,])',') '), # space after ), 
                 (r' *\) +(?=[.!:?;,])',')'),  # ... except before .!:?;,
                 
                 (r'(\d) \%', r'\1%'),
                 (r' [:;]', r'\1')]
    
        if not penn:
            rules.extend([(r'`',"'"), ("''",' " ')])
            pass

        rules.extend(
            [(r'[„“”]','"'),
             (r'–', '-'),   # endash
             (r'—', ' - '), # emdash
             (r'´', "'"),
             (r'(\p{L})[‘’](\p{L})', r"\1'\2"),

             # The following will cause problems with nested quotations!
             # Also, see remarks on quotations and punctuation below. [UG]
             (r'[‘‚’]', '"'), 
             (r"''", '"'),
             (r'´´', '"'),

             # Disagree with the rule below, should be the other way around - UG
             (r'…', '...'), 

             # French quotes:
             # Note that the use of « and » as left / right actually
             # depends on the language, so the stuff below is not correct
             # for some languages. Again, the stuff below is based on the
             # original code from the Moses scripts. UG
             (r'([\xA0]*)«[\xA0]*', lambda m: ' "' if len(m.group(1)) else '"'),
             (r'[\xA0]*»([\xA0]*)', lambda m: '" ' if len(m.group(1)) else '"'),

             # handle non-breaking spaces (\xA0)
             (r'[\xA0]\%', '\%'),
             (r'nº[\xA0]', 'nº '), 
             (r'[\xA0]:', ':'),
             (r'[\xA0]ºC', ' ºC'),
             (r'[\xA0]cm', ' cm'),
             (r'[\xA0]\?', '\?'),
             (r'[\xA0]\!', '\!'),
             (r'[\xA0];', ';'),
             (r',[\xA0]', ', '),
            ]
        )
        
        if language == "en":
            # British and American English differ in their conventions around
            # quotation marks and punctuation. See link below:
            # www.thepunctuationguide.com/british-versus-american-style.html
            # This forces American style for English
            rules.append((r'"([,.]+)', r'\1"'))
        elif language in ["cs","cz"]: # "Czech is confused ,"
            # says "Czech is confuzed 
            pass
        else:
            # first quotation mark, then comma
            rules.append((',"','",'))
            # Don't fix period at end of sentence.
            # (For German that's actually not always correct, see
            # www.duden.de/sprachwissen/rechtschreibregeln/anfuehrungszeichen
            # specifically, if the end-of sentence mark is part of the
            # quotation, it stays inside the quotation marks. Just
            # sayin' - UG)
            rules.append((r'([.]+)"(\s*[^<])',r'"\1\2'))
            pass

        if language in ["de","es","cz","cs","fr"]:
            # isn't this the wrong way around? At least for German, the
            # thousands separator is '.' and the decimal marker ','
            rules.append((r'(\d)[\xA0](\d)', r'\1,\2'))
        else:
            rules.append((r'(\d)[\xA0](\d)', r'\1.\2'))
            pass
        
        rules.append((r'\s+', ' ')) # single space between tokens
        self.rules = [(re.compile(x),y) for x,y in rules]
        return

    def __call__(self,line):
        line = unicodedata.normalize('NFKC',line)
        for pattern,replacement in self.rules:
            line = pattern.sub(replacement,line)
            pass
        return line.strip()
    pass # end of class definition

if __name__ == "__main__":

    from argparse import ArgumentParser

    def interpret_args():
        p = ArgumentParser()
        p.add_argument("-b",action='store_true',dest="flush",
                       help="Flush output buffer after each line") 
        p.add_argument("--penn",action='store_true',
                       help="Penn Treebank mode")
        p.add_argument("-l",dest='lang', default="en",
                       help="ISO 639-1 two-letter language code")
        return p.parse_args()

    opts = interpret_args()
    normpunct = Normalizer(opts.lang,opts.penn)
    for line in sys.stdin:
        print(normpunct(line),flush=opts.flush)
        pass
    

       
