#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'data/parsed_preferences.jsonl'
OUT=ROOT/'data/normalized_preferences.jsonl'
def normalize_prompt(prompt): return ' '.join(prompt.strip().split()).lower()
def main():
    out=[]
    with IN.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                r=json.loads(line); r['_prompt_key']=normalize_prompt(r['prompt']); out.append(r)
    with OUT.open('w',encoding='utf-8') as f:
        for r in out: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'Normalized {len(out)} preference records to {OUT}')
if __name__=='__main__': main()
