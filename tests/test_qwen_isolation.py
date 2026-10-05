import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('qwen_isolation',Path(__file__).resolve().parents[1]/'scripts/qwen_isolation.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class IsolationTests(unittest.TestCase):
    def test_reject_overlap_and_noncanonical_paths(self):
        for home in [Path('/a'),Path('/a/home')]:
            with self.assertRaises(ValueError): m.sandbox_profile(Path('/a'),home,Path('/b'))
        with self.assertRaises(ValueError): m.sandbox_profile(Path('/a/../a'),Path('/b'),Path('/c'))
    def test_profile_denies_user_data_and_workspace_writes(self):
        profile=m.sandbox_profile(Path('/condition'),Path('/runtime'),Path('/node'))
        self.assertIn('(deny file-read* (subpath "/Users")',profile)
        self.assertIn('(deny file-write*)',profile)
        self.assertNotIn('(allow file-write* (subpath "/condition")',profile)
        self.assertNotIn('(subpath "/")',profile)
        self.assertIn('localhost:11434',profile)
    def test_extract_observed_tool_calls_and_exact_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'stdout'; answer='Unmodified\nanswer'
            events=[{'type':'assistant','message':{'content':[{'type':'tool_use','id':'1','name':'read_file','input':{'file_path':'/condition/a'}}]}}, {'type':'assistant','message':{'content':[{'type':'tool_use','id':'2','name':'glob','input':{'pattern':'**/*.py'}}]}}, {'type':'result','result':answer}]
            p.write_text('\n'.join(json.dumps(e) for e in events))
            d=m.extract_events(p,Path('/condition'))
            self.assertEqual(d['observable_tool_call_count'],2)
            self.assertEqual(d['requested_read_or_search_paths'][1]['value'],'**/*.py')
            self.assertEqual(d['requested_read_or_search_paths'][0]['value'],'/condition/a')
            self.assertEqual(d['final_result']['event']['result'],answer)

if __name__=='__main__': unittest.main()
