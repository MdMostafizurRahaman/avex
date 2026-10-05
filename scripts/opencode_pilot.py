"""OpenCode adapter using the existing pilot prompt and preflight helpers."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import run_pilot as shared
from qwen_isolation import sandbox_profile, verify_sandbox
from opencode_events import extract_events

VERSION = '1.18.30'
MODEL_SELECTOR = 'ollama/' + shared.MODEL


def runtime_configuration() -> dict[str, Any]:
    """Bind the locked model; set isolation permissions without performance tuning."""
    return {
        'model': MODEL_SELECTOR,
        'small_model': MODEL_SELECTOR,
        'enabled_providers': ['ollama'],
        'provider': {'ollama': {
            'npm': '@ai-sdk/openai-compatible', 'name': 'Ollama',
            'options': {'baseURL': shared.ENDPOINT},
            'models': {shared.MODEL: {'name': shared.MODEL}},
        }},
        'permission': {'*': 'deny', 'read': 'allow', 'glob': 'allow',
                       'grep': 'allow', 'list': 'allow'},
    }


def command_for_run(binary: str, prompt: str, port: int) -> list[str]:
    """Installed CLI flags; no resume, continue, attach or performance options."""
    return [binary, '--pure', 'run', '--model', MODEL_SELECTOR,
            '--format', 'json', '--port', str(port), '--', prompt]


def run_opencode(args: argparse.Namespace, root: Path) -> int:
    if bool(args.retry_of) != bool(args.infrastructure_reason):
        raise shared.PreflightError('Retry ID and infrastructure reason must be supplied together')
    workspace = root / 'pilot/conditions' / args.condition
    run_id = str(uuid.uuid4())
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = root / 'logs/raw/opencode' / f'{stamp}_{args.condition}_{run_id}'
    output.mkdir(parents=True, exist_ok=False)
    for name in ['stdout.txt', 'stderr.txt']:
        (output/name).open('xb').close()
    start = time.monotonic()
    metadata: dict[str, Any] = {
        'run_id':run_id, 'harness':'OpenCode', 'harness_version':None,
        'model':shared.MODEL, 'model_selector':MODEL_SELECTOR,
        'model_endpoint':shared.ENDPOINT, 'context_length':shared.CONTEXT_LENGTH,
        'condition':args.condition, 'scenario_id':args.scenario_id,
        'working_directory':str(workspace), 'actual_working_directory':str(workspace),
        'start_timestamp_utc':shared.utc_now(), 'end_timestamp_utc':None,
        'wall_clock_seconds':None, 'process_exit_code':None, 'status':'preflight',
        'retry_of':args.retry_of, 'infrastructure_retry_reason':args.infrastructure_reason,
        'observable_tool_calls':None, 'searched_or_read_paths':None,
        'final_answer_location':None, 'prompt_file':'prompt_used.txt',
        'stdout_file':'stdout.txt', 'stderr_file':'stderr.txt', 'command':None,
    }
    def finish(status: str, exit_code: int | None, error: str | None = None) -> int:
        metadata.update(status=status, process_exit_code=exit_code,
                        end_timestamp_utc=shared.utc_now(),
                        wall_clock_seconds=round(time.monotonic()-start,6),
                        infrastructure_error=error)
        shared.write_json(output/'run_metadata.json',metadata)
        print(f'Run {run_id} {args.condition}: {status}, exit {exit_code}; logs {output}',flush=True)
        return 0 if status=='completed' and exit_code==0 else 1
    try:
        if not workspace.is_dir(): raise shared.PreflightError('Condition workspace missing')
        for p in (workspace,*workspace.parents):
            if p.is_symlink(): raise shared.PreflightError(f'Symlink ancestry: {p}')
        before = shared.workspace_hashes(workspace)
        manifest = shared.read_json(root/'results/manifests'/f'{args.condition}_manifest.json')
        if before != {f['path']:f['sha256'] for f in manifest['files']}:
            raise shared.PreflightError('Condition differs from approved file hashes')
        scenario = shared.check_scenario(root,args.scenario_id)
        prompt = shared.construct_prompt(root,args.condition,scenario)
        (output/'prompt_used.txt').write_text(prompt,encoding='utf-8')
        metadata['prompt_sha256']=hashlib.sha256(prompt.encode()).hexdigest()
        metadata['workspace_sha256_before']=before
        metadata['leakage_check']=shared.check_leakage(root,workspace,output)
        binary=shutil.which('opencode')
        if not binary: raise shared.PreflightError('OpenCode binary not found')
        version=shared.command_output([binary,'--version'])
        if version.returncode or version.stdout.strip()!=VERSION:
            raise shared.PreflightError(f'OpenCode version differs from locked {VERSION}')
        metadata['harness_version']=VERSION
        metadata['ollama_server_version']=shared.query_ollama_version()
        ollama=shutil.which('ollama')
        if not ollama: raise shared.PreflightError('Ollama client missing')
        client=shared.command_output([ollama,'--version'])
        import re
        v=re.search(r'\d+\.\d+\.\d+',client.stdout+'\n'+client.stderr)
        if not v: raise shared.PreflightError('Cannot extract Ollama client version')
        metadata['ollama_client_version']=v.group(0)
        metadata['ollama_server_context']=shared.verify_server_context()
        home=Path(tempfile.mkdtemp(prefix='pilot_opencode_runtime_')).resolve()
        for name in ['config/opencode','data','cache','state','tmp']:
            (home/name).mkdir(parents=True,exist_ok=True)
        config=runtime_configuration()
        config_path=home/'config/opencode/opencode.json'
        shared.write_json(config_path,config)
        metadata['runtime_home']=str(home)
        metadata['runtime_config_sha256']=hashlib.sha256(config_path.read_bytes()).hexdigest()
        metadata['runtime_config']=config
        # Reserve an ephemeral loopback port, equivalent to the CLI default port
        # allocation, so the sandbox can authorize only this local control server.
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        metadata['local_control_port']=port
        runtime_root=Path(binary).resolve().parent.parent
        profile=output/'sandbox.sb'
        rules=sandbox_profile(workspace.resolve(),home,runtime_root)
        rules += f'(allow network-inbound (local ip "localhost:{port}"))\n'
        rules += f'(allow network-outbound (remote ip "localhost:{port}"))\n'
        profile.write_text(rules)
        metadata['sandbox_verification']=verify_sandbox(profile,workspace,home,root)
        env={'PATH':os.environ['PATH'],'HOME':str(home),'TMPDIR':str(home/'tmp'),
             'XDG_CONFIG_HOME':str(home/'config'),'XDG_DATA_HOME':str(home/'data'),
             'XDG_CACHE_HOME':str(home/'cache'),'XDG_STATE_HOME':str(home/'state'),
             'OLLAMA_CONTEXT_LENGTH':shared.CONTEXT_LENGTH,'NO_COLOR':'1',
             'TERM':'dumb','LANG':'en_US.UTF-8'}
        prefix=['/usr/bin/sandbox-exec','-f',str(profile)]
        debug=subprocess.run(prefix+[binary,'--pure','debug','config'],cwd=workspace,
                             env=env,capture_output=True,text=True,timeout=30)
        (output/'resolved_config.stdout.json').write_text(debug.stdout)
        (output/'resolved_config.stderr.txt').write_text(debug.stderr)
        if debug.returncode: raise shared.PreflightError('Confined OpenCode configuration check failed')
        resolved=json.loads(debug.stdout)
        if resolved.get('model')!=MODEL_SELECTOR or resolved.get('small_model')!=MODEL_SELECTOR:
            raise shared.PreflightError('Resolved OpenCode models differ from required model')
        if resolved.get('provider',{}).get('ollama',{}).get('options',{}).get('baseURL')!=shared.ENDPOINT:
            raise shared.PreflightError('Resolved OpenCode endpoint differs')
        if resolved.get('permission')!=config['permission']:
            raise shared.PreflightError('Resolved permissions differ')
        command=prefix+command_for_run(binary,prompt,port)
        metadata['command']=['<PROMPT_TEXT_IN_prompt_used.txt>' if x==prompt else x for x in command]
        metadata.update(status='running',start_timestamp_utc=shared.utc_now())
        start=time.monotonic()
        shared.write_json(output/'run_metadata.json',metadata)
        with (output/'stdout.txt').open('wb') as stdout,(output/'stderr.txt').open('wb') as stderr:
            process=subprocess.run(command,cwd=workspace,env=env,stdin=subprocess.DEVNULL,
                                   stdout=stdout,stderr=stderr,check=False)
        observed=extract_events((output/'stdout.txt').read_text())
        shared.write_json(output/'observable_events.json',observed)
        metadata['observable_tool_calls']=observed['tool_call_count']
        metadata['searched_or_read_paths']=observed['requested_read_or_search_paths']
        metadata['actual_session_ids']=observed['session_ids']
        metadata['tool_call_extraction']='Unique recorded tool callIDs in raw OpenCode JSON events; includes failed/denied requests'
        parts=observed['final_text_parts']
        if parts:
            (output/'final_answer.txt').write_text('\n'.join(x['text'] for x in parts))
            metadata['final_answer_location']={'raw_stdout_lines':[x['stdout_line'] for x in parts],
                                                'verbatim_text_parts_file':'final_answer.txt'}
        metadata['workspace_sha256_after']=shared.workspace_hashes(workspace)
        metadata['workspace_unchanged']=metadata['workspace_sha256_after']==before
        if not metadata['workspace_unchanged']:
            return finish('infrastructure_error',process.returncode,'Condition changed during run')
        return finish('completed',process.returncode)
    except (shared.PreflightError,OSError,RuntimeError,subprocess.TimeoutExpired,json.JSONDecodeError) as exc:
        (output/'infrastructure_error.txt').write_text(str(exc)+'\n')
        return finish('infrastructure_error',None,str(exc))
