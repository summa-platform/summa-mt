#!/usr/bin/env python3

import aiohttp, asyncio, sys, os, regex, yaml
from contextlib import closing

CONNECTION_POOL_SIZE = 5 # max 5 connections to server
CHUNK_SIZE = 4096

async def download_file(session,url,fname):
    if os.path.exists(fname):
        return fname, True

    async with session.get(url) as response:
        if response.status == 200:
            saved = open(fname,'wb')
            chunk = await response.content.read(CHUNK_SIZE)
            while chunk:
                saved.write(chunk)
                chunk = await response.content.read(CHUNK_SIZE)
                pass
            saved.close()
            return fname,True
        else:
            print("[%d] Could not download %s"%(response.status,fname))
            return fname,False
        pass
    pass

@asyncio.coroutine
def download_model(session,url,dest):
    mi = "model_info.yaml"
    f,success = yield from download_file(session, "%s/%s"%(url,mi), "%s/%s"%(dest,mi))
    if not os.path.exists("%s/%s"%(dest,mi)): return False
    info = yaml.load(open("%s/%s"%(dest,mi)))
    jobs = [download_file(session, "%s/%s"%(url,f),"%s/%s"%(dest,f))
            for f in info['files']]
    for j in asyncio.as_completed(jobs):
        f,success = yield from j
        print(f,success)
        pass
    return

def main(opts):
    try: os.makedirs(opts.dest)
    except: pass
    base_url = regex.sub(r'(/(model_info\.yaml)?)?$','',opts.url)
    with closing(asyncio.get_event_loop()) as loop:
        conn = aiohttp.TCPConnector(limit=CONNECTION_POOL_SIZE)
        with aiohttp.ClientSession(loop=loop, connector=conn) as session:
            job = download_model(session,base_url,opts.dest)
            result = loop.run_until_complete(job)
    return

if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("url",nargs='?',default="http://data.statmt.org/summa/mt/models/de-en/20180712/model_info.yaml")
    p.add_argument("dest",nargs='?',default="downloads")
    opts = p.parse_args()
    main(opts)
    
