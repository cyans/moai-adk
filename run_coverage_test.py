#!/usr/bin/env python3
"""
Coverage test runner for MoAI-ADK Windows Optimizations

This script runs all tests and generates coverage reports for the Windows optimization components.
"""

import sys
import os
import coverage
import unittest

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_coverage_tests():
    """Run tests with coverage reporting"""
    # Initialize coverage
    cov = coverage.Coverage(
        branch=True,
        source=['moai_adk'],
        omit=['*/tests/*', '*/test_*', '*/__pycache__/*']
    )
    cov.start()

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Stop coverage and generate report
    cov.stop()
    cov.save()

    # Generate coverage report
    print("\n" + "="*80)
    print("COVERAGE REPORT")
    print("="*80)

    # Terminal report
    cov.report(show_missing=True)

    # HTML report
    cov.html_report(directory='coverage_html')
    print(f"\nDetailed HTML coverage report generated in: coverage_html/index.html")

    # Return test results
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_coverage_tests()
    sys.exit(0 if success else 1)