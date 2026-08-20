#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'data/deduped_preferences.jsonl'
OUT=ROOT/'data/final_preferences.jsonl'
MAX_RESPONSE_LENGTH=180
def truncate_response(text,max_length): return text if len(text)<=max_length else text[:max_length].rstrip()+'...'
def format_record(r,max_length): return {'id':r['id'],'prompt':r['prompt'],'chosen':truncate_response(r['chosen'],max_length),'rejected':truncate_response(r['rejected'],max_length)}
def main():
    with IN.open(encoding='utf-8') as f: rows=[format_record(json.loads(x),MAX_RESPONSE_LENGTH) for x in f if x.strip()]
    with OUT.open('w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'Formatted {len(rows)} preference records to {OUT}')
if __name__=='__main__': main()
