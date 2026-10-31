import subprocess
import sys
import unittest
import contextlib
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from security_lab.starter import docker, start


class StarterProcessTests(unittest.TestCase):
    def test_partial_setup_failure_preserves_network_cleanup_reference(self):
        def failed_setup(*args, **options):
            if args[0] == 'info':
                return '{"OSType":"linux"}'
            if args[:2] == ('image', 'inspect'):
                return '[{}]'
            if args[:2] == ('network', 'create'):
                return 'owned-network-id'
            if args[0] == 'create':
                raise RuntimeError('injected create failure')
            if args[:2] == ('network', 'rm'):
                self.assertEqual(args[2], 'owned-network-id')
                raise RuntimeError('injected cleanup failure')
            return ''
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'run'
            with patch('security_lab.starter.docker', side_effect=failed_setup), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'injected create failure'):
                    start(output)
            result = json.loads((output/'result.json').read_text(encoding='utf-8'))
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['owned_network_id'], 'owned-network-id')
            self.assertNotIn('owned_container_id', result)
            self.assertIn('network cleanup failed; inspect recorded ID', result['cleanup'])

    def test_utf8_output_and_progress_survive_windows_locale(self):
        # Run a real child with Unicode on both streams, substituting only the
        # executable so this regression does not require a running Docker engine.
        real_run = subprocess.run
        program = ("import sys; "
                   "sys.stdout.buffer.write(bytes.fromhex('636166c3a90a')); "
                   "sys.stderr.buffer.write(bytes.fromhex('e28f8f20e29688'))")
        def child(_command, **options):
            return real_run([sys.executable, "-c", program], **options)
        with patch("security_lab.starter.subprocess.run", side_effect=child):
            self.assertEqual(docker("version"), "caf\u00e9")


if __name__ == "__main__":
    unittest.main()
