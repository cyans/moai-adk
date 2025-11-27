"""
Code review workflow automation engine.
"""
import os
import subprocess
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import uuid
from dataclasses import dataclass


@dataclass
class ReviewComment:
    """Code review comment data structure."""
    line: int
    comment: str
    severity: str  # low, medium, high, critical
    reviewer_id: str
    timestamp: str
    file_path: str


@dataclass
class ReviewData:
    """Code review data structure."""
    review_id: str
    pr_number: int
    author: str
    title: str
    description: str
    files_changed: List[str]
    reviewers: List[str]
    status: str  # pending, in_progress, completed, approved, changes_requested
    created_at: str
    completed_at: Optional[str] = None
    comments: List[ReviewComment] = None
    overall_score: float = 0.0


class ReviewEngine:
    """Code review workflow automation engine."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        """Initialize review engine."""
        self.repo_path = Path(repo_path)
        self.config = config
        self.logger = self._setup_logger()
        self.active_reviews = {}

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for review engine."""
        logger = logging.getLogger('ReviewEngine')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def on_pr_created(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request creation event."""
        try:
            self.logger.info(f"Processing PR created event: {pr_data['title']}")

            # Generate review ID
            review_id = str(uuid.uuid4())
            pr_number = pr_data["pr_number"]

            # Create review data object
            review = ReviewData(
                review_id=review_id,
                pr_number=pr_number,
                author=pr_data["author"],
                title=pr_data["title"],
                description=pr_data["description"],
                files_changed=pr_data["files_changed"],
                reviewers=[],
                status="pending",
                created_at=datetime.now().isoformat(),
                comments=[]
            )

            # Store the review
            self.active_reviews[review_id] = review

            # Initialize review process
            result = {
                "success": True,
                "review_id": review_id,
                "pr_number": pr_number,
                "required_actions": [
                    "analyze_code_changes",
                    "assign_reviewers",
                    "create_review_requests",
                    "monitor_progress"
                ],
                "next_steps": [
                    "Execute code analysis",
                    "Assign reviewers based on expertise",
                    "Send review requests",
                    "Wait for review completion"
                ],
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(f"PR processed successfully. Review ID: {review_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to process PR created event: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def execute_code_analysis(self, analysis_config: Dict[str, bool]) -> Dict[str, Any]:
        """Execute comprehensive code analysis."""
        try:
            self.logger.info("Executing code analysis...")

            analysis_results = {
                "static_analysis": {},
                "unit_test_coverage": {},
                "security_scan": {},
                "complexity_analysis": {},
                "style_check": {},
                "overall_score": 0.0
            }

            total_checks = 0
            passed_checks = 0

            # 1. Static Analysis
            if analysis_config.get("static_analysis", False):
                total_checks += 1
                static_result = self._perform_static_analysis()
                analysis_results["static_analysis"] = static_result
                if static_result.get("success", False):
                    passed_checks += 1

            # 2. Unit Test Coverage
            if analysis_config.get("unit_test_coverage", False):
                total_checks += 1
                coverage_result = self._check_test_coverage()
                analysis_results["unit_test_coverage"] = coverage_result
                if coverage_result.get("meets_threshold", False):
                    passed_checks += 1

            # 3. Security Scan
            if analysis_config.get("security_scan", False):
                total_checks += 1
                security_result = self._perform_security_scan()
                analysis_results["security_scan"] = security_result
                if security_result.get("vulnerabilities_count", 0) == 0:
                    passed_checks += 1

            # 4. Complexity Analysis
            if analysis_config.get("complexity_analysis", False):
                total_checks += 1
                complexity_result = self._analyze_complexity()
                analysis_results["complexity_analysis"] = complexity_result
                if complexity_result.get("average_complexity", 0) <= self.config.get("complexity_threshold", 10):
                    passed_checks += 1

            # 5. Style Check
            if analysis_config.get("style_check", False):
                total_checks += 1
                style_result = self._check_code_style()
                analysis_results["style_check"] = style_result
                if style_result.get("compliance_rate", 0) >= self.config.get("style_compliance", 0.95):
                    passed_checks += 1

            # Calculate overall score
            if total_checks > 0:
                analysis_results["overall_score"] = (passed_checks / total_checks) * 10

            return {
                "success": True,
                "analysis_results": analysis_results,
                "checks_passed": passed_checks,
                "total_checks": total_checks,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Code analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _perform_static_analysis(self) -> Dict[str, Any]:
        """Perform static code analysis."""
        try:
            issues = []
            files_analyzed = 0

            # Analyze Python files in the repository
            for py_file in self.repo_path.rglob("*.py"):
                files_analyzed += 1
                file_issues = self._analyze_python_file(py_file)
                issues.extend(file_issues)

            return {
                "success": True,
                "issues_found": len(issues),
                "files_analyzed": files_analyzed,
                "issues_by_severity": self._count_issues_by_severity(issues),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _analyze_python_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze individual Python file for issues."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line_content = line.strip()

                # Check for common issues
                if self._contains_security_issue(line_content):
                    issues.append({
                        "line": line_num,
                        "type": "security",
                        "severity": "high",
                        "message": "Potential security vulnerability detected",
                        "file": str(file_path)
                    })

                if self._is_complex_line(line_content):
                    issues.append({
                        "line": line_num,
                        "type": "complexity",
                        "severity": "medium",
                        "message": "Complex line structure",
                        "file": str(file_path)
                    })

                if self._violates_style_guide(line_content):
                    issues.append({
                        "line": line_num,
                        "type": "style",
                        "severity": "low",
                        "message": "Style guide violation",
                        "file": str(file_path)
                    })

        except Exception as e:
            issues.append({
                "line": 0,
                "type": "analysis_error",
                "severity": "critical",
                "message": f"Failed to analyze file: {str(e)}",
                "file": str(file_path)
            })

        return issues

    def _contains_security_issue(self, line: str) -> bool:
        """Check if line contains security issues."""
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*[\'"][^\'"]{8,}[\'"]',
            r'api_key\s*=\s*[\'"][^\'"]{16,}[\'"]',
            r'secret\s*=\s*[\'"][^\'"]{8,}[\'"]'
        ]

        for pattern in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True

        # Check for dangerous functions
        dangerous_functions = ['eval', 'exec', 'os.system', 'subprocess.run']
        for func in dangerous_functions:
            if func in line:
                return True

        return False

    def _is_complex_line(self, line: str) -> bool:
        """Check if line is overly complex."""
        # Count nested structures
        if line.count('(') - line.count(')') > 3:
            return True

        if line.count('[') - line.count(']') > 2:
            return True

        if line.count('{') - line.count('}') > 2:
            return True

        return False

    def _violates_style_guide(self, line: str) -> bool:
        """Check if line violates style guide."""
        # Check line length
        if len(line) > 120:
            return True

        # Check for tabs (should use spaces)
        if '\t' in line:
            return True

        return False

    def _count_issues_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            severity = issue.get("severity", "medium")
            counts[severity] = counts.get(severity, 0) + 1

        return counts

    def _check_test_coverage(self) -> Dict[str, Any]:
        """Check unit test coverage."""
        try:
            # Look for test files
            test_files = list(self.repo_path.rglob("test_*.py")) + list(self.repo_path.rglob("*_test.py"))
            source_files = list(self.repo_path.rglob("*.py"))

            if not source_files:
                return {
                    "success": False,
                    "error": "No source files found",
                    "timestamp": datetime.now().isoformat()
                }

            # Calculate estimated coverage based on test file presence
            coverage_ratio = min(len(test_files) / len(source_files), 1.0)
            threshold = self.config.get("coverage_threshold", 0.85)

            return {
                "success": True,
                "coverage_ratio": coverage_ratio,
                "meets_threshold": coverage_ratio >= threshold,
                "threshold": threshold,
                "test_files_count": len(test_files),
                "source_files_count": len(source_files),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _perform_security_scan(self) -> Dict[str, Any]:
        """Perform security vulnerability scan."""
        try:
            vulnerabilities = []
            scanned_files = 0

            # Scan for common security patterns
            for py_file in self.repo_path.rglob("*.py"):
                scanned_files += 1
                vulns = self._scan_file_for_vulnerabilities(py_file)
                vulnerabilities.extend(vulns)

            return {
                "success": True,
                "vulnerabilities_count": len(vulnerabilities),
                "scanned_files": scanned_files,
                "vulnerabilities": vulnerabilities,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _scan_file_for_vulnerabilities(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan file for security vulnerabilities."""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for SQL injection patterns
            sql_injection_patterns = [
                r"execute\s*\([^)]+\s+\+\s*[^)]+\)",
                r"cursor\.execute\s*\([^)]*%s[^)]*\)",
                r"query\s*=\s*f[\'\"][^\'\"]*\{.*\}[^\'\"]*[\'\"]"
            ]

            for i, line in enumerate(content.split('\n'), 1):
                for pattern in sql_injection_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        vulnerabilities.append({
                            "line": i,
                            "type": "sql_injection",
                            "severity": "critical",
                            "message": "Potential SQL injection vulnerability",
                            "file": str(file_path)
                        })

        except Exception as e:
            vulnerabilities.append({
                "line": 0,
                "type": "scan_error",
                "severity": "high",
                "message": f"Failed to scan file: {str(e)}",
                "file": str(file_path)
            })

        return vulnerabilities

    def _analyze_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity."""
        try:
            complexities = []
            total_complexity = 0
            analyzed_files = 0

            for py_file in self.repo_path.rglob("*.py"):
                analyzed_files += 1
                file_complexity = self._calculate_file_complexity(py_file)
                complexities.append(file_complexity)
                total_complexity += file_complexity

            average_complexity = total_complexity / analyzed_files if analyzed_files > 0 else 0

            return {
                "success": True,
                "average_complexity": average_complexity,
                "total_complexity": total_complexity,
                "analyzed_files": analyzed_files,
                "threshold": self.config.get("complexity_threshold", 10),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_file_complexity(self, file_path: Path) -> float:
        """Calculate complexity score for a file."""
        try:
            complexity_score = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count lines of code
                lines = len([line for line in content.split('\n') if line.strip()])

            # Count nested structures
                nesting_level = 0
                max_nesting = 0

                for line in content.split('\n'):
                    for char in line:
                        if char in '([{':
                            nesting_level += 1
                            max_nesting = max(max_nesting, nesting_level)
                        elif char in ')]}':
                            nesting_level = max(0, nesting_level - 1)

                # Calculate complexity (simplified metric)
                    complexity_score += lines * 0.1
                    complexity_score += max_nesting * 2.0
                    complexity_score += content.count('if ') * 0.5
                    complexity_score += content.count('for ') * 0.5
                    complexity_score += content.count('while ') * 0.5
                    complexity_score += content.count('def ') * 1.0
                    complexity_score += content.count('class ') * 1.5

            return complexity_score

        except Exception as e:
            return 0.0

    def _check_code_style(self) -> Dict[str, Any]:
        """Check code style compliance."""
        try:
            style_issues = 0
            total_checks = 0

            for py_file in self.repo_path.rglob("*.py"):
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    total_checks += 1

                    # Check various style issues
                    if len(line.strip()) > 120:
                        style_issues += 1

                    if line.strip() and line[0].isspace() and '\t' in line:
                        style_issues += 1

                    # Check for common style violations
                    if 'import *' in line:
                        style_issues += 1

                    if len([word for word in line.split() if len(word) > 30]) > 0:
                        style_issues += 1

            compliance_rate = 1.0 - (style_issues / total_checks) if total_checks > 0 else 1.0

            return {
                "success": True,
                "compliance_rate": compliance_rate,
                "style_issues_count": style_issues,
                "total_checks": total_checks,
                "threshold": self.config.get("style_compliance", 0.95),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def assign_reviewers(self, available_reviewers: List[Dict[str, Any]], pr_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assign reviewers based on expertise and availability."""
        try:
            self.logger.info("Assigning reviewers...")

            assignments = []
            context_technologies = pr_context.get("technologies", [])
            context_complexity = pr_context.get("complexity", "low")

            # Calculate reviewer scores
            reviewer_scores = []
            for reviewer in available_reviewers:
                score = self._calculate_reviewer_score(reviewer, context_technologies, context_complexity)
                reviewer_scores.append({
                    "reviewer_id": reviewer["id"],
                    "score": score,
                    "expertise": reviewer["expertise"],
                    "load": reviewer["load"]
                })

            # Sort by score (descending)
            reviewer_scores.sort(key=lambda x: x["score"], reverse=True)

            # Select top reviewers based on required count
            required_reviewers = self.config.get("workflow", {}).get("required_reviewers", 2)
            selected_reviewers = reviewer_scores[:required_reviewers]

            # Create assignments
            for reviewer in selected_reviewers:
                assignments.append({
                    "reviewer_id": reviewer["reviewer_id"],
                    "assigned_at": datetime.now().isoformat(),
                    "reason": f"High expertise match with score: {reviewer['score']:.2f}",
                    "expertise_match": self._calculate_expertise_match(reviewer["expertise"], context_technologies)
                })

            return {
                "success": True,
                "assignments": assignments,
                "total_reviewers": len(available_reviewers),
                "selected_reviewers": len(selected_reviewers),
                "required_reviewers": required_reviewers,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Reviewer assignment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_reviewer_score(self, reviewer: Dict[str, Any], technologies: List[str], complexity: str) -> float:
        """Calculate suitability score for a reviewer."""
        score = 0.0

        # Expertise matching
        expertise_matches = len(set(reviewer["expertise"]) & set(technologies))
        score += expertise_matches * 3.0  # High weight for expertise

        # Load factor (lower load is better)
        load_factor = max(0, 3 - reviewer["load"])  # Scale from 0-3
        score += load_factor * 2.0

        # Complexity bonus
        complexity_bonus = {"low": 0, "medium": 1, "high": 2}
        score += complexity_bonus.get(complexity, 0)

        return score

    def _calculate_expertise_match(self, reviewer_expertise: List[str], required_technologies: List[str]) -> Dict[str, Any]:
        """Calculate expertise match details."""
        matching_expertise = set(reviewer_expertise) & set(required_technologies)
        total_expertise = len(set(reviewer_expertise) | set(required_technologies))

        match_percentage = len(matching_expertise) / len(required_technologies) if required_technologies else 0

        return {
            "matching_expertise": list(matching_expertise),
            "total_required": len(required_technologies),
            "match_percentage": match_percentage
        }

    def generate_review_requests(self, review_assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate review requests for assigned reviewers."""
        try:
            self.logger.info("Generating review requests...")

            notifications = []

            for assignment in review_assignment.get("assignments", []):
                reviewer_id = assignment["reviewer_id"]

                notification = {
                    "notification_id": str(uuid.uuid4()),
                    "reviewer_id": reviewer_id,
                    "review_id": self.active_reviews.get_current_review_id(),
                    "pr_number": self.active_reviews.get_current_pr_number(),
                    "title": self.active_reviews.get_current_pr_title(),
                    "deadline": review_assignment.get("deadline"),
                    "priority": review_assignment.get("priority", "normal"),
                    "assigned_at": datetime.now().isoformat(),
                    "notification_sent": False,
                    "notification_channel": self._get_reviewer_notification_channel(reviewer_id)
                }

                # Simulate sending notification
                notification["notification_sent"] = self._send_review_notification(notification)
                notifications.append(notification)

            return {
                "success": True,
                "notifications": notifications,
                "total_notifications": len(notifications),
                "sent_notifications": sum(1 for n in notifications if n["notification_sent"]),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Review request generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _get_reviewer_notification_channel(self, reviewer_id: str) -> str:
        """Get notification channel for a reviewer."""
        # In a real implementation, this would check reviewer preferences
        return "email"

    def _send_review_notification(self, notification: Dict[str, Any]) -> bool:
        """Send review notification (simulated)."""
        try:
            self.logger.info(f"Sending notification to {notification['reviewer_id']}...")
            # Simulate notification sending
            return True
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False

    def process_review_responses(self, review_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process review responses from reviewers."""
        try:
            self.logger.info("Processing review responses...")

            all_comments = []
            overall_status = "pending"
            overall_score = 0.0
            completed_reviews = 0

            for response in review_responses:
                reviewer_id = response["reviewer_id"]
                status = response["status"]
                comments = response.get("comments", [])
                score = response.get("overall_score", 0.0)

                # Process comments
                for comment in comments:
                    comment_obj = ReviewComment(
                        line=comment["line"],
                        comment=comment["comment"],
                        severity=comment["severity"],
                        reviewer_id=reviewer_id,
                        timestamp=datetime.now().isoformat(),
                        file_path=comment.get("file_path", "unknown")
                    )
                    all_comments.append(comment_obj)

                # Update overall status
                if status == "approved":
                    completed_reviews += 1
                    overall_score += score
                elif status == "changes_requested":
                    overall_status = "changes_requested"

            # Calculate final status
            if overall_status == "pending" and completed_reviews > 0:
                # Check if we have enough approvals
                required_approvals = self.config.get("workflow", {}).get("required_approvals", 1)
                if completed_reviews >= required_approvals:
                    overall_status = "approved"

            # Calculate average score
            if completed_reviews > 0:
                overall_score /= completed_reviews

            return {
                "success": True,
                "overall_status": overall_status,
                "overall_score": overall_score,
                "completed_reviews": completed_reviews,
                "total_reviewers": len(review_responses),
                "comments": [vars(comment) for comment in all_comments],
                "action_items": self._generate_action_items(all_comments),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Review response processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_action_items(self, comments: List[ReviewComment]) -> List[Dict[str, Any]]:
        """Generate action items from review comments."""
        action_items = []

        # Group comments by severity
        high_severity_comments = [c for c in comments if c.severity in ["high", "critical"]]

        for comment in high_severity_comments:
            action_items.append({
                "action_item_id": str(uuid.uuid4()),
                "comment": comment.comment,
                "severity": comment.severity,
                "file_path": comment.file_path,
                "line": comment.line,
                "reviewer_id": comment.reviewer_id,
                "status": "pending",
                "assigned_to": None,
                "due_date": None,
                "created_at": datetime.now().isoformat()
            })

        return action_items

    def prioritize_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prioritize review comments by severity and impact."""
        try:
            # Define priority levels
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

            # Sort by priority (lower number = higher priority)
            prioritized_comments = sorted(
                comments,
                key=lambda x: priority_order.get(x["severity"], 4)
            )

            return {
                "success": True,
                "prioritized_comments": prioritized_comments,
                "comments_by_severity": self._group_comments_by_severity(prioritized_comments),
                "total_comments": len(prioritized_comments),
                "high_priority_comments": len([c for c in prioritized_comments if c["severity"] in ["high", "critical"]]),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _group_comments_by_severity(self, comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group comments by severity level."""
        grouped = {"critical": [], "high": [], "medium": [], "low": []}

        for comment in comments:
            severity = comment.get("severity", "medium")
            if severity in grouped:
                grouped[severity].append(comment)

        return grouped

    def track_workflow_status(self, workflow_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Track review workflow status."""
        try:
            if not workflow_events:
                return {
                    "success": False,
                    "error": "No workflow events provided",
                    "timestamp": datetime.now().isoformat()
                }

            # Sort events by timestamp
            sorted_events = sorted(workflow_events, key=lambda x: x["timestamp"])

            current_stage = "unknown"
            stage_durations = {}
            total_duration = 0

            for i, event in enumerate(sorted_events[1:], 1):
                previous_event = sorted_events[i-1]
                current_time = datetime.fromisoformat(event["timestamp"])
                previous_time = datetime.fromisoformat(previous_event["timestamp"])
                duration = (current_time - previous_time).total_seconds()

                event_name = event["event"]
                stage_durations[f"{previous_event['event']}_to_{event_name}"] = duration

                # Update current stage
                if event["event"] in ["pr_created", "review_assigned"]:
                    current_stage = "review_in_progress"
                elif event["event"] == "reviews_completed":
                    current_stage = "review_completed"

            # Calculate total duration
            start_time = datetime.fromisoformat(sorted_events[0]["timestamp"])
            end_time = datetime.fromisoformat(sorted_events[-1]["timestamp"])
            total_duration = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "current_stage": current_stage,
                "total_duration_seconds": total_duration,
                "stage_durations": stage_durations,
                "completion_percentage": self._calculate_completion_percentage(sorted_events),
                "events_count": len(sorted_events),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_completion_percentage(self, events: List[Dict[str, Any]]) -> float:
        """Calculate workflow completion percentage."""
        # Define expected workflow stages
        expected_stages = ["pr_created", "review_assigned", "reviews_completed"]

        # Track completed stages
        completed_stages = set()
        for event in events:
            if event["event"] in expected_stages:
                completed_stages.add(event["event"])

        return (len(completed_stages) / len(expected_stages)) * 100

    def collect_review_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and analyze review metrics."""
        try:
            review_duration = metrics_data.get("review_duration", 0)
            comments_count = metrics_data.get("comments_count", 0)
            approvals_count = metrics_data.get("approvals_count", 0)
            changes_requested = metrics_data.get("changes_requested", 0)
            quality_score = metrics_data.get("quality_score", 0.0)

            # Calculate derived metrics
            comments_per_review = comments_count / max(approvals_count + changes_requested, 1)
            approval_rate = approvals_count / max(approvals_count + changes_requested, 1) if (approvals_count + changes_requested) > 0 else 0

            # Calculate average review time
            total_reviews = approvals_count + changes_requested
            average_review_time = review_duration / max(total_reviews, 1)

            return {
                "success": True,
                "collected_metrics": metrics_data,
                "derived_metrics": {
                    "comments_per_review": comments_per_review,
                    "approval_rate": approval_rate,
                    "average_review_time": average_review_time,
                    "total_reviews": total_reviews
                },
                "performance_indicators": {
                    "efficiency": "good" if comments_per_review < 5 else "needs_improvement",
                    "quality": "excellent" if quality_score >= 8.0 else "good" if quality_score >= 6.0 else "needs_attention"
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }