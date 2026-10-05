from __future__ import annotations

import importlib.util
import json
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("normalize_logs", ROOT / "scripts/normalize_logs.py")
nl = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(nl)
FIX = ROOT / "tests/fixtures/normalization"


class ParserTests(unittest.TestCase):
    def lines(self, name: str) -> list[str]:
        return (FIX / name).read_text().splitlines()

    def test_qwen_result_precedence_and_denied_request_count(self) -> None:
        trace, final, lines = nl.parse_qwen(self.lines("qwen.jsonl"))
        self.assertEqual(final, "**Vulnerability Found:** vulnerable")
        self.assertEqual(lines, [5])
        self.assertEqual(nl.tool_metrics(trace)[:3], (1, 1, 0))
        self.assertEqual(trace[0]["results"][0]["is_error"], True)

    def test_opencode_updates_deduplicated_and_error_clears_progress(self) -> None:
        trace, final, _ = nl.parse_opencode(self.lines("opencode.jsonl"))
        self.assertEqual(len(trace), 1)
        self.assertEqual(len(trace[0]["updates"]), 2)
        self.assertEqual(final, "")
        self.assertEqual(nl.tool_metrics(trace)[:3], (1, 1, 0))
        trace, final, raw_lines = nl.parse_opencode(self.lines("opencode_final.jsonl"))
        self.assertEqual(final,"## Verdict: **VULNERABLE**")
        self.assertEqual(raw_lines,[1])
        self.assertEqual(nl.verdict(final),("VULNERABLE","## Verdict: **VULNERABLE**"))

    def test_verdict_is_conservative(self) -> None:
        self.assertEqual(nl.verdict("Verdict: NOT VULNERABLE")[0], "NOT_VULNERABLE")
        self.assertEqual(nl.verdict("## Verdict: **VULNERABLE**"),("VULNERABLE","## Verdict: **VULNERABLE**"))
        self.assertEqual(nl.verdict("Verdict: VULNERABLE")[0], "VULNERABLE")
        self.assertEqual(nl.verdict("Verdict: maybe vulnerable")[0], "UNPARSEABLE")
        self.assertEqual(nl.verdict("searched for missing file; insufficient evidence was not established")[0], "UNPARSEABLE")
        self.assertEqual(nl.verdict("Verdict: VULNERABLE\nVerdict: NOT VULNERABLE")[0], "UNPARSEABLE")
        self.assertEqual(nl.verdict("**Vulnerability Found:** No vulnerability can be established")[0],"UNPARSEABLE")
        self.assertEqual(nl.verdict("**Vulnerability Found:** None")[0],"UNPARSEABLE")
        self.assertEqual(nl.verdict_rule("Verdict: VULNERABLE\nVerdict: NOT VULNERABLE"),"unparseable-or-conflicted-final")

    def test_opencode_latest_text_updates_parts_and_final_message(self) -> None:
        events = [
            {"type":"text","part":{"id":"t1","messageID":"m1","text":"Old text"}},
            {"type":"text","part":{"id":"t1","messageID":"m1","text":"Verdict: NOT VULNERABLE"}},
            {"type":"text","part":{"id":"t2","messageID":"m1","text":"Explanation"}},
            {"type":"step_finish","part":{"messageID":"m1","reason":"stop"}},
        ]
        _,final,lines = nl.parse_opencode([json.dumps(e) for e in events])
        self.assertEqual(final,"Verdict: NOT VULNERABLE\nExplanation")
        self.assertEqual(lines,[1,2,3])
        events.append({"type":"step_finish","part":{"messageID":"m2","reason":"stop"}})
        self.assertEqual(nl.parse_opencode([json.dumps(e) for e in events])[1],"")

    def test_opencode_tool_input_from_completed_update(self) -> None:
        events = [
            {"type":"tool_use","part":{"type":"tool","tool":"read","callID":"c1","state":{"status":"pending","input":{}}}},
            {"type":"tool_use","part":{"type":"tool","tool":"read","callID":"c1","state":{"status":"completed","input":{"filePath":"a.py"},"output":"code"}}},
        ]
        trace,_,_ = nl.parse_opencode([json.dumps(e) for e in events])
        self.assertEqual(nl.tool_metrics(trace),(1,0,1,["requested:filePath=a.py"]))

    def test_malformed_json_and_non_object_events_fail(self) -> None:
        for parser in (nl.parse_qwen,nl.parse_opencode):
            for line in ("not JSON", "[]"):
                with self.assertRaises(nl.NormalizeError): parser([line])
            self.assertEqual(parser([]),([],"",[]))

    def test_retry_leaf_selection_and_rejects_missing_ancestor_or_branch(self) -> None:
        runs=[]
        for h in ("Qwen Code", "OpenCode"):
            for c in ("E1", "E2", "E3"):
                rid=("QwenCode-E1-startup" if h=="Qwen Code" and c=="E1" else f"{h.replace(' ','')}-{c}-0"); m={"run_id":rid,"harness":h,"condition":c,"scenario_id":"24e78349","retry_of":None}
                runs.append({"meta":m})
        runs.append({"meta":{"run_id":"retry-mid","harness":"Qwen Code","condition":"E1","scenario_id":"24e78349","retry_of":"QwenCode-E1-startup"}})
        runs.append({"meta":{"run_id":"retry","harness":"Qwen Code","condition":"E1","scenario_id":"24e78349","retry_of":"retry-mid"}})
        roles=nl.validate_chain(runs,"24e78349")
        self.assertEqual(roles["retry"],"draft"); self.assertEqual(roles["QwenCode-E1-startup"],"superseded")
        runs[-1]["meta"]["retry_of"]="absent"
        with self.assertRaises(nl.NormalizeError): nl.validate_chain(runs,"24e78349")
        runs[-1]["meta"]["run_id"]="../escape"
        runs[-1]["meta"]["retry_of"]="QwenCode-E1-startup"
        with self.assertRaises(nl.NormalizeError): nl.validate_chain(runs,"24e78349")
        runs[-1]["meta"]["run_id"]="branch"
        runs[-1]["meta"]["retry_of"]="QwenCode-E1-startup"
        branch={"meta":{"run_id":"branch-2","harness":"Qwen Code","condition":"E1","scenario_id":"24e78349","retry_of":"QwenCode-E1-startup"}}
        with self.assertRaises(nl.NormalizeError): nl.validate_chain(runs+[branch],"24e78349")

    def test_path_traversal_and_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"root"; root.mkdir()
            outside=Path(td)/"outside-normalization-test"; outside.write_text("x")
            with self.assertRaises(nl.NormalizeError): nl.safe_child(root,"../outside-normalization-test")
            (root/"link").symlink_to(outside)
            with self.assertRaises(nl.NormalizeError): nl.safe_child(root,"link")
            with self.assertRaises(nl.NormalizeError): nl.sha_tree(root)
            (root/"real").mkdir(); (root/"real/a.txt").write_text("x")
            (root/"internal").symlink_to(root/"real",target_is_directory=True)
            with self.assertRaises(nl.NormalizeError): nl.safe_child(root,"internal/a.txt")
            outside.unlink()

    def test_cli_copies_attempts_indexes_six_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); (repo/"logs/raw").mkdir(parents=True); (repo/"results").mkdir()
            qwen=(FIX/"qwen.jsonl").read_bytes(); startup=(FIX/"qwen_startup.jsonl").read_bytes(); opencode=(FIX/"opencode.jsonl").read_bytes()
            attempts=[]
            for harness,condition in ((h,c) for h in ("Qwen Code","OpenCode") for c in ("E1","E2","E3")):
                rid=f"{harness.replace(' ','')}-{condition}"; parent=None
                if harness=="Qwen Code" and condition=="E1": parent="QwenCode-E1-startup"
                if harness=="OpenCode" and condition=="E2": parent="OpenCode-E2-original"
                attempts.append((rid,harness,condition,parent))
            attempts.extend([("QwenCode-E1-startup","Qwen Code","E1",None),("OpenCode-E2-original","OpenCode","E2",None)])
            for rid,harness,condition,parent in attempts:
                root="qwen" if harness=="Qwen Code" else "opencode"; run=repo/f"logs/raw/{root}/{rid}"; run.mkdir(parents=True)
                meta={"run_id":rid,"retry_of":parent,"harness":harness,"harness_version":"test","model":"model","context_length":"16384","condition":condition,"scenario_id":"24e78349","start_timestamp_utc":"2026-10-03T00:00:00+00:00","end_timestamp_utc":"2026-10-03T00:00:02+00:00","wall_clock_seconds":2,"process_exit_code":0,"status":"completed"}
                stdout=startup if rid=="QwenCode-E1-startup" else (qwen if root=="qwen" else opencode)
                (run/"stdout.txt").write_bytes(stdout); (run/"stderr.txt").write_bytes(b"stderr\x00\xff")
                (run/"run_metadata.json").write_text(json.dumps(meta))
                if root=="qwen" and rid!="QwenCode-E1-startup": (run/"final_answer.txt").write_bytes(b"**Vulnerability Found:** vulnerable")
            (repo/"logs/normalized").mkdir()
            raw_before={p.relative_to(repo).as_posix():p.read_bytes() for p in (repo/"logs/raw").rglob("*") if p.is_file()}
            cmd=[sys.executable,str(ROOT/"scripts/normalize_logs.py"),"--repo-root",str(repo)]
            done=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(done.returncode,0,done.stderr)
            with (repo/"results/pilot_results_draft.csv").open() as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),6)
            self.assertTrue(all(not row[col] for row in rows for col in nl.JUDGMENT))
            index=json.loads((repo/"logs/normalized/index.json").read_text())
            self.assertEqual(len(index["all_attempt_run_ids"]),8); self.assertEqual(len(index["draft_run_ids"]),6)
            self.assertFalse((repo/"logs/normalized/QwenCode-E1-startup/final_answer.txt").exists())
            with (repo/"results/pilot_attempts.csv").open() as f: all_rows=list(csv.DictReader(f))
            self.assertEqual(len(all_rows),8)
            self.assertTrue(all(not row["final_answer_path"] for row in all_rows if row["run_id"]=="QwenCode-E1-startup"))
            for rel,data in raw_before.items():
                run_id=Path(rel).parent.name; name=Path(rel).name
                if name in {"stdout.txt","stderr.txt","final_answer.txt"}:
                    self.assertEqual((repo/"logs/normalized"/run_id/name).read_bytes(),data)
            original=(repo/"results/pilot_results_draft.csv").read_bytes()
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)
            self.assertEqual((repo/"results/pilot_results_draft.csv").read_bytes(),original)
            self.assertEqual({p.relative_to(repo).as_posix():p.read_bytes() for p in (repo/"logs/raw").rglob("*") if p.is_file()},raw_before)


if __name__ == "__main__":
    unittest.main()
