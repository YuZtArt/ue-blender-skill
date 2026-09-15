import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'skills/ue-blender/scripts/mcp_cli.py'
FIXTURE = Path(__file__).with_name('fake_server.py')
spec = importlib.util.spec_from_file_location('mcp_cli', CLI)
cli = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cli
spec.loader.exec_module(cli)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {**os.environ, 'CODEX_HOME': str(self.root / 'codex')}
        self.config = self.root / 'fixture.json'
        self.config.write_text(json.dumps({'mcpServers': {'blender': {
            'command': sys.executable, 'args': [str(FIXTURE)]}}}), encoding='utf-8')

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, str(CLI), *args, '--config', str(self.config)],
                                cwd=self.root, env=self.env, text=True, capture_output=True, timeout=15)
        return result.returncode, json.loads(result.stdout)

    def test_single_host_doctor(self):
        code, payload = self.run_cli('doctor', '--server', 'blender')
        self.assertEqual(code, 0)
        self.assertTrue(payload['ok'])
        self.assertEqual(self.run_cli('doctor')[0], 2)

    def test_preflight_and_schema(self):
        self.assertEqual(self.run_cli('preflight', 'blender')[0], 0)
        code, payload = self.run_cli('schema', 'blender', 'echo')
        self.assertEqual(code, 0)
        self.assertEqual(payload['tool']['name'], 'echo')

    def test_prompt_and_json_file(self):
        args_path = self.root / 'args.json'
        args_path.write_text(json.dumps({'value': 'quoted "value"'}), encoding='utf-8')
        code, payload = self.run_cli('call', 'blender', 'echo', '--intent', 'read',
                                     '--args-file', str(args_path), '--user-prompt', 'Original request')
        self.assertEqual(code, 0)
        args = json.loads(payload['result']['content'][0]['text'])
        self.assertEqual(args, {'value': 'quoted "value"', 'user_prompt': 'Original request'})

    def test_tool_error_is_failure(self):
        code, payload = self.run_cli('blender', 'fail', '--intent', 'write')
        self.assertEqual(code, 2)
        self.assertFalse(payload['ok'])
        self.assertEqual(payload['outcome'], 'unknown')

    def test_lost_write_response(self):
        code, payload = self.run_cli('blender', 'drop', '--intent', 'write')
        self.assertEqual(code, 2)
        self.assertEqual(payload['outcome'], 'unknown')

    def test_timeout_intent(self):
        for intent, expected, outcome in [('read', 3, 'not_observed'), ('write', 4, 'unknown')]:
            with self.subTest(intent=intent):
                code, payload = self.run_cli('blender', 'slow', '--intent', intent, '--timeout', '0.2')
                self.assertEqual(code, expected)
                self.assertEqual(payload['outcome'], outcome)

    def test_binary_materialization(self):
        output = self.root / 'captures'
        code, payload = self.run_cli('blender', 'image', '--intent', 'read', '--output-dir', str(output))
        self.assertEqual(code, 0)
        block = payload['result']['content'][0]
        self.assertNotIn('data', block)
        self.assertEqual(Path(block['saved_file']).read_bytes(), b'fixture-image-bytes')

    def test_config_precedence(self):
        codex_dir = self.root / 'codex'
        codex_dir.mkdir()
        (codex_dir / 'config.toml').write_text('[mcp_servers.blender]\ncommand = "global"\n', encoding='utf-8')
        project = self.root / 'project'
        project.mkdir()
        (project / '.mcp.json').write_text(json.dumps({'mcpServers': {'blender': {'command': 'project'}}}), encoding='utf-8')
        with patch.dict(os.environ, {'CODEX_HOME': str(codex_dir)}), patch.object(cli.Path, 'cwd', return_value=project):
            servers, found = cli.load_servers()
            self.assertEqual(servers['blender'].command, 'project')
            self.assertEqual(found, project / '.mcp.json')
            servers, _ = cli.load_servers(str(self.config))
            self.assertEqual(servers['blender'].command, sys.executable)


if __name__ == '__main__':
    unittest.main()
