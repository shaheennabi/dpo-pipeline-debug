#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw_preferences.jsonl'
OUT=ROOT/'data/parsed_preferences.jsonl'
def validate(r):
    req={"id","prompt","chosen","rejected"}
    if set(r)!=req: raise ValueError(f"unexpected keys: {r.get('id')}")
    if any(not isinstance(r[k],str) for k in req): raise TypeError(r.get('id'))
    if not r['id'].strip() or not r['prompt'].strip(): raise ValueError(r.get('id'))
    return r
def main():
    out=[]
    with RAW.open(encoding='utf-8') as f:
        for n,line in enumerate(f,1):
            if not line.strip(): continue
            r=validate(json.loads(line)); r['_source_index']=n; out.append(r)
    with OUT.open('w',encoding='utf-8') as f:
        for r in out: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'Parsed {len(out)} preference records to {OUT}')
if __name__=='__main__': main()
