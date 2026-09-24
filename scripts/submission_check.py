import json, os, glob, sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
CASES=os.path.join(ROOT,'cases')
EXPECTED=[f'HHG-{i:03d}.json' for i in range(1,21)]
errors=[]
files=sorted(os.path.basename(p) for p in glob.glob(os.path.join(CASES,'HHG-*.json')))
if files!=EXPECTED: errors.append(f'cases/ filenames mismatch: expected {EXPECTED}, got {files}')
for fn in EXPECTED:
    p=os.path.join(CASES,fn)
    try:d=json.load(open(p,encoding='utf8'))
    except Exception as e: errors.append(f'{fn}: invalid JSON: {e}'); continue
    required=['case_id','evidence','verdict','confidence','approval_route','next_best_action','recommended_actions','sar_required','playbook','nba_before_additional_evidence','additional_evidence_request','after_additional_evidence','evidence_progression','graph_writeback']
    missing=[k for k in required if k not in d]
    if missing: errors.append(f'{fn}: missing {missing}')
    if d.get('case_id') != fn[:-5]: errors.append(f'{fn}: case_id mismatch')
    if d.get('evidence_progression',{}).get('before_additional_evidence',{}).get('next_best_action') != d.get('next_best_action'): errors.append(f'{fn}: before NBA mismatch')
    if d.get('sar_required') and not d.get('sar_narrative'): errors.append(f'{fn}: SAR required but narrative empty')
    if d.get('graph_writeback',{}).get('status') != 'ready_for_tigergraph_writeback': errors.append(f'{fn}: graph writeback status missing')
for folder in ['answers']:
    af=sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT,folder,'HHG-*.json')))
    if af!=EXPECTED: errors.append(f'{folder}/ filenames mismatch')
if not os.path.exists(os.path.join(ROOT,'tigergraph/generated/benchmark_case_writeback.gsql')): errors.append('missing generated GSQL')
if errors:
    print('SUBMISSION CHECK: FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('SUBMISSION CHECK: PASS')
print('20/20 case files validated; explicit before/request/after NBA lifecycle present; SAR and graph-writeback manifests checked.')
