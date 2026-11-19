"""Test tiers for the offline unit tests.

`python -I -m unittest discover -s tests` runs everything (~4 minutes). tools/test_fast.sh sets TTL_FAST_TESTS=1, and
then the tests marked @heavy skip: they read the big canon structures (tempest, dwargon, every build's footprint),
which is where nearly all of the time goes. Mark a test heavy when it takes more than a second or two.
"""
import os
import unittest

FAST = os.environ.get("TTL_FAST_TESTS") == "1"


def heavy(why: str):
    return unittest.skipIf(FAST, f"heavy ({why}): full suite only")
