"""
Test runner script for Gemini AI Chat Application.
Executes all test cases in tests/ and reports structured test summary.
"""

import os
import sys
import unittest
import time

# Ensure project root and backend are in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)


def run_all_tests():
    print("=" * 70)
    print(" Gemini AI Chat Application - Automated Test Suite")
    print("=" * 70)
    print(f"Project Directory : {PROJECT_ROOT}")
    print(f"Backend Directory : {BACKEND_DIR}")
    print(f"Tests Directory   : {TESTS_DIR}")
    print("-" * 70)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=TESTS_DIR, pattern="test_*.py")

    total_tests = suite.countTestCases()
    print(f"Discovered {total_tests} test cases across test modules.\n")

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n" + "=" * 70)
    print(" TEST EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total Tests Run : {result.testsRun}")
    print(f"Successes       : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures        : {len(result.failures)}")
    print(f"Errors          : {len(result.errors)}")
    print(f"Skipped         : {len(result.skipped)}")
    print(f"Duration        : {duration:.3f} seconds")
    print("=" * 70)

    if result.wasSuccessful():
        print(">>> ALL TESTS PASSED SUCCESSFULLY! <<<\n")
        return 0
    else:
        print(">>> SOME TESTS FAILED! <<<\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
