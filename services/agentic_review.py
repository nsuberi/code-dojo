"""Agentic review service for multi-step code analysis (Section 3.2)."""

import os
import json
import re
from anthropic import Anthropic
from config import Config

# LangSmith tracing - optional dependency
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    # Fallback decorator that does nothing
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False


class AgenticReviewService:
    """Multi-step review pipeline for analyzing code submissions."""

    def __init__(self, submission_id=None):
        self.submission_id = submission_id
        self.api_key = Config.ANTHROPIC_API_KEY
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def _call_claude(self, prompt, max_tokens=1500):
        """Make a call to Claude API."""
        if not self.client:
            return None

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    @traceable(name="detect_approach")
    def _detect_approach(self, diff_content, rubric):
        """
        Step 1: Detect which approach the student used.
        Returns: {approach_id, confidence, evidence_lines}
        """
        valid_approaches = rubric.get('valid_approaches', [])

        # Build detection prompt
        approaches_desc = "\n".join([
            f"- {a['id']}: {a['name']} - Look for: {', '.join(a['detection_patterns'])}"
            for a in valid_approaches
        ])

        prompt = f"""Analyze this code diff to determine which authentication approach was used.

## Valid Approaches
{approaches_desc}

## Code Diff
{diff_content}

Respond in JSON format:
{{
    "approach_id": "the approach ID (api_key, basic_auth, or jwt)",
    "confidence": "high, medium, or low",
    "evidence_lines": ["list of specific line numbers or code snippets that indicate this approach"],
    "reasoning": "brief explanation of why this approach was detected"
}}"""

        result = self._call_claude(prompt, max_tokens=500)
        if not result:
            return {"approach_id": "unknown", "confidence": "low", "evidence_lines": [], "reasoning": "No API key configured"}

        # Extract JSON from response
        try:
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"approach_id": "unknown", "confidence": "low", "evidence_lines": [], "reasoning": result}

    @traceable(name="analyze_architecture")
    def _analyze_architecture(self, diff_content):
        """
        Step 2: Analyze the code architecture and component map.
        Returns: component map with line ranges
        """
        prompt = f"""Analyze the architecture of this code diff. Identify the main components and their line ranges.

## Code Diff
{diff_content}

Respond in JSON format:
{{
    "components": [
        {{"name": "component name", "type": "decorator/route/function/etc", "start_line": 1, "end_line": 10, "purpose": "brief description"}}
    ],
    "overall_structure": "brief description of how the code is organized"
}}"""

        result = self._call_claude(prompt, max_tokens=800)
        if not result:
            return {"components": [], "overall_structure": "Unable to analyze"}

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"components": [], "overall_structure": result}

    @traceable(name="evaluate_universal_criteria")
    def _evaluate_universal_criteria(self, diff_content, rubric):
        """
        Step 3: Evaluate approach-agnostic criteria.
        Returns: list of criteria evaluations
        """
        universal_criteria = rubric.get('universal_criteria', [])

        criteria_list = "\n".join([
            f"- {c['id']}: {c['criterion']} (pass indicators: {', '.join(c['pass_indicators'])})"
            for c in universal_criteria
        ])

        prompt = f"""Evaluate this code against the following universal criteria:

## Criteria
{criteria_list}

## Code Diff
{diff_content}

For each criterion, respond in JSON format:
{{
    "evaluations": [
        {{"criterion_id": "id", "passed": true/false, "evidence": "specific line or code reference", "feedback": "brief feedback"}}
    ]
}}"""

        result = self._call_claude(prompt, max_tokens=1000)
        if not result:
            return {"evaluations": []}

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"evaluations": []}

    @traceable(name="evaluate_approach_criteria")
    def _evaluate_approach_criteria(self, diff_content, approach_id, rubric):
        """
        Step 4: Evaluate approach-specific criteria.
        Returns: list of approach-specific evaluations
        """
        approach_criteria = rubric.get('approach_specific_criteria', {}).get(approach_id, [])

        if not approach_criteria:
            return {"evaluations": []}

        criteria_list = "\n".join([
            f"- {c['id']}: {c['criterion']}"
            for c in approach_criteria
        ])

        prompt = f"""Evaluate this code against the {approach_id} approach-specific criteria:

## Criteria
{criteria_list}

## Code Diff
{diff_content}

For each criterion, respond in JSON format:
{{
    "evaluations": [
        {{"criterion_id": "id", "passed": true/false, "evidence": "specific line or code reference", "feedback": "brief feedback"}}
    ]
}}"""

        result = self._call_claude(prompt, max_tokens=800)
        if not result:
            return {"evaluations": []}

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"evaluations": []}

    @traceable(name="evaluate_tests")
    def _evaluate_tests(self, diff_content):
        """
        Step 5: Evaluate test coverage.
        Returns: test coverage assessment
        """
        prompt = f"""Analyze the test coverage in this code diff.

## Code Diff
{diff_content}

Respond in JSON format:
{{
    "has_tests": true/false,
    "test_files": ["list of test files if any"],
    "coverage_assessment": "good/adequate/insufficient/none",
    "tested_scenarios": ["list of what is tested"],
    "missing_tests": ["list of what should be tested"],
    "feedback": "overall test feedback"
}}"""

        result = self._call_claude(prompt, max_tokens=600)
        if not result:
            return {"has_tests": False, "coverage_assessment": "unknown", "feedback": "Unable to analyze"}

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"has_tests": False, "coverage_assessment": "unknown", "feedback": result}

    @traceable(name="analyze_security")
    def _analyze_security(self, diff_content, approach_id):
        """
        Step 6: Security analysis for the chosen approach.
        Returns: security assessment
        """
        prompt = f"""Perform a security analysis of this {approach_id} authentication implementation.

## Code Diff
{diff_content}

Check for common security issues:
- Hardcoded secrets
- Timing attacks (use of == instead of constant-time comparison)
- Information leakage in error messages
- Missing HTTPS enforcement
- Token/key exposure risks

Respond in JSON format:
{{
    "security_score": "good/adequate/needs_improvement/critical",
    "issues": [
        {{"severity": "critical/high/medium/low", "issue": "description", "line_reference": "line number or code", "fix": "suggested fix"}}
    ],
    "best_practices_followed": ["list of good security practices found"],
    "recommendations": ["list of security recommendations"]
}}"""

        result = self._call_claude(prompt, max_tokens=800)
        if not result:
            return {"security_score": "unknown", "issues": [], "recommendations": []}

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"security_score": "unknown", "issues": [], "recommendations": []}

    @traceable(name="generate_alternatives_discussion")
    def _generate_alternatives_discussion(self, approach_id, rubric):
        """
        Step 7: Explain other valid approaches.
        Returns: discussion of alternative approaches
        """
        valid_approaches = rubric.get('valid_approaches', [])
        other_approaches = [a for a in valid_approaches if a['id'] != approach_id]

        if not other_approaches:
            return {"alternatives": []}

        approaches_json = json.dumps(other_approaches, indent=2)

        prompt = f"""The student used the {approach_id} approach. Explain the other valid approaches they could have used.

## Other Valid Approaches
{approaches_json}

For each alternative, provide:
1. Brief explanation of how it would work
2. When you might choose it over the current approach
3. Key tradeoffs

Respond in JSON format:
{{
    "alternatives": [
        {{
            "id": "approach_id",
            "name": "approach name",
            "explanation": "how it works",
            "when_to_use": "scenarios where this is preferred",
            "tradeoffs": {{"pros": ["..."], "cons": ["..."]}}
        }}
    ]
}}"""

        result = self._call_claude(prompt, max_tokens=1000)
        if not result:
            return {"alternatives": []}

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"alternatives": []}

    @traceable(name="synthesize_feedback")
    def _synthesize_feedback(self, approach_detection, architecture, universal_eval,
                             approach_eval, tests_eval, security_analysis, alternatives, rubric):
        """
        Step 8: Consolidate all analysis into final feedback.
        Returns: structured feedback markdown
        """
        approach_id = approach_detection.get('approach_id', 'unknown')
        approach_info = None
        for a in rubric.get('valid_approaches', []):
            if a['id'] == approach_id:
                approach_info = a
                break

        approach_name = approach_info['name'] if approach_info else approach_id

        # Build the feedback markdown
        feedback_parts = []

        # Header
        feedback_parts.append(f"# Code Review: API Authentication\n")
        feedback_parts.append(f"## Your Approach: {approach_name} ✓\n")
        feedback_parts.append(f"You implemented {approach_name.lower()}.")
        if approach_detection.get('reasoning'):
            feedback_parts.append(f" {approach_detection['reasoning']}\n")

        # What You Did Well
        feedback_parts.append("\n## What You Did Well\n")
        passed_criteria = []
        for eval_item in universal_eval.get('evaluations', []):
            if eval_item.get('passed'):
                passed_criteria.append(f"- {eval_item.get('feedback', eval_item.get('criterion_id'))}")
        for eval_item in approach_eval.get('evaluations', []):
            if eval_item.get('passed'):
                passed_criteria.append(f"- {eval_item.get('feedback', eval_item.get('criterion_id'))}")

        if passed_criteria:
            feedback_parts.append("\n".join(passed_criteria))
        else:
            feedback_parts.append("- Good attempt at implementing authentication")

        # Areas for Improvement
        feedback_parts.append("\n\n## Areas for Improvement\n")
        failed_criteria = []
        for eval_item in universal_eval.get('evaluations', []):
            if not eval_item.get('passed'):
                failed_criteria.append(f"- {eval_item.get('feedback', eval_item.get('criterion_id'))}")
        for eval_item in approach_eval.get('evaluations', []):
            if not eval_item.get('passed'):
                failed_criteria.append(f"- {eval_item.get('feedback', eval_item.get('criterion_id'))}")

        if failed_criteria:
            feedback_parts.append("\n".join(failed_criteria))
        else:
            feedback_parts.append("- Your implementation looks good! Consider edge cases.")

        # Security Considerations
        feedback_parts.append("\n\n## Security Considerations\n")
        security_issues = security_analysis.get('issues', [])
        if security_issues:
            for issue in security_issues:
                severity = issue.get('severity', 'medium')
                feedback_parts.append(f"- **[{severity.upper()}]** {issue.get('issue')}")
                if issue.get('fix'):
                    feedback_parts.append(f"  - Fix: {issue['fix']}")
        else:
            feedback_parts.append("- No critical security issues found")

        if security_analysis.get('recommendations'):
            feedback_parts.append("\n**Recommendations:**")
            for rec in security_analysis['recommendations']:
                feedback_parts.append(f"- {rec}")

        # Test Coverage
        if tests_eval.get('feedback'):
            feedback_parts.append(f"\n\n## Test Coverage\n")
            feedback_parts.append(tests_eval['feedback'])
            if tests_eval.get('missing_tests'):
                feedback_parts.append("\n**Consider adding tests for:**")
                for test in tests_eval['missing_tests']:
                    feedback_parts.append(f"- {test}")

        # Other Valid Approaches
        feedback_parts.append("\n\n---\n\n## Other Valid Approaches\n")
        alternatives_list = alternatives.get('alternatives', [])
        if alternatives_list:
            for alt in alternatives_list:
                feedback_parts.append(f"\n### {alt.get('name', alt.get('id'))}\n")
                feedback_parts.append(alt.get('explanation', ''))
                if alt.get('when_to_use'):
                    feedback_parts.append(f"\n**When to use:** {alt['when_to_use']}")
                tradeoffs = alt.get('tradeoffs', {})
                if tradeoffs.get('pros') or tradeoffs.get('cons'):
                    feedback_parts.append("\n**Tradeoffs:**")
                    if tradeoffs.get('pros'):
                        feedback_parts.append(f"- Pros: {', '.join(tradeoffs['pros'])}")
                    if tradeoffs.get('cons'):
                        feedback_parts.append(f"- Cons: {', '.join(tradeoffs['cons'])}")
        else:
            feedback_parts.append("This challenge supports multiple valid approaches including API Key, HTTP Basic Auth, and JWT.")

        # Key Learning Points
        feedback_parts.append("\n\n---\n\n## Key Learning Points\n")
        feedback_parts.append("1. Authentication protects sensitive endpoints while keeping read operations accessible")
        feedback_parts.append("2. The decorator pattern provides clean, reusable authentication logic")
        feedback_parts.append("3. Different auth approaches have different tradeoffs - choose based on your use case")

        return "\n".join(feedback_parts)

    @traceable(name="run_full_review")
    def run_full_review(self, challenge_md, diff_content, rubric):
        """
        Run the complete agentic review pipeline.

        Returns:
            dict with keys: content, detected_approach, evaluation, alternatives, line_references
        """
        if not self.api_key:
            return {
                'content': self._get_demo_feedback(),
                'detected_approach': None,
                'evaluation': None,
                'alternatives': None,
                'line_references': None
            }

        # Step 1: Detect approach
        approach_detection = self._detect_approach(diff_content, rubric)
        approach_id = approach_detection.get('approach_id', 'unknown')

        # Step 2: Analyze architecture
        architecture = self._analyze_architecture(diff_content)

        # Step 3: Evaluate universal criteria
        universal_eval = self._evaluate_universal_criteria(diff_content, rubric)

        # Step 4: Evaluate approach-specific criteria
        approach_eval = self._evaluate_approach_criteria(diff_content, approach_id, rubric)

        # Step 5: Evaluate tests
        tests_eval = self._evaluate_tests(diff_content)

        # Step 6: Security analysis
        security_analysis = self._analyze_security(diff_content, approach_id)

        # Step 7: Generate alternatives discussion
        alternatives = self._generate_alternatives_discussion(approach_id, rubric)

        # Step 8: Synthesize feedback
        content = self._synthesize_feedback(
            approach_detection, architecture, universal_eval,
            approach_eval, tests_eval, security_analysis, alternatives, rubric
        )

        # Compile line references from all analyses
        line_references = []
        for eval_item in universal_eval.get('evaluations', []):
            if eval_item.get('evidence'):
                line_references.append({
                    'criterion': eval_item.get('criterion_id'),
                    'reference': eval_item.get('evidence')
                })
        for issue in security_analysis.get('issues', []):
            if issue.get('line_reference'):
                line_references.append({
                    'type': 'security',
                    'severity': issue.get('severity'),
                    'reference': issue.get('line_reference')
                })

        return {
            'content': content,
            'detected_approach': approach_id,
            'evaluation': {
                'approach_detection': approach_detection,
                'architecture': architecture,
                'universal_criteria': universal_eval,
                'approach_criteria': approach_eval,
                'tests': tests_eval,
                'security': security_analysis
            },
            'alternatives': alternatives,
            'line_references': line_references
        }

    def _get_demo_feedback(self):
        """Return demo feedback when no API key is configured."""
        return """**AI Feedback (Demo Mode)**

No Anthropic API key configured. In production, the agentic review would provide:

1. **Approach Detection** - Automatically identify whether you used API Key, HTTP Basic Auth, or JWT
2. **Architecture Analysis** - Map your code components and structure
3. **Criteria Evaluation** - Check against universal and approach-specific rubric criteria
4. **Test Coverage** - Assess your test coverage
5. **Security Analysis** - Identify security issues specific to your chosen approach
6. **Alternatives Discussion** - Compare your approach to other valid solutions

To enable full agentic review, set the ANTHROPIC_API_KEY environment variable."""
