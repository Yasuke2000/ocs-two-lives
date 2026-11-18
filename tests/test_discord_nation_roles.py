"""Exercise the Discord reconciliation against an in-memory guild, without a bot or a network."""
import subprocess
import unittest
from pathlib import Path


class NationRoles(unittest.TestCase):
    def test_reconcile(self):
        subprocess.run(["node", str(Path(__file__).with_name("discord_nation_roles.js"))], check=True)
