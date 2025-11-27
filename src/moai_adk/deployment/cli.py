"""
CLI interface for Windows deployment engine
TAG-CLI-002: CLI interface and user interaction
"""

import asyncio
import os
import sys
import yaml
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import click

from .workflow import DeploymentWorkflow
from .state import DeploymentStatus, DeploymentResult


@dataclass
class CLIConfig:
    """CLI configuration settings"""
    config_file: str = "deploy.yaml"
    verbose: bool = False
    no_confirm: bool = False
    progress_interval: int = 5  # Update progress every N seconds


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if not os.path.exists(config_file):
        raise click.ClickException(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML configuration: {e}")
    except Exception as e:
        raise click.ClickException(f"Error loading configuration: {e}")


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration structure"""
    required_fields = ['project', 'deployment']
    for field in required_fields:
        if field not in config:
            raise click.ClickException(f"Missing required configuration field: {field}")

    # Validate project structure
    project = config['project']
    if not project.get('name'):
        raise click.ClickException("Project name is required")

    # Validate deployment steps
    deployment = config['deployment']
    steps = deployment.get('steps', [])

    # Validate step sequence (should skip step 2)
    expected_steps = [1, 3, 4, 5]
    if not all(step in expected_steps for step in steps):
        raise click.ClickException(
            f"Invalid step sequence. Expected subset of {expected_steps}, got: {steps}"
        )


def get_user_input(prompt: str) -> str:
    """Get user input with Korean language support"""
    while True:
        try:
            user_input = input(prompt).strip()

            # Validate Korean input options
            if user_input in ['진행', '건너뛰기', '중단']:
                return user_input

            # Accept English alternatives for debugging
            if user_input.lower() in ['proceed', 'skip', 'abort']:
                if user_input.lower() == 'proceed':
                    return '진행'
                elif user_input.lower() == 'skip':
                    return '건너뛰기'
                elif user_input.lower() == 'abort':
                    return '중단'

            # Handle invalid input
            print("⚠️ 유효하지 않은 입력입니다. '진행', '건너뛰기', '중단' 중 하나를 선택하세요.")

        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ 사용자에 의해 중단되었습니다.")
            sys.exit(1)
        except Exception as e:
            print(f"⚠️ 입력 오류: {e}")
            continue


async def confirm_deployment(step_description: str, steps_to_skip: List[int]) -> bool:
    """Confirm deployment with user"""
    if steps_to_skip:
        skip_desc = ', '.join(map(str, steps_to_skip))
        prompt = f"단계 {skip_desc} 건너뛰기\n{step_description}\n진행하시겠습니까? (진행/건너뛰기/중단): "
    else:
        prompt = f"{step_description}\n진행하시겠습니까? (진행/건너뛰기/중단): "

    user_input = get_user_input(prompt)

    if user_input == '진행':
        return True
    elif user_input == '건너뛰기':
        return False
    elif user_input == '중단':
        raise click.ClickException("사용자에 의해 배포가 중단되었습니다.")
    else:
        raise click.ClickException("⚠️ 알 수 없는 사용자 입력입니다.")


def display_progress(status: DeploymentStatus, progress: float, message: str = ""):
    """Display deployment progress with Windows-friendly formatting"""
    status_emojis = {
        DeploymentStatus.PENDING: "⏳",
        DeploymentStatus.VALIDATING: "🔍",
        DeploymentStatus.BUILDING: "🏗️",
        DeploymentStatus.TESTING: "🧪",
        DeploymentStatus.DEPLOYING: "🚀",
        DeploymentStatus.COMPLETED: "✅",
        DeploymentStatus.FAILED: "❌",
        DeploymentStatus.ABORTED: "⛔"
    }

    emoji = status_emojis.get(status, "❓")
    progress_percent = int(progress * 100)

    if message:
        click.echo(f"{emoji} [{progress_percent:3d}%] {message}")
    else:
        click.echo(f"{emoji} [{progress_percent:3d}%] {status.value}")


def print_color(text: str, color: str = "green"):
    """Print colored text for Windows compatibility"""
    colors = {
        'red': '🔴',
        'green': '🟢',
        'yellow': '🟡',
        'blue': '🔵',
        'purple': '🟣'
    }

    emoji = colors.get(color, '⚪')
    click.echo(f"{emoji} {text}")


@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', default='deploy.yaml', help='Configuration file path')
@click.pass_context
def main(ctx, verbose, config):
    """MoAI-ADK Windows 배포 엔진 CLI

    Windows 환경을 최적화한 자동 배포 도구입니다.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = CLIConfig(config_file=config, verbose=verbose)


@main.command()
@click.option('--project', '-p', required=True, help='Project name to deploy')
@click.option('--dry-run', is_flag=True, help='Simulate deployment without executing')
@click.option('--skip-steps', multiple=True, type=int, help='Step numbers to skip (e.g., --skip-steps 2)')
@click.pass_context
def deploy(ctx, project, dry_run, skip_steps):
    """배포 프로세스를 실행합니다"""
    config = ctx.obj['config']

    if config.verbose:
        print_color(f"배포 시작: 프로젝트 {project}", "blue")

    try:
        # Load and validate configuration
        config_data = load_config(config.config_file)
        validate_config(config_data)

        # Check if project matches
        if config_data['project']['name'] != project:
            raise click.ClickException(
                f"프로젝트 이름 불일치: 요청 '{project}', 설정 '{config_data['project']['name']}'"
            )

        if dry_run:
            print_color("드라이 럴 모드로 실행합니다.", "yellow")
            print_color(f"프로젝트: {project}", "yellow")
            print_color(f"배포 단계: {config_data['deployment']['steps']}", "yellow")
            print_color(f"건너뛰기 단계: {list(skip_steps) if skip_steps else '없음'}", "yellow")
            return

        # Create and run deployment workflow
        workflow = DeploymentWorkflow.from_config(project, config_data)

        # User confirmation
        if not config.no_confirm:
            with click.progressbar(length=len(workflow.steps), label='사용자 확인') as bar:
                bar.update(0)
                confirmed = confirm_deployment(
                    f"프로젝트 '{project}' 배포를 시작합니다",
                    list(skip_steps)
                )
                bar.update(1)

            if not confirmed:
                print_color("배포가 건너뛰어졌습니다.", "yellow")
                return

        # Execute deployment
        print_color(f"배포 시작: {project}", "green")

        async def run_deployment():
            # Handle step skipping
            steps_to_skip = list(skip_steps) if skip_steps else []

            # Execute workflow
            result = await workflow.execute(steps_to_skip=steps_to_skip)

            if result.success:
                print_color("배포가 성공적으로 완료되었습니다!", "green")
                if config.verbose:
                    click.echo(f"결과: {result.message}")
            else:
                print_color(f"배포 실패: {result.error}", "red")
                if config.verbose:
                    click.echo(f"상세 정보: {result.message}")
                sys.exit(1)

        # Run async deployment
        asyncio.run(run_deployment())

    except click.ClickException as e:
        print_color(f"오류 발생: {e}", "red")
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print_color(f"오류 발생: {e}", "red")
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('config_file', default='deploy.yaml')
def validate(config_file):
    """배포 구성 파일을 검증합니다"""
    try:
        config_data = load_config(config_file)
        validate_config(config_data)
        print_color("구성 파일이 유효합니다.", "green")

        if config.verbose:
            project = config_data['project']
            deployment = config_data['deployment']
            click.echo(f"프로젝트: {project['name']}")
            click.echo(f"버전: {project.get('version', 'N/A')}")
            click.echo(f"배포 단계: {deployment['steps']}")

    except Exception as e:
        print_color(f"구성 파일 검증 실패: {e}", "red")
        sys.exit(1)


@main.command()
def init():
    """샘플 배포 구성 파일을 생성합니다"""
    sample_config = """# MoAI-ADK 배포 구성 파일
# Windows 환경을 최적화한 배포 설정입니다

project:
  name: my-windows-project
  version: 1.0.0
  description: "Windows 환경을 위한 배포 프로젝트"

deployment:
  # 배포 단계: 1=검증, 2=빌드(건너뛰기), 3=테스트, 4=배포, 5=배포
  # step 2(빌드)는 WSL2 환경에서 문제가 있으므로 건너뜁니다
  steps: [1, 3, 4, 5]

  # 단별 실행 명령어 (Windows 환경에 맞게 조정)
  validation_command: "python -m py_compile main.py"
  build_command: "python setup.py build"  # 건너뜁니다
  test_command: "python -m pytest"
  deploy_command: "python deploy.py"

  # Windows 특화 설정
  windows:
    encoding: "utf-8"
    path_handling: "windows"
    wsl2_compatible: true

    # 경로 변환 규칙
    path_mappings:
      "/app/": "C:\\\\app\\\\"
      "/data/": "C:\\\\data\\\\"

    # Windows 환경 변수
    environment:
      PYTHONPATH: "."
      PATH: "%PATH%;C:\\\\Python\\\\Scripts"
"""

    try:
        if os.path.exists('deploy.yaml'):
            if not get_user_input("deploy.yaml 파일이 이미 존재합니다. 덮어쓰시겠습니까? (y/n): ").lower().startswith('y'):
                print_color("작업이 취소되었습니다.", "yellow")
                return

        with open('deploy.yaml', 'w', encoding='utf-8') as f:
            f.write(sample_config)

        print_color("샘플 배포 구성 파일(deploy.yaml)이 생성되었습니다.", "green")
        print_color("파일을 필요에 맞게 수정한 후 'moai deploy' 명령어를 실행하세요.", "blue")

    except Exception as e:
        print_color(f"파일 생성 실패: {e}", "red")
        sys.exit(1)


@main.command()
@click.option('--steps', '-s', multiple=True, type=int, help='특정 단계만 보기')
def list_steps(steps):
    """사용 가능한 배포 단계를 나열합니다"""
    step_descriptions = {
        1: "검증 - 구성 파일 및 환경 검증",
        2: "빌드 - 프로젝트 빌드 (Windows에서 건너뜀)",
        3: "테스트 - 단위 테스트 실행",
        4: "배포 - 프로덕션 환경 배포",
        5: "배포 - 추가 배포 작업"
    }

    print_color("사용 가능한 배포 단계:", "blue")
    for step_num in sorted(step_descriptions.keys()):
        if steps and step_num not in steps:
            continue

        status = ""
        if step_num == 2:
            status = " (기본 건너뜀)"

        click.echo(f"  {step_num}. {step_descriptions[step_num]}{status}")


if __name__ == '__main__':
    main()