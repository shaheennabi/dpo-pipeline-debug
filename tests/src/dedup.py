#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'data/normalized_preferences.jsonl'
OUT=ROOT/'data/deduped_preferences.jsonl'
def deduplicate_records(path):
    records=[]
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip(): records.append(json.loads(line))
    seen=set(); unique=[]
    for r in records:
        if r['_prompt_key'] in seen: continue
        seen.add(r['_prompt_key']); unique.append(r)
    return unique
def main():
    rows=deduplicate_records(IN)
    with OUT.open('w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'Kept {len(rows)} unique preference records at {OUT}')
if __name__=='__main__': main()
