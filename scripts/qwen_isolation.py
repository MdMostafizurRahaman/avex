"""Verified macOS read-only confinement for a single Qwen experiment."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def sandbox_profile(workspace: Path, runtime_home: Path, node_root: Path) -> str:
    paths = [workspace, runtime_home, node_root]
    if any(not p.is_absolute() or p.resolve() != p for p in paths):
        raise ValueError('Sandbox paths must be absolute canonical paths')
    if any(workspace == p or workspace.is_relative_to(p) or p.is_relative_to(workspace)
           for p in [runtime_home, node_root]):
        raise ValueError('Runtime paths must be disjoint from the condition workspace')
    def subpath(p: Path) -> str:
        return '(subpath ' + json.dumps(str(p)) + ')'
    return '\n'.join([
        '(version 1)', '(allow default)',
        '(deny file-read* (subpath "/Users") (subpath "/private/tmp") (subpath "/private/var/folders"))',
        '(allow file-read* ' + ' '.join(subpath(p) for p in paths) + ')',
        '(allow file-read-metadata)',
        '(deny file-write*)',
        '(allow file-write* ' + subpath(runtime_home) + ' (literal "/dev/null") (subpath "/dev/fd"))',
        '(deny network*)',
        '(allow network-outbound (remote ip "localhost:11434"))',
        '',
    ])



def verify_sandbox(profile: Path, workspace: Path, runtime_home: Path,
                   repo_root: Path) -> dict:
    """Test actual kernel denials before any model call (no sensitive data printed)."""
    other = repo_root / 'pilot/conditions' / ('E2' if workspace.name != 'E2' else 'E1')
    checks = {'target': str(workspace / 'controllers/panel/log.py'),
              'private': str(repo_root / 'config/scenario.json'),
              'ground_truth': str(repo_root / 'private/ground_truth'),
              'ancestor': str(repo_root),
              'other_condition': str(other / 'controllers/panel/log.py'),
              'workspace_write': str(workspace / '.sandbox_write_probe'),
              'home_write': str(runtime_home / '.sandbox_write_probe')}
    probe = r'''
import json,os,pathlib,urllib.request
p=json.loads(os.environ['PILOT_BOUNDARY_PROBE'])
out={}
for name in ['target','private','other_condition']:
    try:
        with open(p[name],'rb') as f: f.read(1)
        out[name]=True
    except PermissionError: out[name]=False
for name in ['ground_truth','ancestor']:
    try: os.listdir(p[name]); out[name]=True
    except PermissionError: out[name]=False
for name in ['workspace_write','home_write']:
    try:
        with open(p[name],'xb') as f: f.write(b'probe')
        out[name]=True
    except PermissionError: out[name]=False
with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=5) as r:
    out['ollama']=json.load(r)['version']
print(json.dumps(out))
'''
    import os
    env = os.environ.copy()
    env['PILOT_BOUNDARY_PROBE'] = json.dumps(checks)
    result = subprocess.run(['/usr/bin/sandbox-exec', '-f', str(profile), sys.executable, '-c', probe],
                            cwd=workspace, env=env, capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError(f'OS sandbox verification failed: {result.stderr.strip()}')
    report = json.loads(result.stdout)
    expected = {'target':True,'private':False,'other_condition':False,'ground_truth':False,
                'ancestor':False,'workspace_write':False,'home_write':True}
    if any(report.get(k) != v for k,v in expected.items()):
        raise RuntimeError(f'OS sandbox boundary mismatch: {report}')
    return report


def extract_events(stdout: Path, workspace: Path) -> dict:
    """Extract only observable requests and exact result text; never judge answers."""
    calls = {}; results = []; invalid = 0
    for line_number, line in enumerate(stdout.read_text().splitlines(),1):
        if not line.strip(): continue
        try: event=json.loads(line)
        except json.JSONDecodeError:
            invalid += 1; continue
        if event.get('type') == 'assistant':
            for block in event.get('message',{}).get('content',[]):
                if isinstance(block,dict) and block.get('type')=='tool_use':
                    calls[block.get('id',f'line{line_number}_{len(calls)}')] = {
                        'stdout_line':line_number,'name':block.get('name'), 'input':block.get('input')}
        if event.get('type') == 'result':
            results.append({'stdout_line':line_number,'event':event})
    paths=[]
    for call in calls.values():
        inp=call.get('input')
        if isinstance(inp,dict):
            keys = ['file_path','path','directory','dir_path','include_pattern','include']
            if call['name'] == 'glob':
                keys.append('pattern')
            for key in keys:
                value=inp.get(key)
                if isinstance(value,str):
                    paths.append({'tool':call['name'],'argument':key,'value':value,
                                  'stdout_line':call['stdout_line']})
    answer = next((r for r in reversed(results) if isinstance(r['event'].get('result'),str)),None)
    return {'observable_tool_call_count':len(calls),'tool_calls':list(calls.values()),
            'requested_read_or_search_paths':paths,'result_events':results,
            'non_json_stdout_lines':invalid,'final_result':answer,
            'path_semantics':'Observed tool arguments, not proof of successful reads'}
