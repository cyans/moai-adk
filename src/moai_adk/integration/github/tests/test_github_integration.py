"""
Test suite for GitHub Actions integration.
TAG-CI-004: GitHub Actions integration
"""

import pytest
import os
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

# Import the GitHub integration modules to be tested
from moai_adk.integration.github.workflow_generator import GitHubWorkflowGenerator
from moai_adk.integration.github.deploy_action import MoAIDeployAction
from moai_adk.integration.github.secrets_manager import GitHubSecretsManager
from moai_adk.integration.github.branch_protection import GitHubBranchProtection
from moai_adk.integration.github.pr_handler import GitHubPRHandler
from moai_adk.integration.github.event_handler import GitHubEventHandler
from moai_adk.integration.github.api_client import GitHubAPIClient
from moai_adk.integration.github.errors import GitHubError, WorkflowError, APIError


class TestGitHubWorkflowGenerator:
    """Test cases for GitHubWorkflowGenerator class"""

    def test_workflow_generator_initialization(self):
        """Test GitHubWorkflowGenerator initialization"""
        generator = GitHubWorkflowGenerator()

        assert generator.owner is None
        assert generator.repo is None
        assert generator.branch == "main"
        assert generator.windows_compatible is True

    def test_set_repository_info(self):
        """Test setting repository information"""
        generator = GitHubWorkflowGenerator()

        generator.set_repository("owner", "repo-name", "develop")

        assert generator.owner == "owner"
        assert generator.repo == "repo-name"
        assert generator.branch == "develop"

    def test_generate_deployment_workflow(self):
        """Test generating deployment workflow"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_deployment_workflow(
            name="Windows Deployment",
            on=["push", "pull_request"],
            steps_config=[
                {
                    "name": "Setup Environment",
                    "uses": "actions/setup-python@v4",
                    "with": {"python-version": "3.11"}
                },
                {
                    "name": "Run Deployment",
                    "uses": "./.github/actions/moai-deploy@v1",
                    "env": {"ENVIRONMENT": "production"}
                }
            ]
        )

        assert "name" in workflow
        assert "on" in workflow
        assert "jobs" in workflow
        assert workflow["name"] == "Windows Deployment"
        assert "push" in workflow["on"]
        assert "pull_request" in workflow["on"]

    def test_generate_windows_specific_workflow(self):
        """Test generating Windows-specific workflow"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_windows_workflow(
            name="Windows Build",
            os=["windows-latest"],
            steps=[
                {"run": "echo 'Running on Windows'"},
                {"run": "powershell -Command \"Get-Process\""}
            ]
        )

        assert workflow["runs-on"] == ["windows-latest"]
        assert len(workflow["jobs"]) > 0

        # Verify Windows-specific steps
        steps = workflow["jobs"]["build"]["steps"]
        assert any("powershell" in step.get("run", "").lower() for step in steps)

    def test_generate_workflow_with_matrix(self):
        """Test generating workflow with matrix strategy"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_matrix_workflow(
            name="Multi-Platform Deployment",
            matrix={
                "os": ["ubuntu-latest", "windows-latest"],
                "python": ["3.11", "3.12"]
            },
            steps=[
                {"run": "python --version"}
            ]
        )

        assert strategy := workflow["jobs"]["deploy"]["strategy"]
        assert "matrix" in strategy
        assert "os" in strategy["matrix"]
        assert "python" in strategy["matrix"]
        assert len(strategy["matrix"]["os"]) == 2
        assert len(strategy["matrix"]["python"]) == 2

    def test_generate_secrets_workflow(self):
        """Test generating workflow with secrets"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_deployment_workflow(
            name="Secret Deployment",
            secrets=["API_KEY", "DATABASE_URL"],
            steps_config=[
                {
                    "name": "Deploy with Secrets",
                    "run": "echo ${{ secrets.API_KEY }}"
                }
            ]
        )

        job_steps = workflow["jobs"]["deploy"]["steps"]
        # Should add environment setup for secrets
        assert len(job_steps) > 0

    def test_generate_workflow_with_artifacts(self):
        """Test generating workflow with artifacts"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_workflow_with_artifacts(
            name="Build and Deploy",
            artifacts=["build_output", "test_results"],
            steps=[
                {
                    "name": "Upload Artifacts",
                    "uses": "actions/upload-artifact@v3",
                    "with": {
                        "name": "build_output",
                        "path": "dist/"
                    }
                }
            ]
        )

        assert "jobs" in workflow
        job_steps = workflow["jobs"]["build"]["steps"]
        assert any("actions/upload-artifact" in step.get("uses", "") for step in job_steps)

    def test_validate_workflow_structure(self):
        """Test workflow structure validation"""
        generator = GitHubWorkflowGenerator()

        valid_workflow = {
            "name": "Test Workflow",
            "on": ["push"],
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"run": "echo test"}]
                }
            }
        }

        assert generator.validate_workflow(valid_workflow) is True

        invalid_workflow = {
            "name": "Invalid Workflow",
            "on": ["push"]
            # Missing jobs
        }

        assert generator.validate_workflow(invalid_workflow) is False

    def test_save_workflow_file(self):
        """Test saving workflow to file"""
        generator = GitHubWorkflowGenerator()

        workflow = {
            "name": "Test Workflow",
            "on": ["push"],
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"run": "echo test"}]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name

        try:
            generator.save_workflow(workflow, temp_path)

            # Verify file was created and contains correct content
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_content = yaml.safe_load(f)

            assert saved_content == workflow

        finally:
            os.unlink(temp_path)

    def test_generate_conditional_workflow(self):
        """Test generating workflow with conditions"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_conditional_workflow(
            name="Conditional Deployment",
            condition="github.ref == 'refs/heads/main'",
            steps=[
                {
                    "name": "Deploy",
                    "if": "github.ref == 'refs/heads/main'",
                    "run": "echo 'Deploying to production'"
                }
            ]
        )

        job_steps = workflow["jobs"]["deploy"]["steps"]
        assert "if" in job_steps[0]

    def test_workflow_template_engineering(self):
        """Test workflow template generation for engineering workflows"""
        generator = GitHubWorkflowGenerator()
        generator.set_repository("owner", "repo-name", "main")

        workflow = generator.generate_engineering_workflow(
            name="Engineering Pipeline",
            stages=["lint", "test", "security", "build", "deploy"],
            quality_gates=True
        )

        assert workflow["name"] == "Engineering Pipeline"
        assert "lint" in workflow["jobs"]
        assert "test" in workflow["jobs"]
        assert "security" in workflow["jobs"]
        assert "build" in workflow["jobs"]
        assert "deploy" in workflow["jobs"]

        # Verify dependencies between stages
        assert workflow["jobs"]["test"]["needs"] == ["lint"]
        assert workflow["jobs"]["security"]["needs"] == ["test"]
        assert workflow["jobs"]["build"]["needs"] == ["security"]
        assert workflow["jobs"]["deploy"]["needs"] == ["build"]


