#!/usr/bin/env python3
"""
Setup Command Test Main

TAG-WIN-004: Setup Command 실제 동작 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from moai_adk.platform.setup_command import SetupCommand

def test_setup_command():
    """SetupCommand 실제 동작 테스트"""
    print("=== MoAI-ADK Setup Command 테스트 ===")

    # SetupCommand 생성 및 기본 테스트
    setup_cmd = SetupCommand()
    print("[OK] SetupCommand 생성 완료")

    # OS 감지 테스트
    os_type = setup_cmd.get_detected_os()
    print(f"[OK] 감지된 OS: {os_type}")

    # 플랫폼 지원 여부
    is_supported = setup_cmd.is_platform_supported()
    print(f"[OK] 플랫폼 지원 여부: {is_supported}")

    # 설정 요약
    summary = setup_cmd.get_setup_summary()
    print(f"[OK] 설정 요약 - 플랫폼: {summary['platform']}, 상태: {summary['status']}")
    print(f"     MCP 서버: {summary['configs']['mcp_servers']}")

    # 도움말
    print("\n[INFO] 도움말 일부:")
    help_text = setup_cmd.get_help()
    print(help_text[:200] + '...')

    print("\n=== 테스트 완료 ===")
    return True

if __name__ == "__main__":
    test_setup_command()