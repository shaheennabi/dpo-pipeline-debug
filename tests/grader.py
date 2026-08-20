#!/usr/bin/env python3
import importlib.util, json, re
from pathlib import Path

TEST=Path('/tests'); SOL=Path('/solution'); DATA=Path('/data')
MAX=180

def load(path):
    with path.open(encoding='utf-8') as f: return [json.loads(x) for x in f if x.strip()]

def key(prompt): return ' '.join(prompt.strip().split()).lower()

def expected_dedup(rows):
    seen=set(); out=[]
    for r in rows:
        k=key(r['prompt'])
        if k in seen: continue
        seen.add(k); out.append(r)
    return out

def trunc(s): return s if len(s)<=MAX else s[:MAX].rstrip()+'...'

def import_mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def check_exact(candidate, expected, label):
    if len(candidate)!=len(expected): raise AssertionError(f'{label}: row count {len(candidate)} != {len(expected)}')
    for i,(a,e) in enumerate(zip(candidate,expected)):
        for field in ('id','prompt','chosen','rejected'):
            if a.get(field)!=e.get(field): raise AssertionError(f'{label}: mismatch at row {i}, field {field}, candidate id={a.get("id")}, expected id={e.get("id")}')

def main():
    raw=load(DATA/'raw_preferences.jsonl')
    hidden=load(TEST/'hidden_preferences.jsonl')
    expected=expected_dedup(raw)
    cand_dedup=load(SOL/'data/deduped_preferences.jsonl')
    cand_final=load(SOL/'data/final_preferences.jsonl')
    expected_final=[{'id':r['id'],'prompt':r['prompt'],'chosen':trunc(r['chosen']),'rejected':trunc(r['rejected'])} for r in expected]
    functional=constraint=robust=artifact=1.0
    try:
        check_exact(cand_dedup,expected,'visible dedup')
        check_exact(cand_final,expected_final,'visible final')
    except AssertionError as e:
        functional=0.0; print('FUNCTIONAL FAILURE:',e)
    # Direct semantic checks of candidate implementation on hidden data.
    try:
        parse_mod=import_mod(SOL/'src/parse.py','candidate_parse')
        dedup_mod=import_mod(SOL/'src/dedup.py','candidate_dedup')
        fmt_mod=import_mod(SOL/'src/format.py','candidate_format')
        tmp=TEST/'_hidden_work.jsonl'
        parsed=[]
        for idx,r in enumerate(hidden,1):
            rr=dict(r); rr['_source_index']=idx; rr['_prompt_key']=key(rr['prompt']); parsed.append(rr)
        tmp.write_text('\n'.join(json.dumps(x) for x in parsed)+'\n',encoding='utf-8')
        # Exercise the function directly against an independently created hidden fixture.
        got=dedup_mod.deduplicate_records(tmp)
        exp=[]; seen=set()
        for r in parsed:
            k=key(r['prompt'])
            if k in seen: continue
            seen.add(k); exp.append(r)
        if [r['id'] for r in got] != [r['id'] for r in exp]: raise AssertionError('hidden dedup semantics mismatch')
        for r in exp:
            out=fmt_mod.format_record(r,MAX)
            if out != {'id':r['id'],'prompt':r['prompt'],'chosen':trunc(r['chosen']),'rejected':trunc(r['rejected'])}: raise AssertionError(f'hidden formatter mismatch for {r["id"]}')
    except Exception as e:
        robust=0.0; print('ROBUSTNESS FAILURE:',e)
    finally:
        try: (TEST/'_hidden_work.jsonl').unlink()
        except FileNotFoundError: pass
    report=SOL/'REPORT.md'
    if not report.exists(): artifact=0.0
    else:
        text=report.read_text(encoding='utf-8').lower()
        for token in ('root cause','verification','what was wrong','what i changed'):
            if token not in text: artifact=0.0
    # Constraint score is about not deleting legitimate rows except true normalized duplicates.
    if functional==1.0 and len(expected)==2200 and len(cand_dedup)==2200: constraint=1.0
    else: constraint=0.0
    overall=round((functional+constraint+robust+artifact)/4,3)
    reward={'overall':overall,'functional_correctness':functional,'constraint_satisfaction':constraint,'robustness':robust,'artifact_quality':artifact}
    Path('/tests/reward.json').write_text(json.dumps(reward,indent=2),encoding='utf-8')
    print(json.dumps(reward,indent=2))
    if overall < 1.0: raise SystemExit(1)
if __name__=='__main__': main()
