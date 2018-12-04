#!/usr/bin/env python3

import sys, os, yaml, dbm, shutil

def repl_vars(spec,variables):
    """Replace variables in specification."""
    if type(spec) is str:
        return spec.format(**variables)
    elif type(spec) is list:
        return [ repl_vars(x,variables) for x in spec ]
    elif type(spec) is dict:
        return dict((k.format(**variables),repl_vars(v,variables))
                    for k,v in spec.items())
    else:
        return spec
    return

from argparse import ArgumentParser
p = ArgumentParser()
p.add_argument("--config", "-c", required=True,
               help="image config file (in yaml format)")
p.add_argument("--dryrun", "-n", help="dryrun", action="store_true")
p.add_argument("--force", action="store_true",
               help="force copy even if target exists")
p.add_argument("--output", "-o", help="output directory", required=True)
p.add_argument("--license", help="Model License terms.",
               default="CC BY-SA 4.0")

opts = p.parse_args()
config = yaml.load(open(opts.config))

if not opts.dryrun:
    try:
        os.makedirs(opts.output)
    except:
        pass

# the preprocessing and postprocessing sections are optional
# model_info and decoder are mandatory
prepro    = config.get('preprocess')
postpro   = config.get('postprocess')
mdl_info  = config.get('model_info')
variables = config.get('variables')
decoder   = config.get('decoder')
filemap   = config.get('local')

assert mdl_info, "Section 'mdl_info' is required!"
assert decoder,  "Section 'decoder' is required!"
assert filemap,  "Section 'local' is required!"

if 'variables' in config:
    prepro,postpro,decoder,mdl_info,filemap \
        = [ repl_vars(s,variables)
            for s in [prepro,postpro,decoder,mdl_info,filemap] ]
    pass

def verify_file(fname):
    filepath = filemap.get(fname)
    if not filepath:
        raise Exception("No source file given for %s"%fname)
    if not os.path.exists(filepath):
        raise Exception("No such file: %s"%filepath)
    return filepath

def tc2dbm(src,trg,dryrun=False):
    """convert text-based truecase model to .dbm format."""
    if dryrun:
        print("Convert %s to %s"%(src,trg))
    else:
        if os.path.exists(trg):
            print("Skipping convertion of %s to %s: "
                  "target file exists"%(src,trg))
            return
        print("Converting truecasing model. This may take a while.",
              file=sys.stderr)
        db = dbm.open(trg+"_",'c')
        for line in open(src):
            x = line.strip().split(' ')
            for i in range(0,len(x),2):
                db[x[i]] = ""
                db[x[0].lower()] = x[0]
                pass
            pass
        db.close() # make sure things get written to disk
        os.rename(trg+"_",trg)
    return

def copy_file(src,trg, dryrun=False, force=False):
    if dryrun:
        print("Copy %s to %s"%(src,trg))
    elif os.path.exists(trg):
        if force:
            print("Overwriting %s."%src,file=sys.stderr) 
            shutil.copy2(src,trg)
        else:
            print("Skipping %s: target file exists."%src,file=sys.stderr)
            pass
    else:
        shutil.copy2(src,trg)
        pass
    return

files = []
dest = "%s/%%s"%(opts.output)
def provision(trg):
    if not trg: return
    src = verify_file(trg)
    copy_file(src,dest%trg,opts.dryrun,opts.force)
    files.append(trg)

def dump_yml(yml,trg,dryrun,force):
    if not yml: return
    files.append(trg)
    trg = dest%trg
    if dryrun:
        print("Create file '%s'."%trg)
    elif os.path.exists(trg) and not force:
        print("File '%s' exists, skipping it. "
              "Use --force to force overwrite."%trg,file=sys.stderr)
    else:
        print(yaml.dump(yml, indent=2,default_flow_style=False),
              file=open(trg,'w'))
    return

if prepro:
    for step in prepro['steps']:
        action = step.get('action')
        if action == 'truecase':
            trg = step['model']
            src = verify_file(trg)
            tc2dbm(src,dest%trg,opts.dryrun)
            files.append(trg)
        elif action == "bpe":
            provision(step['codes'])
            provision(step.get('vocabulary'))
        pass
    dump_yml(prepro, "preprocess.yml", opts.dryrun, opts.force)
    pass

for trg in decoder['models']:
    provision(trg)
for trg in decoder['vocabs']:
    provision(trg)
    
#dump_yml(prepro,  "preprocess.yml", opts.dryrun, opts.force)
dump_yml(decoder, "decoder.yml", opts.dryrun, opts.force)
dump_yml(postpro, "postprocess.yml", opts.dryrun, opts.force)

have_license = False
for f in ["LICENSE","LICENSE.txt"]:
    if f in mdl_info['files']:
        have_license=True
        break
    pass

LICENSE_LINK={"CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/"}
if not have_license:
    if opts.dryrun:
        print("Add LICENSE.txt")
    else:
        files.append("LICENSE.txt")
        with open(dest%"LICENSE.txt",'w') as license:
            print("The models in this directory are licensed under %s."%opts.license,
                  file=license)
            if opts.license in LICENSE_LINK:
                print("(%s)"%LICENSE_LINK[opts.license], file=license)
                pass
            pass
        pass
    pass

for f in mdl_info['files']:
    if os.path.exists(dest%f) or f in files: continue
    provision(f)
    pass

mdl_info['files'].extend([f for f in files if not f in mdl_info['files']])
dump_yml(mdl_info, "model_info.yml", opts.dryrun, opts.force)

if opts.dryrun:
    print("Create Dockerfile")
else:
    with open(dest%"Dockerfile",'w') as f:
        f.write("FROM scratch\n")
        f.write("COPY . /model\n")
        pass
    pass
