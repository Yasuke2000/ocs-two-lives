"""A staff command with secret arguments must stay redacted in both destinations."""
import subprocess
import unittest
from pathlib import Path


class StaffCommandAudit(unittest.TestCase):
    def test_redaction_and_ring(self):
        subprocess.run(["node", str(Path(__file__).with_name("ops_cmdlog.js"))], check=True)