class TestMoAIDeployAction:
    """Test cases for MoAIDeployAction class"""

    def test_deploy_action_initialization(self):
        """Test MoAIDeployAction initialization"""
        action = MoAIDeployAction()

        assert action.name == "moai-deploy"
        assert action.version == "v1"
        assert action.supported_platforms == ["windows-latest", "ubuntu-latest"]

    def test_generate_action_manifest(self):
        """Test generating action manifest"""
        action = MoAIDeployAction()

        manifest = action.generate_manifest(
            name="moai-deploy",
            description="MoAI ADK Deployment Action",
            inputs={
                "config-file": {"description": "Configuration file path"},
                "environment": {"description": "Target environment"}
            },
            outputs={
                "deployment-status": {"description": "Deployment status"}
            }
        )

        assert manifest["name"] == "moai-deploy"
        assert manifest["description"] == "MoAI ADK Deployment Action"
        assert "inputs" in manifest
        assert "outputs" in manifest
        assert "runs" in manifest

    def test_generate_action_dockerfile(self):
        """Test generating action Dockerfile"""
        action = MoAIDeployAction()

        dockerfile = action.generate_dockerfile(
            base_image="python:3.11-slim",
            install_commands=["pip install moai-adk"],
            entrypoint=["python", "/action/deploy.py"]
        )

        assert "FROM python:3.11-slim" in dockerfile
        assert "pip install moai-adk" in dockerfile
        assert "ENTRYPOINT" in dockerfile

    def test_generate_action_script(self):
        """Test generating action entrypoint script"""
        action = MoAIDeployAction()

        script = action.generate_action_script(
            main_command="moai deploy",
            support_config_validation=True,
            support_windows=True
        )

        assert "moai deploy" in script
        assert "config validation" in script.lower()
        assert "windows" in script.lower()

    def test_create_action_directory(self):
        """Test creating action directory structure"""
        action = MoAIDeployAction()

        with tempfile.TemporaryDirectory() as temp_dir:
            action.create_action_structure(temp_dir)

            # Verify directory structure
            assert os.path.exists(os.path.join(temp_dir, "action.yml"))
            assert os.path.exists(os.path.join(temp_dir, "Dockerfile"))
            assert os.path.exists(os.path.join(temp_dir, "deploy.py"))

    def test_validate_action_compatibility(self):
        """Test action compatibility validation"""
        action = MoAIDeployAction()

        # Test compatible versions
        assert action.validate_version_compatibility("v1") is True
        assert action.validate_platform_compatibility("windows-latest") is True

        # Test incompatible versions
        assert action.validate_version_compatibility("v0.9") is False

        # Test incompatible platforms
        assert action.validate_platform_compatibility("macos-latest") is False

    def test_generate_action_documentation(self):
        """Test generating action documentation"""
        action = MoAIDeployAction()

        docs = action.generate_documentation(
            usage_example="uses: ./.github/actions/moai-deploy@v1",
            inputs_description={
                "config-file": "Path to deployment configuration"
            },
            troubleshooting_tips=["Check file permissions", "Validate configuration"]
        )

        assert "Usage" in docs
        assert "Inputs" in docs
        assert "Troubleshooting" in docs
        assert "uses: ./.github/actions/moai-deploy@v1" in docs


