#!/usr/bin/env python3
"""Normalize preserved Qwen Code and OpenCode pilot traces without scoring them."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JUDGMENT = ("recognition_correct", "decisive_evidence_retrieved", "abstention_correct",
            "final_behavior_correct", "explanation_grounded", "unsupported_claim_present",
            "researcher_notes", "codex_candidate_value", "codex_candidate_evidence", "codex_confidence")
BASE = ("run_id scenario_id harness harness_version model context_length condition start_time end_time runtime_seconds exit_code tool_call_count search_call_count read_call_count files_or_paths_observed raw_verdict_text normalized_verdict normalized_verdict_rule reported_insufficient_evidence raw_log_path final_answer_path retry_of attempt_role utc_runtime_discrepancy_seconds".split())
SEARCH = {"glob", "grep", "grep_search", "list", "list_directory", "list_directory_contents"}
READ = {"read", "read_file"}

class NormalizeError(ValueError): pass

def sha_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink(): raise NormalizeError(f"symlink in raw input: {p}")
        if p.is_file(): out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def safe_child(root: Path, rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts: raise NormalizeError(f"unsafe metadata path: {rel}")
    dest = root / p
    if any(part.is_symlink() for part in [root, *dest.parents, dest] if part.is_relative_to(root)) or not dest.resolve().is_relative_to(root.resolve()): raise NormalizeError(f"unsafe path: {dest}")
    return dest

def text_content(value: Any) -> str:
    if isinstance(value, str): return value
    if isinstance(value, list): return "".join(text_content(x.get("text", "") if isinstance(x, dict) else x) for x in value)
    return ""

def parse_qwen(lines: list[str]) -> tuple[list[dict[str, Any]], str, list[int]]:
    calls: dict[str, dict[str, Any]] = {}; outputs: dict[str, dict[str, Any]] = {}; finals=[]; final_lines=[]
    for n,line in enumerate(lines,1):
        if not line.strip(): continue
        try: ev=json.loads(line)
        except json.JSONDecodeError as exc: raise NormalizeError(f"invalid Qwen JSON at stdout line {n}") from exc
        if not isinstance(ev, dict): raise NormalizeError(f"Qwen event is not an object at stdout line {n}")
        typ=ev.get("type"); msg=ev.get("message",{})
        content=msg.get("content",[]) if isinstance(msg,dict) else []
        if typ=="assistant":
            for part in content if isinstance(content,list) else []:
                if part.get("type")=="tool_use":
                    key=str(part.get("id", f"line{n}")); calls.setdefault(key,{"id":key,"name":part.get("name"),"input":part.get("input",{}),"call_lines":[]})["call_lines"].append(n)
        elif typ=="user":
            for part in content if isinstance(content,list) else []:
                if part.get("type")=="tool_result":
                    key=str(part.get("tool_use_id","")); outputs.setdefault(key,{"result_lines":[],"results":[]})["result_lines"].append(n); outputs[key]["results"].append({"is_error":part.get("is_error"),"content":part.get("content")})
        if ev.get("type")=="result":
            val=ev.get("result")
            if isinstance(val,str): finals.append(val); final_lines.append(n)
    trace=[]
    for k,c in calls.items(): c.update(outputs.get(k,{})); trace.append(c)
    return trace, (finals[-1] if finals else ""), ([final_lines[-1]] if final_lines else [])

def parse_opencode(lines: list[str]) -> tuple[list[dict[str, Any]], str, list[int]]:
    calls: dict[str,dict[str,Any]]={}; messages:dict[str,dict[str,Any]]={}; latest_text_id: str | None=None; latest_text_order=-1; invalid_after_text=-1
    for n,line in enumerate(lines,1):
        if not line.strip(): continue
        try: ev=json.loads(line)
        except json.JSONDecodeError as exc: raise NormalizeError(f"invalid OpenCode JSON at stdout line {n}") from exc
        if not isinstance(ev, dict): raise NormalizeError(f"OpenCode event is not an object at stdout line {n}")
        part=ev.get("part",{}); typ=ev.get("type") or part.get("type")
        if typ=="tool_use" or part.get("type")=="tool":
            invalid_after_text=n
            cid=str(part.get("callID",part.get("id",f"line{n}"))); state=part.get("state",{})
            item=calls.setdefault(cid,{"id":cid,"name":part.get("tool"),"input":state.get("input",{}),"call_lines":[],"updates":[]})
            if isinstance(state.get("input"), dict): item["input"] = state["input"]
            item["call_lines"].append(n); item.setdefault("result_lines",[]).append(n)
            item["updates"].append({"line":n,"status":state.get("status"),"input":state.get("input"),"output":state.get("output"),"error":state.get("error")})
        elif typ in {"step_start", "step_finish"} or part.get("type") in {"step-start", "step-finish"}:
            mid=str(part.get("messageID",ev.get("messageID", "")))
            if latest_text_id and mid and mid!=latest_text_id: invalid_after_text=n
        elif typ=="error":
            invalid_after_text=n
        # A step_finish for the same message closes its text; it does not erase it.
        if typ=="text" and part.get("text"):
            mid=str(part.get("messageID",ev.get("messageID", ""))) or "__unkeyed__"
            if latest_text_id and mid!=latest_text_id:
                messages[mid]={"parts":[],"lines":[]}
            latest_text_id=mid; latest_text_order=n
            bucket=messages.setdefault(mid,{"parts":[],"lines":[]})
            pid=str(part.get("id",f"line{n}"))
            existing = next((p for p in bucket["parts"] if p["id"] == pid), None)
            if existing is not None:
                existing.update(text=text_content(part["text"]), line=n)
            else:
                bucket["parts"].append({"id":pid,"text":text_content(part["text"]),"line":n})
            bucket["lines"].append(n)
    trace=list(calls.values())
    if latest_text_id is None or invalid_after_text>latest_text_order: return trace,"",[]
    bucket=messages[latest_text_id]
    return trace,"\n".join(p["text"] for p in bucket["parts"]),bucket["lines"]

def verdict(text: str) -> tuple[str,str]:
    lines=text.splitlines(); patterns=[(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?verdict(?:\*\*)?\s*[:—-]\s*(.+?)\s*$", "verdict-line"), (r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(VULNERABLE|NOT[_ ]VULNERABLE|INSUFFICIENT[_ ]EVIDENCE)(?:\*\*)?\s*$", "standalone")]
    found=[]
    for line in lines:
        for pat,rule in patterns:
            m=re.match(pat,line,re.I)
            if m:
                value=m.group(1).strip().strip("*").strip(); up=re.sub(r"[_ ]+"," ",value.upper())
                if up in {"NOT VULNERABLE", "NOT VULNERABLE."}: label="NOT_VULNERABLE"
                elif up in {"INSUFFICIENT EVIDENCE", "INSUFFICIENT EVIDENCE."}: label="INSUFFICIENT_EVIDENCE"
                elif up in {"VULNERABLE", "VULNERABLE."}: label="VULNERABLE"
                else: label="UNPARSEABLE"
                found.append((label,rule,line))
    if not found:
        for line in lines:
            if re.match(r"^\s*\*\*Vulnerability Found:\*\*\s*\S",line,re.I) and not re.search(r"\b(no|none|not vulnerable|maybe|possibly|unclear|uncertain|potential|cannot determine)\b",line,re.I): found.append(("VULNERABLE","qwen-vulnerability-found",line))
    labels={x[0] for x in found}
    if not found: return "UNPARSEABLE", ""
    return (next(iter(labels)),found[-1][2]) if len(labels)==1 else ("UNPARSEABLE", found[-1][2])

def verdict_rule(text: str) -> str:
    if verdict(text)[0] == "UNPARSEABLE": return "unparseable-or-conflicted-final"
    if re.search(r"^\s*\*\*Vulnerability Found:\*\*",text,re.I|re.M): return "qwen-vulnerability-found"
    if re.search(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?verdict(?:\*\*)?\s*[:—-]",text,re.I|re.M): return "verdict-line"
    if re.search(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:VULNERABLE|NOT[_ ]VULNERABLE|INSUFFICIENT[_ ]EVIDENCE)(?:\*\*)?\s*$",text,re.I|re.M): return "standalone"
    return "unparseable"

def tool_metrics(trace: list[dict[str,Any]]) -> tuple[int,int,int,list[str]]:
    searches=reads=0; paths=[]
    for t in trace:
        name=str(t.get("name","")).lower(); inp=t.get("input") or {}
        if name in SEARCH: searches+=1
        if name in READ: reads+=1
        for key,val in inp.items() if isinstance(inp,dict) else []:
            if key.lower() in {"path","filepath","file_path","pattern","include","query"} and isinstance(val,(str,int,float)): paths.append(f"requested:{key}={val}")
    return len(trace),searches,reads,sorted(set(paths))

def validate_chain(runs: list[dict[str,Any]], scenario: str) -> dict[str,str]:
    byid={r["meta"].get("run_id"):r for r in runs}
    if len(byid)!=len(runs) or None in byid: raise NormalizeError("missing or duplicate run_id")
    groups:dict[tuple[str,str,str],list[dict[str,Any]]]={}
    for r in runs:
        m=r["meta"]
        rid=m.get("run_id")
        if not isinstance(rid,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*",rid) or rid in {".",".."}:
            raise NormalizeError(f"unsafe run_id: {rid!r}")
        if str(m.get("scenario_id"))!=scenario: raise NormalizeError(f"unexpected scenario attempt {m.get('run_id')}")
        groups.setdefault((m.get("harness",""),m.get("condition",""),str(m.get("scenario_id"))),[]).append(r)
    expected={(h,c,scenario) for h in ("Qwen Code","OpenCode") for c in ("E1","E2","E3")}
    if set(groups)!=expected: raise NormalizeError(f"expected six harness/condition cells; got {sorted(groups)}")
    role={}
    for group,rs in groups.items():
        children:dict[str,list[str]]={}
        for r in rs:
            parent=r["meta"].get("retry_of")
            if parent:
                if parent not in byid: raise NormalizeError(f"missing retry ancestor {parent}")
                p=byid[parent]["meta"]
                if (p.get("harness"),p.get("condition"),str(p.get("scenario_id")))!=group: raise NormalizeError("retry crosses harness/condition/scenario")
                children.setdefault(parent,[]).append(r["meta"]["run_id"])
        if any(len(c)>1 for c in children.values()): raise NormalizeError("retry branch ambiguity")
        roots=[r for r in rs if not r["meta"].get("retry_of")]
        if len(roots)!=1: raise NormalizeError("retry chain must have one root")
        seen=set(); cur=roots[0]["meta"]["run_id"]
        while True:
            if cur in seen: raise NormalizeError("retry cycle")
            seen.add(cur); nxt=children.get(cur,[])
            if not nxt: break
            cur=nxt[0]
        if len(seen)!=len(rs): raise NormalizeError("disconnected retry chain")
        for r in rs: role[r["meta"]["run_id"]]="draft" if r["meta"]["run_id"]==cur else "superseded"
    return role

def load_runs(repo: Path, scenario: str) -> list[dict[str,Any]]:
    raw=repo/"logs/raw"; runs=[]
    if raw.is_symlink() or (repo/"logs").is_symlink(): raise NormalizeError("logs/raw path contains a symlink")
    for mp in sorted(raw.glob("*/**/run_metadata.json")):
        if mp.is_symlink(): raise NormalizeError(f"symlink metadata {mp}")
        base=mp.parent
        if any(x.is_symlink() for x in [base,*base.parents] if x!=repo.parent): raise NormalizeError(f"symlink path in raw run: {base}")
        m=json.loads(mp.read_text())
        if str(m.get("scenario_id"))!=scenario: raise NormalizeError(f"unexpected scenario attempt: {m.get('run_id')} ({m.get('scenario_id')})")
        harness=m.get("harness","").lower()
        if "qwen" in harness: kind="qwen"
        elif "opencode" in harness: kind="opencode"
        else: raise NormalizeError(f"unknown harness {harness}")
        stdout_name=m.get("stdout_file","stdout.txt"); stderr_name=m.get("stderr_file","stderr.txt")
        for name in (stdout_name,stderr_name,"final_answer.txt"):
            if (base/name).exists(): safe_child(base,name)
        stdout=safe_child(base,stdout_name).read_bytes(); stderr=safe_child(base,stderr_name).read_bytes()
        lines=stdout.decode("utf-8",errors="replace").splitlines()
        trace,final,final_lines=(parse_qwen(lines) if kind=="qwen" else parse_opencode(lines))
        f=base/"final_answer.txt"
        source_final=f.read_text() if f.exists() else ""
        if source_final and not final: raise NormalizeError(f"raw final_answer.txt exists but no final text was extracted for {m['run_id']}")
        if f.exists() and final and source_final!=final: raise NormalizeError(f"final_answer.txt differs from extracted final for {m['run_id']}")
        final_bytes=f.read_bytes() if f.exists() else final.encode("utf-8")
        m["_base"]=base; m["_stdout"]=stdout; m["_stderr"]=stderr; m["_final_bytes"]=final_bytes; m["_trace"]=trace; m["_final"]=final; m["_final_lines"]=final_lines; m["_kind"]=kind
        runs.append({"meta":m,"meta_path":mp})
    return runs

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--scenario-id",default="24e78349")
    args=ap.parse_args(); repo=args.repo_root.resolve()
    if not repo.is_dir(): raise NormalizeError("repo root does not exist")
    raw_hash=sha_tree(repo/"logs/raw")
    runs=load_runs(repo,args.scenario_id); roles=validate_chain(runs,args.scenario_id)
    norm=repo/"logs/normalized"; results=repo/"results"
    if any(p.is_symlink() for p in (repo/"logs", repo/"results")): raise NormalizeError("output parent contains a symlink")
    output_files=(results/"pilot_results_draft.csv",results/"pilot_attempts.csv")
    if norm.is_symlink() or (norm.exists() and (not norm.is_dir() or any(norm.iterdir()))) or any(p.exists() or p.is_symlink() for p in output_files): raise NormalizeError("output path already exists or normalized directory is not empty")
    norm_preexisting=norm.exists()
    norm.parent.mkdir(parents=True,exist_ok=True); results.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix=".normalize-",dir=repo/"logs"))
    try:
        snorm=staging/"normalized"; snorm.mkdir(); rows=[]
        for run in sorted(runs,key=lambda x:(x["meta"]["harness"],x["meta"]["condition"],x["meta"]["run_id"])):
            m=run["meta"]; rid=m["run_id"]; d=snorm/rid; d.mkdir()
            for name,data in (("stdout.txt",m["_stdout"]),("stderr.txt",m["_stderr"])): (d/name).write_bytes(data)
            if m["_final"] or m["_final_bytes"]: (d/"final_answer.txt").write_bytes(m["_final_bytes"])
            calls,searches,reads,paths=tool_metrics(m["_trace"])
            label,rawv=verdict(m["_final"])
            start=m.get("start_timestamp_utc",m.get("start_time","")); end=m.get("end_timestamp_utc",m.get("end_time","")); runtime=m.get("wall_clock_seconds",m.get("runtime_seconds",""))
            interval_seconds=None; discrepancy=""
            try:
                if start and end:
                    interval_seconds=round((datetime.fromisoformat(end.replace("Z", "+00:00"))-datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds(),3)
                if interval_seconds is not None and runtime != "": discrepancy=round(interval_seconds-float(runtime),3)
            except (ValueError, TypeError) as exc:
                raise NormalizeError(f"invalid recorded timing for run {rid}") from exc
            answer_path=(Path("logs/normalized")/rid/"final_answer.txt").as_posix() if m["_final"] or m["_final_bytes"] else ""
            rec={k:v for k,v in m.items() if not k.startswith("_")}; rec.update({"attempt_role":roles[rid],"raw_log_path":run["meta_path"].parent.relative_to(repo).as_posix(),"final_answer_path":answer_path,"trace_summary":{"tool_call_count":calls,"search_call_count":searches,"read_call_count":reads,"observed_requests":paths},"normalized_verdict":label,"raw_verdict_text":rawv,"normalized_verdict_rule":verdict_rule(m["_final"])})
            tr={"run_id":rid,"harness":m["harness"],"events":m["_trace"],"final_text_parts":[{"text":m["_final"],"raw_stdout_lines":m["_final_lines"]}] if m["_final"] else [],"final_status":m.get("status"),"final_absent":not bool(m["_final"]),"final_extraction_scope":"Qwen result.result or text parts of the latest OpenCode assistant message; same-message finish preserves text, later tool/error/message events invalidate earlier progress","reported_insufficient_evidence_scope":"literal phrase in extracted final response only, including quoted or negated occurrences; this does not assess correctness","normalized_verdict_rule":verdict_rule(m["_final"]),"recorded_runtime_seconds":runtime,"utc_interval_runtime_seconds":interval_seconds,"runtime_comparison_note":"runtime_seconds copies the runner time.monotonic() interval; UTC minus that interval is retained in CSV, including sleep-related differences."}
            (d/"record.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\n"); (d/"trace.json").write_text(json.dumps(tr,indent=2,ensure_ascii=False)+"\n")
            rows.append({"run_id":rid,"scenario_id":m.get("scenario_id"),"harness":m.get("harness"),"harness_version":m.get("harness_version"),"model":m.get("model"),"context_length":m.get("context_length"),"condition":m.get("condition"),"start_time":start,"end_time":end,"runtime_seconds":runtime,"exit_code":m.get("process_exit_code",m.get("exit_code")),"tool_call_count":calls,"search_call_count":searches,"read_call_count":reads,"files_or_paths_observed":"; ".join(paths),"raw_verdict_text":rawv,"normalized_verdict":label,"normalized_verdict_rule":verdict_rule(m["_final"]),"reported_insufficient_evidence":str(bool(re.search(r"insufficient[ _]evidence",m["_final"],re.I))).lower(),"raw_log_path":rec["raw_log_path"],"final_answer_path":rec["final_answer_path"],"retry_of":m.get("retry_of") or "","attempt_role":roles[rid],"utc_runtime_discrepancy_seconds":discrepancy,**{c:"" for c in JUDGMENT}})
        draft=[r for r in rows if r["attempt_role"]=="draft"]
        if len(draft)!=6 or len({(r["harness"],r["condition"]) for r in draft})!=6: raise NormalizeError("draft selection did not produce six unique cells")
        fields=BASE+list(JUDGMENT)
        for filename,subset in (("pilot_results_draft.csv",draft),("pilot_attempts.csv",rows)):
            with (staging/filename).open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(subset)
        (snorm/"index.json").write_text(json.dumps({"generated_at_utc":datetime.now(timezone.utc).isoformat(),"normalizer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"source_root":str(repo),"scenario_id":args.scenario_id,"all_attempt_run_ids":[r["run_id"] for r in rows],"draft_run_ids":[r["run_id"] for r in draft],"selection_policy":"terminal leaf of validated retry_of chain per harness-condition-scenario; outcome-independent","inclusion_review_status":"REQUIRES RESEARCHER VALIDATION","raw_input_sha256":raw_hash,"attempts_csv":"results/pilot_attempts.csv","draft_csv":"results/pilot_results_draft.csv"},indent=2)+"\n")
        if sha_tree(repo/"logs/raw")!=raw_hash: raise NormalizeError("raw tree changed during normalization")
        if (norm.exists() and any(norm.iterdir())) or any((results/n).exists() for n in ("pilot_results_draft.csv","pilot_attempts.csv")): raise NormalizeError("output appeared during staging")
        # Exclusive destinations cannot overwrite a concurrently created file.
        # On commit failure, retain new partial outputs rather than delete data.
        try:
            norm.mkdir(exist_ok=norm_preexisting)
            for source in sorted(snorm.iterdir()):
                if source.is_dir():
                    target = norm/source.name
                    target.mkdir(exist_ok=False)
                    for artifact in sorted(source.iterdir()):
                        os.link(artifact, target/artifact.name)
            for filename in ("pilot_results_draft.csv", "pilot_attempts.csv"):
                os.link(staging/filename, results/filename)
            os.link(snorm/"index.json", norm/"index.json")
        except OSError as exc:
            raise NormalizeError("exclusive output commit failed; partial new outputs retained for inspection") from exc
        print(f"Normalized {len(rows)} attempts; draft rows: {len(draft)}; raw SHA-256 tree unchanged.")
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except NormalizeError as exc: raise SystemExit(f"normalize_logs: error: {exc}")
