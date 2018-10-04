#!/usr/bin/env python3

import aiohttp, asyncio, sys, os, regex, yaml, subprocess
from contextlib import closing

# mydir = os.path.dirname(__file__)

CONNECTION_POOL_SIZE = 5 # max 5 connections to server
CHUNK_SIZE = 4096

from summa_mt.truecase import Truecaser as tc

def build_truecase_database(mdir, force):
    # Truecase database is big and not included in the download
    cfg = "%s/preprocess.yml"%mdir
    if not os.path.exists(cfg): return
    info = yaml.load(open(cfg))
    for s in [ x for x in info['steps'] if x['action'] == 'truecase']:
        if not 'model' in s: continue
        mdl = "%s/%s"%(mdir, s['model'])
        db = "%s.dbm"%mdl
        if force and os.path.exists(db):
            os.unlink(db)
        if not os.path.exists(db): tc(mdl)
        pass
    return

async def download_file(session,url,fname,force=False):
    found = os.path.exists(fname)
    if found and not force:
        return fname, 'ALREADY THERE'

    async with session.get(url) as response:
        if response.status == 200:
            saved = open(fname,'wb')
            chunk = await response.content.read(CHUNK_SIZE)
            while chunk:
                saved.write(chunk)
                chunk = await response.content.read(CHUNK_SIZE)
                pass
            saved.close()
            return fname, "DOWNLOADED AGAIN" if found else "OK"
        else:
            print("[%d] Could not download %s"%(response.status,fname))
            return fname, "FAILED"
        pass
    pass

@asyncio.coroutine
def download_model(session,url,dest,force=False):
    mi = "model_info.yml"
    f,success = yield from download_file(session, "%s/%s"%(url,mi), "%s/%s"%(dest,mi), force)
    if not os.path.exists("%s/%s"%(dest,mi)): return False
    info = yaml.load(open("%s/%s"%(dest,mi)))
    jobs = [download_file(session, "%s/%s"%(url,f),"%s/%s"%(dest,f), force)
            for f in info['files']]
    for j in asyncio.as_completed(jobs):
        f,success = yield from j
        print(f, success)
        pass
    return

def get_url_and_dest(opts):
    if opts.url:
        if not opts.mpath:
            raise Exception("Option --url requires --path")
        return opts.url, opts.mpath
    catalog = yaml.load(open(opts.config))
    lpair = opts.lpair
    if not lpair in catalog['mt-models']:
        raise Exception("No models listed for language pair '%r'"%lpair)
    choices = catalog['mt-models'][lpair]
    version = choices.get('latest') if opts.version=='latest' else opts.version
    info = choices.get(version, None)
    if not info:
        raise Exception("Requested model version '%s' not listed."%opts.version)
    path = opts.mpath if opts.mpath else \
           "%s/mt/%s/%s"%(opts.mroot, opts.lpair, version)
    return info['URL'], path

def main(opts):
    url, dest = get_url_and_dest(opts)
    print(url,dest)
    try: os.makedirs(dest)
    except: pass

    base_url = regex.sub(r'(/(model_info\.yml)?)?$','', url)
    with closing(asyncio.get_event_loop()) as loop:
        conn = aiohttp.TCPConnector(limit=CONNECTION_POOL_SIZE)
        with aiohttp.ClientSession(loop=loop, connector=conn) as session:
            job = download_model(session,base_url, dest, opts.force)
            result = loop.run_until_complete(job)
            pass
        pass

    # build_truecase_database(dest,opts.force)
    os.chdir(dest)
    info = yaml.load(open('model_info.yml'))
    # print(yaml.dump(info))
    for f in info.get('unpack-after-download',[]):
        if f.endswith('.tgz') or f.endswith('.tar.gz'):
            if os.path.getsize(f):
                subprocess.call(['tar','xvzf',f])
                # leave empty file to prevent downloading again:
                open(f,'w').close() 
        elif f.endswith('.zip'):
            if os.path.getsize(f):
                subprocess.call(['unzip',f])
                # leave empty file to prevent downloading again:
                open(f,'w').close() # empty file
            pass
        pass
    return

if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("--config", "-c", default="catalog.yml",
                   help="Catalog of available models.")
    p.add_argument("--url", help="Download directly from URL")
    p.add_argument("--force","-f", action='store_true',
                   help="Force download, even if files exist.")
    p.add_argument("lpair", nargs='?', help = "language pair")
    p.add_argument("version", nargs='?', default='latest',
                   help = "model version")
    p.add_argument("-M", dest="mroot", default="models",
                   help = "model root directory")
    p.add_argument("--path", dest="mpath", 
                   help="override automatic model path generation "
                   "with specific directory")
    opts = p.parse_args()
    main(opts)
    