class TestGitHubSecretsManager:
    """Test cases for GitHubSecretsManager class"""

    def test_secrets_manager_initialization(self):
        """Test GitHubSecretsManager initialization"""
        manager = GitHubSecretsManager()

        assert manager.api_client is None
        assert manager.repository == None
        assert manager.secrets == {}

    def test_set_repository(self):
        """Test setting repository for secrets"""
        manager = GitHubSecretsManager()
        api_client = Mock()

        manager.set_repository("owner", "repo", api_client)

        assert manager.owner == "owner"
        assert manager.repo == "repo"
        assert manager.api_client == api_client

    def test_add_secrets_from_dict(self):
        """Test adding secrets from dictionary"""
        manager = GitHubSecretsManager()

        secrets = {
            "API_KEY": "secret123",
            "DATABASE_URL": "postgres://user:pass@localhost:5432/db",
            "ENVIRONMENT": "production"
        }

        manager.add_secrets(secrets)

        assert len(manager.secrets) == 3
        assert manager.secrets["API_KEY"] == "secret123"
        assert manager.secrets["DATABASE_URL"] == "postgres://user:pass@localhost:5432/db"

    def test_add_secrets_from_file(self):
        """Test adding secrets from file"""
        manager = GitHubSecretsManager()

        # Create temporary secrets file
        secrets_content = """
API_KEY: secret123
DATABASE_URL: postgres://user:pass@localhost:5432/db
ENVIRONMENT: production
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(secrets_content)
            temp_path = f.name

        try:
            manager.add_secrets_from_file(temp_path)

            assert len(manager.secrets) == 3
            assert manager.secrets["API_KEY"] == "secret123"

        finally:
            os.unlink(temp_path)

    @patch.object(GitHubAPIClient, 'create_or_update_secret')
    def test_sync_secrets_to_github(self, mock_create_secret):
        """Test syncing secrets to GitHub"""
        manager = GitHubSecretsManager()
        api_client = Mock()
        manager.set_repository("owner", "repo", api_client)
        manager.add_secrets({"API_KEY": "secret123"})

        mock_create_secret.return_value = True

        result = manager.sync_secrets()

        assert result is True
        assert mock_create_secret.call_count == 1
        mock_create_secret.assert_called_with("API_KEY", "secret123")

    def test_validate_secrets(self):
        """Test secret validation"""
        manager = GitHubSecretsManager()

        # Valid secrets
        valid_secrets = {
            "API_KEY": "valid-secret-123",
            "PASSWORD": "secure-password-456"
        }

        assert manager.validate_secrets(valid_secrets) is True

        # Invalid secrets (empty or too short)
        invalid_secrets = {
            "EMPTY_SECRET": "",
            "SHORT": "123",
            "NULL_SECRET": None
        }

        assert manager.validate_secrets(invalid_secrets) is False

    def test_generate_secrets_template(self):
        """Test generating secrets template"""
        manager = GitHubSecretsManager()

        template = manager.generate_secrets_template(
            required_secrets=["API_KEY", "DATABASE_URL", "ENVIRONMENT"],
            optional_secrets=["DEBUG_MODE"],
            descriptions={
                "API_KEY": "API authentication key",
                "DATABASE_URL": "Database connection string"
            }
        )

        assert template["required"] == ["API_KEY", "DATABASE_URL", "ENVIRONMENT"]
        assert template["optional"] == ["DEBUG_MODE"]
        assert "descriptions" in template
        assert template["descriptions"]["API_KEY"] == "API authentication key"

    def test_list_secrets(self):
        """Test listing secrets"""
        manager = GitHubSecretsManager()
        manager.add_secrets({"API_KEY": "secret123", "DB_PASS": "password456"})

        secrets_list = manager.list_secrets()

        assert len(secrets_list) == 2
        assert "API_KEY" in secrets_list
        assert "DB_PASS" in secrets_list

    def test_get_secret_value(self):
        """Test getting secret value"""
        manager = GitHubSecretsManager()
        manager.add_secrets({"API_KEY": "secret123"})

        value = manager.get_secret("API_KEY")
        assert value == "secret123"

        # Test getting nonexistent secret
        value = manager.get_secret("NONEXISTENT")
        assert value is None

    def test_remove_secret(self):
        """Test removing secret"""
        manager = GitHubSecretsManager()
        manager.add_secrets({"API_KEY": "secret123", "DB_PASS": "password456"})

        manager.remove_secret("API_KEY")

        assert len(manager.secrets) == 1
        assert "API_KEY" not in manager.secrets
        assert "DB_PASS" in manager.secrets


class TestGitHubBranchProtection:
    """Test cases for GitHubBranchProtection class"""

    def test_branch_protection_initialization(self):
        """Test GitHubBranchProtection initialization"""
        protection = GitHubBranchProtection()

        assert enabled := protection.settings.get("required_status_checks")
        assert enabled["strict"] is True
        assert enabled["contexts"] == ["ci/circleci: build"]

    def test_enable_pull_requests(self):
        """Test enabling pull request requirements"""
        protection = GitHubBranchProtection()

        protection.enable_pull_requests(
            require_code_owner_review=True,
            require_approving_review_count=2,
            dismiss_stale_reviews=False
        )

        settings = protection.settings
        assert settings["required_pull_request_reviews"]["require_code_owner_review"] is True
        assert settings["required_pull_request_reviews"]["require_approving_review_count"] == 2

    def test_enable_status_checks(self):
        """Test enabling status checks"""
        protection = GitHubBranchProtection()

        protection.enable_status_checks(
            required_contexts=["ci/circleci: build", "coverage"],
            strict=True
        )

        settings = protection.settings
        assert settings["required_status_checks"]["contexts"] == ["ci/circleci: build", "coverage"]

    def test_enable_branch_restrictions(self):
        """Test enabling branch restrictions"""
        protection = GitHubBranchProtection()

        protection.enable_restrictions(
            push_allow=["user1", "user2"],
            push_block=[],
            delete_allow=["admin"]
        )

        settings = protection.settings
        assert "restrictions" in settings
        assert "push" in settings["restrictions"]
        assert "delete" in settings["restrictions"]

    def test_enable_conversation_resolution(self):
        """Test enabling conversation resolution requirement"""
        protection = GitHubBranchProtection()

        protection.enable_conversation_resolution()

        assert protection.settings["required_conversation_resolution"] is True

    def test_enable_linear_history(self):
        """Test enabling linear history requirement"""
        protection = GitHubBranchProtection()

        protection.enable_linear_history()

        assert protection.settings["enforce_admins"]["enable"] is True

    def test_generate_protection_config(self):
        """Test generating protection configuration"""
        protection = GitHubBranchProtection()

        config = protection.generate_protection_config(
            branch_name="main",
            require_pull_requests=True,
            require_status_checks=True,
            restrict_push=True
        )

        assert config["branch"] == "main"
        assert "protection" in config
        assert config["protection"]["required_status_checks"]["strict"] is True

    def test_validate_protection_rules(self):
        """Test protection rules validation"""
        protection = GitHubBranchProtection()

        # Valid protection configuration
        valid_config = {
            "required_pull_request_reviews": True,
            "required_status_checks": True,
            "enforce_admins": True
        }

        assert protection.validate_rules(valid_config) is True

        # Invalid protection configuration
        invalid_config = {
            "required_pull_request_reviews": "invalid_value",
            "nonexistent_rule": True
        }

        assert protection.validate_rules(invalid_config) is False

    def test_apply_to_repository(self):
        """Test applying protection to repository"""
        protection = GitHubBranchProtection()
        api_client = Mock()

        protection.apply_to_repository("owner", "repo", "main", api_client)

        # Verify API client was called with protection settings
        api_client.update_branch_protection.assert_called_once()

    def test_create_branch_protection_rule(self):
        """Test creating branch protection rule"""
        protection = GitHubBranchProtection()

        rule = protection.create_rule(
            pattern="main",
            requires_approving_reviews=2,
            requires_status_checks=True,
            restricts_pushes=True
        )

        assert rule["pattern"] == "main"
        assert rule["protection"]["required_pull_request_reviews"]["require_approving_review_count"] == 2


class TestGitHubPRHandler:
    """Test cases for GitHubPRHandler class"""

    def test_pr_handler_initialization(self):
        """Test GitHubPRHandler initialization"""
        handler = GitHubPRHandler()

        assert handler.api_client is None
        assert handler.repository == None
        assert handler.auto_merge_enabled is False

    def test_set_repository(self):
        """Test setting repository for PR handling"""
        handler = GitHubPRHandler()
        api_client = Mock()

        handler.set_repository("owner", "repo", api_client)

        assert handler.owner == "owner"
        assert handler.repo == "repo"
        assert handler.api_client == api_client

    @patch.object(GitHubAPIClient, 'create_pull_request')
    def test_create_pull_request(self, mock_create_pr):
        """Test creating pull request"""
        handler = GitHubPRHandler()
        api_client = Mock()
        handler.set_repository("owner", "repo", api_client)

        mock_create_pr.return_value = {"number": 123, "html_url": "https://github.com/owner/repo/pull/123"}

        pr = handler.create_pull_request(
            title="Update deployment configuration",
            head="feature/deployment-update",
            base="main",
            body="Updated deployment workflow for Windows compatibility"
        )

        assert pr["number"] == 123
        assert pr["html_url"] == "https://github.com/owner/repo/pull/123"
        mock_create_pr.assert_called_once()

    @patch.object(GitHubAPIClient, 'get_pull_request')
    def test_get_pull_request(self, mock_get_pr):
        """Test getting pull request"""
        handler = GitHubPRHandler()
        api_client = Mock()
        handler.set_repository("owner", "repo", api_client)

        mock_get_pr.return_value = {
            "number": 123,
            "title": "Test PR",
            "user": {"login": "testuser"},
            "state": "open"
        }

        pr = handler.get_pull_request(123)

        assert pr["number"] == 123
        assert pr["title"] == "Test PR"
        mock_get_pr.assert_called_once_with(123)

    @patch.object(GitHubAPIClient, 'add_label_to_pull_request')
    def test_add_labels_to_pr(self, mock_add_label):
        """Test adding labels to pull request"""
        handler = GitHubPRHandler()
        api_client = Mock()
        handler.set_repository("owner", "repo", api_client)

        mock_add_label.return_value = True

        result = handler.add_labels_to_pr(123, ["windows", "deployment", "ready"])

        assert result is True
        assert mock_add_label.call_count == 3

    @patch.object(GitHubAPIClient, 'merge_pull_request')
    def test_merge_pull_request(self, mock_merge_pr):
        """Test merging pull request"""
        handler = GitHubPRHandler()
        api_client = Mock()
        handler.set_repository("owner", "repo", api_client)

        mock_merge_pr.return_value = {"merged": True, "sha": "abc123"}

        result = handler.merge_pull_request(
            pr_number=123,
            commit_title="Merge deployment updates",
            commit_message="Updated Windows deployment workflow"
        )

        assert result["merged"] is True
        assert result["sha"] == "abc123"

    @patch.object(GitHubAPIClient, 'create_pull_request_review')
    def test_add_pull_request_review(self, mock_create_review):
        """Test adding pull request review"""
        handler = GitHubPRHandler()
        api_client = Mock()
        handler.set_repository("owner", "repo", api_client)

        mock_create_review.return_value = {"id": 456}

        result = handler.add_review(
            pr_number=123,
            body="Please review Windows deployment changes",
            event="REQUEST_CHANGES"
        )

        assert result["id"] == 456

    def test_validate_pr_title(self):
        """Test pull request title validation"""
        handler = GitHubPRHandler()

        # Valid titles
        valid_titles = [
            "feat: Add Windows deployment support",
            "fix: Resolve Windows path handling issue",
            "docs: Update deployment documentation"
        ]

        for title in valid_titles:
            assert handler.validate_pr_title(title) is True

        # Invalid titles
        invalid_titles = [
            "",  # Empty
            "invalid title without prefix",  # No prefix
            "feat",  # Just prefix
            "123: Only numbers in prefix"  # Invalid prefix
        ]

        for title in invalid_titles:
            assert handler.validate_pr_title(title) is False

    def test_generate_pr_description(self):
        """Test generating pull request description"""
        handler = GitHubPRHandler()

        description = handler.generate_pr_description(
            changes=["Added Windows compatibility", "Fixed path handling"],
            testing=["Manual testing on Windows 11", "Automated tests passing"],
            impact="Backward compatible",
            reviewers=["developer1", "developer2"]
        )

        assert "Changes" in description
        assert "Testing" in description
        assert "Impact" in description
        assert "Reviewers" in description
        assert "Windows compatibility" in description
        assert "developer1" in description

    @patch.object(GitHubAPIClient, 'list_pull_requests')
    def test_list_pull_requests(self, mock_list_prs):
        """Test listing pull requests"""
        handler = GitHubPRHandler()
        api_client = Mock()
        handler.set_repository("owner", "repo", api_client)

        mock_list_prs.return_value = [
            {"number": 123, "title": "PR 1", "state": "open"},
            {"number": 124, "title": "PR 2", "state": "closed"}
        ]

        prs = handler.list_pull_requests(state="all")

        assert len(prs) == 2
        assert prs[0]["number"] == 123
        assert prs[1]["number"] == 124

    def test_check_pr_requirements(self):
        """Test checking pull request requirements"""
        handler = GitHubPRHandler()

        pr_data = {
            "title": "feat: Add Windows deployment",
            "body": "Updated deployment workflow for Windows",
            "labels": ["windows", "deployment", "ready"],
            "number": 123
        }

        requirements = {
            "title_prefix": "feat:",
            "required_labels": ["windows", "deployment"],
            "min_body_length": 10
        }

        result = handler.check_pr_requirements(pr_data, requirements)

        assert result["meets_requirements"] is True
        assert result["missing"] == []

        # Test failing requirements
        failing_requirements = {
            "title_prefix": "fix:",
            "required_labels": ["nonexistent"],
            "min_body_length": 1000
        }

        result = handler.check_pr_requirements(pr_data, failing_requirements)

        assert result["meets_requirements"] is False
        assert len(result["missing"]) > 0


class TestGitHubEventHandler:
    """Test cases for GitHubEventHandler class"""

    def test_event_handler_initialization(self):
        """Test GitHubEventHandler initialization"""
        handler = GitHubEventHandler()

        assert handler.handlers == {}
        assert handler.default_handler is None

    def test_register_event_handler(self):
        """Test registering event handlers"""
        handler = GitHubEventHandler()

        def pull_request_handler(event_data):
            return {"status": "processed"}

        handler.register_handler("pull_request", pull_request_handler)

        assert "pull_request" in handler.handlers
        assert handler.handlers["pull_request"] == pull_request_handler

    def test_register_default_handler(self):
        """Test registering default handler"""
        handler = GitHubEventHandler()

        def default_handler(event_data):
            return {"status": "default_processed"}

        handler.register_default_handler(default_handler)

        assert handler.default_handler == default_handler

    def test_handle_pull_request_event(self):
        """Test handling pull request events"""
        handler = GitHubEventHandler()

        def pr_handler(event_data):
            return {
                "action": event_data["action"],
                "number": event_data["pull_request"]["number"]
            }

        handler.register_handler("pull_request", pr_handler)

        event_data = {
            "action": "opened",
            "pull_request": {"number": 123}
        }

        result = handler.handle_event("pull_request", event_data)

        assert result["action"] == "opened"
        assert result["number"] == 123

    def test_handle_push_event(self):
        """Test handling push events"""
        handler = GitHubEventHandler()

        def push_handler(event_data):
            return {
                "ref": event_data["ref"],
                "commit": event_data["head_commit"]["id"]
            }

        handler.register_handler("push", push_handler)

        event_data = {
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123"}
        }

        result = handler.handle_event("push", event_data)

        assert result["ref"] == "refs/heads/main"
        assert result["commit"] == "abc123"

    def test_handle_deployment_event(self):
        """Test handling deployment events"""
        handler = GitHubEventHandler()

        deployment_handler = Mock(return_value={"status": "deployment_processed"})

        handler.register_handler("deployment", deployment_handler)

        event_data = {
            "deployment": {"id": 456, "environment": "production"},
            "action": "created"
        }

        result = handler.handle_event("deployment", event_data)

        assert result["status"] == "deployment_processed"
        deployment_handler.assert_called_once_with(event_data)

    def test_handle_unknown_event(self):
        """Test handling unknown events"""
        handler = GitHubEventHandler()

        def default_handler(event_data):
            return {"status": "unknown_event"}

        handler.register_default_handler(default_handler)

        event_data = {"action": "unknown_action"}

        result = handler.handle_event("unknown_event_type", event_data)

        assert result["status"] == "unknown_event"

    def test_event_routing(self):
        """Test event routing to correct handlers"""
        handler = GitHubEventHandler()

        handlers_called = []

        def log_handler(event_data):
            handlers_called.append("pull_request")
            return {"status": "logged"}

        handler.register_handler("pull_request", log_handler)

        # Test that only the correct handler is called
        result = handler.handle_event("pull_request", {"action": "opened"})

        assert result["status"] == "logged"
        assert handlers_called == ["pull_request"]

    def test_event_filtering(self):
        """Test event filtering"""
        handler = GitHubEventHandler()

        filtered_events = []

        def filtering_handler(event_data):
            filtered_events.append("pull_request")
            return {"status": "filtered"}

        handler.register_handler("pull_request", filtering_handler)

        # Test event is processed
        result = handler.handle_event("pull_request", {"action": "opened"})

        assert result["status"] == "filtered"
        assert len(filtered_events) == 1


class TestGitHubAPIClient:
    """Test cases for GitHubAPIClient class"""

    def test_api_client_initialization(self):
        """Test GitHubAPIClient initialization"""
        client = GitHubAPIClient()

        assert client.token is None
        assert client.base_url == "https://api.github.com"
        assert client.timeout == 30

    def test_set_authentication_token(self):
        """Test setting authentication token"""
        client = GitHubAPIClient()

        client.set_token("ghp_test123456")

        assert client.token == "ghp_test123456"

    @patch('requests.get')
    def test_get_repository(self, mock_get):
        """Test getting repository information"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "private": False
        }
        mock_get.return_value = mock_response

        repo = client.get_repository("owner", "test-repo")

        assert repo["name"] == "test-repo"
        assert mock_get.call_count == 1

    @patch('requests.get')
    def test_get_pull_request(self, mock_get):
        """Test getting pull request information"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test PR",
            "state": "open"
        }
        mock_get.return_value = mock_response

        pr = client.get_pull_request(123)

        assert pr["number"] == 123
        assert pr["title"] == "Test PR"

    @patch('requests.post')
    def test_create_pull_request(self, mock_post):
        """Test creating pull request"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/owner/repo/pull/123"
        }
        mock_post.return_value = mock_response

        pr = client.create_pull_request(
            owner="owner",
            repo="repo",
            title="Test PR",
            head="feature-branch",
            base="main"
        )

        assert pr["number"] == 123
        assert pr["html_url"] == "https://github.com/owner/repo/pull/123"

    @patch('requests.put')
    def test_create_or_update_secret(self, mock_put):
        """Test creating or updating repository secret"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 201
        mock_put.return_value = mock_response

        result = client.create_or_update_secret(
            owner="owner",
            repo="repo",
            secret_name="API_KEY",
            secret_value="secret123"
        )

        assert result is True

    @patch('requests.put')
    def test_update_branch_protection(self, mock_put):
        """Test updating branch protection"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        protection_settings = {
            "required_status_checks": {"strict": True, "contexts": ["ci"]},
            "required_pull_request_reviews": {"require_code_owner_reviews": True}
        }

        result = client.update_branch_protection(
            owner="owner",
            repo="repo",
            branch="main",
            settings=protection_settings
        )

        assert result is True

    @patch('requests.get')
    def test_list_pull_requests(self, mock_get):
        """Test listing pull requests"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"number": 123, "title": "PR 1", "state": "open"},
            {"number": 124, "title": "PR 2", "state": "closed"}
        ]
        mock_get.return_value = mock_response

        prs = client.list_pull_requests("owner", "repo")

        assert len(prs) == 2
        assert prs[0]["number"] == 123

    @patch('requests.post')
    def test_merge_pull_request(self, mock_post):
        """Test merging pull request"""
        client = GitHubAPIClient()
        client.set_token("ghp_test123456")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"merged": True, "sha": "abc123"}
        mock_post.return_value = mock_response

        result = client.merge_pull_request(
            owner="owner",
            repo="repo",
            pr_number=123,
            commit_title="Merge PR",
            commit_message="Merged changes"
        )

        assert result["merged"] is True
        assert result["sha"] == "abc123"

    def test_validate_authentication(self):
        """Test authentication validation"""
        client = GitHubAPIClient()

        # Test without token
        assert client.validate_authentication() is False

        # Test with token
        client.set_token("ghp_test123456")
        assert client.validate_authentication() is True

    def test_handle_api_errors(self):
        """Test API error handling"""
        client = GitHubAPIClient()

        # Test rate limiting
        rate_limit_error = {
            "message": "API rate limit exceeded",
            "documentation_url": "https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting"
        }

        error = client.handle_api_error(rate_limit_error, 403)

        assert isinstance(error, APIError)
        assert "rate limit" in str(error).lower()

        # Test not found error
        not_found_error = {
            "message": "Not Found"
        }

        error = client.handle_api_error(not_found_error, 404)

        assert isinstance(error, APIError)
        assert "not found" in str(error).lower()


class TestGitHubIntegration:
    """Integration tests for GitHub Actions components"""

    def test_complete_ci_cd_workflow_generation(self):
        """Test complete CI/CD workflow generation"""
        # Initialize components
        workflow_generator = GitHubWorkflowGenerator()
        workflow_generator.set_repository("owner", "repo", "main")

        secrets_manager = GitHubSecretsManager()
        secrets_manager.add_secrets({
            "API_KEY": "secret123",
            "DATABASE_URL": "postgres://localhost:5432/db"
        })

        # Generate deployment workflow
        workflow = workflow_generator.generate_deployment_workflow(
            name="Windows CI/CD Pipeline",
            on=["push", "pull_request"],
            secrets=["API_KEY", "DATABASE_URL"],
            steps_config=[
                {
                    "name": "Setup Environment",
                    "uses": "actions/setup-python@v4",
                    "with": {"python-version": "3.11"}
                },
                {
                    "name": "Run Tests",
                    "run": "pytest --cov=src/"
                },
                {
                    "name": "Deploy to Production",
                    "uses": "./.github/actions/moai-deploy@v1",
                    "env": {
                        "API_KEY": "${{ secrets.API_KEY }}",
                        "DATABASE_URL": "${{ secrets.DATABASE_URL }}"
                    }
                }
            ]
        )

        # Validate workflow
        assert workflow_generator.validate_workflow(workflow) is True

        # Verify workflow structure
        assert "jobs" in workflow
        assert "deploy" in workflow["jobs"]

        # Verify secrets are referenced
        deploy_steps = workflow["jobs"]["deploy"]["steps"]
        env_steps = [step for step in deploy_steps if "env" in step]
        assert len(env_steps) > 0

    def test_github_actions_deployment_action(self):
        """Test GitHub Actions deployment action creation"""
        deploy_action = MoAIDeployAction()

        # Generate action components
        manifest = deploy_action.generate_manifest(
            name="moai-deploy",
            description="MoAI ADK Windows Deployment Action",
            inputs={
                "config": {"description": "Deployment configuration file"},
                "environment": {"description": "Target environment"}
            }
        )

        dockerfile = deploy_action.generate_dockerfile(
            base_image="python:3.11-slim",
            install_commands=["pip install moai-adk", "pip install click pyyaml tqdm"]
        )

        action_script = deploy_action.generate_action_script(
            main_command="moai deploy --config ${{ inputs.config }} --env ${{ inputs.environment }}"
        )

        # Validate generated components
        assert manifest["name"] == "moai-deploy"
        assert "FROM python:3.11-slim" in dockerfile
        assert "moai deploy" in action_script

    def test_branch_protection_and_pr_workflow(self):
        """Test branch protection and pull request workflow"""
        # Setup branch protection
        branch_protection = GitHubBranchProtection()
        branch_protection.enable_pull_requests(
            require_code_owner_review=True,
            require_approving_review_count=2
        )
        branch_protection.enable_status_checks(
            required_contexts=["ci/circleci: build", "coverage"],
            strict=True
        )

        # Setup PR handler
        pr_handler = GitHubPRHandler()
        api_client = Mock()
        pr_handler.set_repository("owner", "repo", api_client)

        # Test PR creation
        pr_data = pr_handler.create_pull_request(
            title="feat: Add Windows deployment workflow",
            head="feature/windows-deployment",
            base="main",
            body="Added Windows-specific deployment optimizations"
        )

        assert pr_data["number"] is not None

        # Test PR requirements check
        pr_requirements = {
            "title_prefix": "feat:",
            "required_labels": ["windows", "deployment"],
            "min_body_length": 10
        }

        mock_pr = {
            "title": "feat: Add Windows deployment workflow",
            "body": "Added Windows-specific deployment optimizations",
            "labels": ["windows", "deployment"]
        }

        requirements_check = pr_handler.check_pr_requirements(mock_pr, pr_requirements)

        assert requirements_check["meets_requirements"] is True

    def test_github_event_processing_workflow(self):
        """Test GitHub event processing workflow"""
        event_handler = GitHubEventHandler()

        # Register event handlers
        def pr_handler(event_data):
            if event_data["action"] == "opened":
                return {"action": "review_requested", "pr_number": event_data["pull_request"]["number"]}
            return {"action": "processed"}

        def push_handler(event_data):
            return {
                "ref": event_data["ref"],
                "commit": event_data["head_commit"]["id"]
            }

        event_handler.register_handler("pull_request", pr_handler)
        event_handler.register_handler("push", push_handler)

        # Test pull request event
        pr_event = {
            "action": "opened",
            "pull_request": {"number": 123, "title": "Test PR"}
        }

        pr_result = event_handler.handle_event("pull_request", pr_event)

        assert pr_result["action"] == "review_requested"
        assert pr_result["pr_number"] == 123

        # Test push event
        push_event = {
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123", "message": "Update deployment workflow"}
        }

        push_result = event_handler.handle_event("push", push_event)

        assert push_result["ref"] == "refs/heads/main"
        assert push_result["commit"] == "abc123"

    @patch('requests.post')
    def test_secrets_sync_workflow(self, mock_post):
        """Test secrets synchronization workflow"""
        # Setup secrets manager
        secrets_manager = GitHubSecretsManager()
        api_client = Mock()
        secrets_manager.set_repository("owner", "repo", api_client)

        # Add secrets
        secrets_manager.add_secrets({
            "API_KEY": "new-secret-123",
            "DATABASE_URL": "postgres://new:pass@new-host:5432/db"
        })

        # Mock successful API calls
        mock_post.return_value.status_code = 201

        # Sync secrets
        sync_result = secrets_manager.sync_secrets()

        assert sync_result is True
        assert mock_post.call_count == 2  # Called for each secret

    def test_error_handling_scenarios(self):
        """Test error handling scenarios"""
        # Test API client error handling
        api_client = GitHubAPIClient()

        # Test without authentication
        assert api_client.validate_authentication() is False

        # Test invalid API response
        with pytest.raises(APIError):
            api_client.handle_api_error({"message": "Invalid token"}, 401)

        # Test invalid workflow
        workflow_generator = GitHubWorkflowGenerator()

        invalid_workflow = {
            "name": "Invalid Workflow"
            # Missing required fields
        }

        assert workflow_generator.validate_workflow(invalid_workflow) is False

        # Test invalid secrets
        secrets_manager = GitHubSecretsManager()

        invalid_secrets = {
            "EMPTY_SECRET": "",
            "SHORT": "123"
        }

        assert secrets_manager.validate_secrets(invalid_secrets) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])