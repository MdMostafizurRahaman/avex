import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from opencode_pilot import runtime_configuration,command_for_run,MODEL_SELECTOR
from run_pilot import ENDPOINT

class OpenCodeAdapterTests(unittest.TestCase):
    def test_fresh_command_without_performance_flags(self):
        command=command_for_run('/opt/homebrew/bin/opencode','literal task',43210)
        self.assertEqual(command[-2:],['--','literal task'])
        self.assertIn(MODEL_SELECTOR,command)
        for flag in ['--session','--continue','--fork','--attach','--variant','--auto']:
            self.assertNotIn(flag,command)
    def test_model_endpoint_and_read_only_permissions(self):
        config=runtime_configuration()
        self.assertEqual(config['model'],MODEL_SELECTOR)
        self.assertEqual(config['small_model'],MODEL_SELECTOR)
        self.assertEqual(config['enabled_providers'],['ollama'])
        self.assertEqual(config['provider']['ollama']['options'],{'baseURL':ENDPOINT})
        self.assertEqual(config['permission']['*'],'deny')
        for name in ['read','glob','grep','list']:
            self.assertEqual(config['permission'][name],'allow')
        self.assertNotIn('limit',config['provider']['ollama']['models']['qwen3.5:9b-q4_K_M'])

if __name__=='__main__':unittest.main()
