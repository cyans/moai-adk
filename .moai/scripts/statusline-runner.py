#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statusline runner with UTF-8 encoding support for Windows
"""
import os
import sys
import subprocess

# UTF-8 환경 변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows에서 콘솔 코드 페이지를 UTF-8로 설정
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except Exception:
        pass

# moai-adk statusline 실행
try:
    result = subprocess.run(
        ['uv', 'run', 'moai-adk', 'statusline'],
        env=os.environ,
        stdout=sys.stdout,
        stderr=sys.stderr,
        encoding='utf-8',
        errors='replace'
    )
    sys.exit(result.returncode)
except Exception as e:
    print(f"Error running statusline: {e}", file=sys.stderr)
    sys.exit(1)

