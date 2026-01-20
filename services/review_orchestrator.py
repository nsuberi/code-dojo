"""LangGraph orchestrator for AI code review with architectural analysis.

Coordinates multiple analysis steps using LangGraph state machine with parallel execution.
"""

from typing import TypedDict, Optional, Dict, List, Annotated
from datetime import datetime
import traceback

# LangGraph imports - optional dependency
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

# LangSmith tracing
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

from services.agentic_review import AgenticReviewService
from services.architectural_analyzer import ArchitecturalAnalyzer
from services.diagram_generator import DiagramGenerator
from models import db
from models.ai_feedback import AIFeedback
from models.architectural_analysis import ArchitecturalAnalysis
from config import Config


class ReviewState(TypedDict):
    """State schema for the review workflow."""
    # Input
    submission_id: int
    challenge_md: str
    diff_content: str
    rubric: Optional[Dict]

    # PR data (optional, for enhanced analysis)
    pr_metadata: Optional[Dict]
    pr_files: Optional[List[Dict]]

    # Analysis results
    approach_detection: Optional[Dict]
    architecture_basic: Optional[Dict]  # From existing agentic review
    universal_eval: Optional[Dict]
    approach_eval: Optional[Dict]
    tests_eval: Optional[Dict]
    security_analysis: Optional[Dict]
    alternatives: Optional[Dict]

    # NEW - Architectural analysis
    arch_components: Optional[Dict]
    arch_dependencies: Optional[Dict]
    arch_api_changes: Optional[Dict]
    arch_schema_changes: Optional[Dict]
    arch_impact: Optional[Dict]
    arch_diagrams: Optional[Dict[str, str]]

    # Progress tracking
    progress_events: List[Dict]

    # Output
    final_content: str
    errors: List[str]
    analysis_path: str  # 'simple' or 'enhanced'


def create_review_graph():
    """Create the LangGraph state machine for code review."""
    if not LANGGRAPH_AVAILABLE:
        return None

    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("initialize", initialize_review)
    workflow.add_node("route_analysis", route_analysis_type)
    workflow.add_node("run_basic_review", run_basic_review)
    workflow.add_node("run_arch_analysis", run_architectural_analysis)
    workflow.add_node("enrich_feedback", enrich_with_architecture)
    workflow.add_node("synthesize", synthesize_final_feedback)
    workflow.add_node("save_results", save_review_results)

    # Define the flow
    workflow.set_entry_point("initialize")

    # Initialize -> Route
    workflow.add_edge("initialize", "route_analysis")

    # Route -> Either basic review only or both
    workflow.add_conditional_edges(
        "route_analysis",
        route_decision,
        {
            "simple": "run_basic_review",
            "enhanced": "run_basic_review"  # Both paths run basic review
        }
    )

    # After basic review, check if we need arch analysis
    workflow.add_conditional_edges(
        "run_basic_review",
        check_for_arch_analysis,
        {
            "simple": "synthesize",      # Skip arch analysis
            "enhanced": "run_arch_analysis"  # Run arch analysis
        }
    )

    # Arch analysis -> Enrich -> Synthesize
    workflow.add_edge("run_arch_analysis", "enrich_feedback")
    workflow.add_edge("enrich_feedback", "synthesize")

    # Synthesize -> Save -> END
    workflow.add_edge("synthesize", "save_results")
    workflow.add_edge("save_results", END)

    # Compile the graph
    return workflow.compile()


# Node implementations

@traceable(name="initialize_review")
def initialize_review(state: ReviewState) -> ReviewState:
    """Initialize the review workflow."""
    state['errors'] = state.get('errors', [])
    state['analysis_path'] = 'enhanced'  # Default to enhanced if PR metadata available

    # Determine if we can do enhanced analysis
    has_pr_metadata = bool(state.get('pr_metadata'))
    has_rubric = bool(state.get('rubric'))

    if not has_pr_metadata:
        state['analysis_path'] = 'simple'

    return state


@traceable(name="route_analysis")
def route_analysis_type(state: ReviewState) -> ReviewState:
    """Determine which analysis path to take."""
    # Check if we should skip arch analysis
    if not Config.ARCH_ANALYSIS_ENABLED:
        state['analysis_path'] = 'simple'
        return state

    # Check if PR is small and we should skip
    if Config.ARCH_SKIP_SMALL_PRS:
        pr_files = state.get('pr_files', [])
        if pr_files and len(pr_files) < 5:
            state['analysis_path'] = 'simple'
            return state

    # Keep existing path determination
    return state


def route_decision(state: ReviewState) -> str:
    """Conditional edge function for routing."""
    return state.get('analysis_path', 'simple')


@traceable(name="run_basic_review")
def run_basic_review(state: ReviewState) -> ReviewState:
    """Run the existing agentic review pipeline."""
    try:
        submission_id = state['submission_id']
        service = AgenticReviewService(submission_id)

        # Initialize progress_events in state if not exists
        if 'progress_events' not in state:
            state['progress_events'] = []

        # Run individual steps
        diff_content = state['diff_content']
        rubric = state['rubric']

        if not rubric:
            # No rubric - return simple feedback
            state['final_content'] = "No rubric available for detailed review."
            state['analysis_path'] = 'simple'
            return state

        # Create callback that translates sub-progress to overall progress
        # base_progress: 5% (initialize) + 3% (route_analysis) = 8%
        base_progress = 8
        basic_review_weight = 50

        def sub_progress_callback(step, description, sub_progress_pct):
            """Translate sub-step progress to overall progress."""
            overall_progress = base_progress + (sub_progress_pct / 100.0 * basic_review_weight)

            state['progress_events'].append({
                'step': step,
                'description': description,
                'progress': int(overall_progress),
                'status': 'running'
            })

        # Run the full review with progress callback
        result = service.run_full_review(
            challenge_md=state['challenge_md'],
            diff_content=diff_content,
            rubric=rubric,
            progress_callback=sub_progress_callback
        )

        # Extract results into state
        state['approach_detection'] = result.get('evaluation', {}).get('approach_detection', {})
        state['architecture_basic'] = result.get('evaluation', {}).get('architecture', {})
        state['universal_eval'] = result.get('evaluation', {}).get('universal_criteria', {})
        state['approach_eval'] = result.get('evaluation', {}).get('approach_criteria', {})
        state['tests_eval'] = result.get('evaluation', {}).get('tests', {})
        state['security_analysis'] = result.get('evaluation', {}).get('security', {})
        state['alternatives'] = result.get('alternatives', {})

    except Exception as e:
        state['errors'].append(f"Basic review error: {str(e)}")
        traceback.print_exc()

    return state


def check_for_arch_analysis(state: ReviewState) -> str:
    """Check if we should run architectural analysis."""
    return state.get('analysis_path', 'simple')


@traceable(name="run_architectural_analysis")
def run_architectural_analysis(state: ReviewState) -> ReviewState:
    """Run enhanced architectural analysis."""
    try:
        analyzer = ArchitecturalAnalyzer()
        diagram_gen = DiagramGenerator()

        # Get PR files if available
        pr_files = state.get('pr_files')
        diff_content = state['diff_content']

        # Run analysis
        analysis_results = analyzer.analyze_pr_diff(diff_content, pr_files)

        # Extract results
        state['arch_components'] = analysis_results.get('components', {})
        state['arch_dependencies'] = analysis_results.get('dependencies', {})
        state['arch_api_changes'] = analysis_results.get('api_changes', {})
        state['arch_schema_changes'] = analysis_results.get('schema_changes', {})
        state['arch_impact'] = analysis_results.get('impact', {})

        # Generate diagrams
        diagrams = diagram_gen.generate_all_diagrams(analysis_results)
        state['arch_diagrams'] = diagrams

    except Exception as e:
        state['errors'].append(f"Architectural analysis error: {str(e)}")
        traceback.print_exc()
        # Continue even if arch analysis fails
        state['analysis_path'] = 'simple'

    return state


@traceable(name="enrich_with_architecture")
def enrich_with_architecture(state: ReviewState) -> ReviewState:
    """Enrich the basic review with architectural insights."""
    # Architectural insights are already in state
    # This node is a placeholder for future enrichment logic
    # (e.g., cross-referencing security issues with API changes)
    return state


@traceable(name="synthesize_feedback")
def synthesize_final_feedback(state: ReviewState) -> ReviewState:
    """Synthesize all analysis into final markdown feedback."""
    try:
        # Start with existing synthesis
        service = AgenticReviewService(state['submission_id'])

        base_feedback = service._synthesize_feedback(
            state.get('approach_detection', {}),
            state.get('architecture_basic', {}),
            state.get('universal_eval', {}),
            state.get('approach_eval', {}),
            state.get('tests_eval', {}),
            state.get('security_analysis', {}),
            state.get('alternatives', {}),
            state.get('rubric', {})
        )

        # Add architectural sections if enhanced path
        if state.get('analysis_path') == 'enhanced' and state.get('arch_impact'):
            arch_sections = _generate_architectural_sections(state)
            # Insert architectural sections after the main review
            insertion_point = base_feedback.find("\n\n---\n\n## Other Valid Approaches")
            if insertion_point > 0:
                base_feedback = (
                    base_feedback[:insertion_point] +
                    "\n\n" + arch_sections +
                    base_feedback[insertion_point:]
                )
            else:
                base_feedback += "\n\n" + arch_sections

        state['final_content'] = base_feedback

    except Exception as e:
        state['errors'].append(f"Synthesis error: {str(e)}")
        traceback.print_exc()
        state['final_content'] = "Error generating feedback. Please try again."

    return state


def _generate_architectural_sections(state: ReviewState) -> str:
    """Generate markdown sections for architectural analysis."""
    sections = []

    # Impact Assessment
    impact = state.get('arch_impact', {})
    if impact:
        sections.append("---\n\n## Architectural Overview 🏗️")
        sections.append("\n**Impact Assessment:**")
        sections.append(f"- **Scope:** {impact.get('scope', 'unknown').title()} ({len(impact.get('components_affected', []))} components)")
        sections.append(f"- **Risk:** {impact.get('risk', 'unknown').title()}")
        sections.append(f"- **Complexity:** {impact.get('complexity', 'unknown').title()} ({impact.get('files_changed', 0)} files, {impact.get('lines_added', 0)}+ / {impact.get('lines_removed', 0)}- lines)")

        if impact.get('risk_factors'):
            sections.append("\n**Risk Factors:**")
            for factor in impact['risk_factors']:
                sections.append(f"- {factor}")

    # Component Changes
    components = state.get('arch_components', {})
    if components:
        sections.append("\n\n**Components Modified:**")
        for comp_name, comp_data in list(components.items())[:5]:  # Limit to 5
            comp_type = comp_data.get('type', 'module')
            file_count = comp_data.get('file_count', 0)
            sections.append(f"- **{comp_name}** ({comp_type}): {file_count} file(s)")

    # Impact diagram
    diagrams = state.get('arch_diagrams', {})
    if diagrams.get('impact'):
        sections.append("\n\n```mermaid")
        sections.append(diagrams['impact'])
        sections.append("```")

    # API Changes
    api_changes = state.get('arch_api_changes', {})
    if api_changes and api_changes.get('summary', {}).get('added', 0) > 0:
        sections.append("\n\n## API Changes 🔌")

        new_endpoints = api_changes.get('new_endpoints', [])
        if new_endpoints:
            sections.append("\n**New Endpoints:**")
            for endpoint in new_endpoints[:8]:
                sections.append(f"- `{endpoint['method']} {endpoint['path']}` in `{endpoint['file']}`")

        removed_endpoints = api_changes.get('removed_endpoints', [])
        if removed_endpoints:
            sections.append("\n**Removed Endpoints:**")
            for endpoint in removed_endpoints[:8]:
                sections.append(f"- `{endpoint['method']} {endpoint['path']}` in `{endpoint['file']}`")

        if diagrams.get('api_surface'):
            sections.append("\n\n```mermaid")
            sections.append(diagrams['api_surface'])
            sections.append("```")

    # Database Schema Changes
    schema_changes = state.get('arch_schema_changes', {})
    if schema_changes and schema_changes.get('summary', {}).get('migrations', 0) > 0:
        sections.append("\n\n## Database Schema Changes 🗄️")

        migration_files = schema_changes.get('migration_files', [])
        if migration_files:
            sections.append("\n**Migration Files:**")
            for migration in migration_files:
                sections.append(f"- `{migration}`")

        new_models = schema_changes.get('new_models', [])
        if new_models:
            sections.append("\n**New Models:**")
            for model in new_models:
                sections.append(f"- **{model['name']}** → `{model['table']}`")

        if schema_changes.get('breaking_changes'):
            sections.append("\n**⚠️ Potential Breaking Changes:**")
            for change in schema_changes['breaking_changes']:
                sections.append(f"- {change}")

    # Dependency Changes
    dependencies = state.get('arch_dependencies', {})
    if dependencies and (dependencies.get('added') or dependencies.get('removed')):
        sections.append("\n\n## Dependency Changes 📦")

        added = dependencies.get('added', [])
        if added:
            sections.append("\n**New Dependencies:**")
            for dep in added[:10]:
                sections.append(f"- `{dep}`")

        removed = dependencies.get('removed', [])
        if removed:
            sections.append("\n**Removed Dependencies:**")
            for dep in removed[:10]:
                sections.append(f"- `{dep}`")

        if diagrams.get('dependency'):
            sections.append("\n\n```mermaid")
            sections.append(diagrams['dependency'])
            sections.append("```")

    return "\n".join(sections)


@traceable(name="save_results")
def save_review_results(state: ReviewState) -> ReviewState:
    """Save the review results to the database."""
    try:
        submission_id = state['submission_id']

        # Save AI feedback
        ai_feedback = AIFeedback.query.filter_by(submission_id=submission_id).first()
        if not ai_feedback:
            ai_feedback = AIFeedback(submission_id=submission_id)

        ai_feedback.content = state.get('final_content', '')
        ai_feedback.detected_approach = state.get('approach_detection', {}).get('approach_id')

        # Set evaluation JSON
        evaluation_data = {
            'approach_detection': state.get('approach_detection'),
            'architecture': state.get('architecture_basic'),
            'universal_criteria': state.get('universal_eval'),
            'approach_criteria': state.get('approach_eval'),
            'tests': state.get('tests_eval'),
            'security': state.get('security_analysis')
        }
        ai_feedback.set_evaluation(evaluation_data)
        ai_feedback.set_alternative_approaches(state.get('alternatives', {}))

        # Compile line references
        line_references = []
        for eval_item in state.get('universal_eval', {}).get('evaluations', []):
            if eval_item.get('evidence'):
                line_references.append({
                    'criterion': eval_item.get('criterion_id'),
                    'reference': eval_item.get('evidence')
                })
        ai_feedback.set_line_references(line_references)

        db.session.add(ai_feedback)

        # Save architectural analysis if enhanced path
        if state.get('analysis_path') == 'enhanced' and state.get('arch_impact'):
            arch_analysis = ArchitecturalAnalysis.query.filter_by(submission_id=submission_id).first()
            if not arch_analysis:
                arch_analysis = ArchitecturalAnalysis(submission_id=submission_id)

            # Set structured data
            arch_analysis.set_components(state.get('arch_components', {}))
            arch_analysis.set_dependencies_diff(state.get('arch_dependencies', {}))
            arch_analysis.set_api_changes(state.get('arch_api_changes', {}))
            arch_analysis.set_schema_changes(state.get('arch_schema_changes', {}))

            # Set impact scores
            impact = state.get('arch_impact', {})
            arch_analysis.scope_score = impact.get('scope')
            arch_analysis.risk_score = impact.get('risk')
            arch_analysis.complexity_score = impact.get('complexity')
            arch_analysis.files_changed = impact.get('files_changed', 0)
            arch_analysis.lines_added = impact.get('lines_added', 0)
            arch_analysis.lines_removed = impact.get('lines_removed', 0)

            # Set diagrams
            diagrams = state.get('arch_diagrams', {})
            arch_analysis.component_diagram = diagrams.get('component')
            arch_analysis.dataflow_diagram = diagrams.get('dataflow')
            arch_analysis.dependency_diagram = diagrams.get('dependency')

            db.session.add(arch_analysis)

        db.session.commit()

    except Exception as e:
        state['errors'].append(f"Save error: {str(e)}")
        traceback.print_exc()
        db.session.rollback()

    return state


# Main orchestration function

@traceable(name="orchestrate_review")
def orchestrate_review_streaming(submission_id: int, challenge_md: str, diff_content: str,
                                  rubric: Optional[Dict] = None, pr_metadata: Optional[Dict] = None,
                                  pr_files: Optional[List[Dict]] = None, progress_callback=None) -> Dict:
    """
    Orchestrate the complete review workflow using LangGraph with real-time progress updates.

    Args:
        submission_id: Submission ID
        challenge_md: Challenge description
        diff_content: Unified diff content
        rubric: Challenge rubric dictionary
        pr_metadata: Optional PR metadata from GitHub API
        pr_files: Optional list of file changes from GitHub API
        progress_callback: Function called with progress events
            Event format: {"step": str, "description": str, "progress": int, "status": str}

    Returns:
        Dict with review results (same format as AgenticReviewService.run_full_review)
    """
    # Fallback if LangGraph not available
    if not LANGGRAPH_AVAILABLE:
        service = AgenticReviewService(submission_id)
        return service.run_full_review(challenge_md, diff_content, rubric)

    # Define step metadata for user-friendly display
    step_metadata = {
        "initialize": {"description": "Setting up analysis", "weight": 5},
        "route_analysis": {"description": "Determining analysis path", "weight": 3},
        "run_basic_review": {"description": "Running core analysis", "weight": 50},
        "run_arch_analysis": {"description": "Analyzing architecture", "weight": 20},
        "enrich_feedback": {"description": "Cross-referencing insights", "weight": 7},
        "synthesize": {"description": "Creating feedback", "weight": 10},
        "save_results": {"description": "Saving results", "weight": 5}
    }

    total_weight = sum(meta["weight"] for meta in step_metadata.values())
    current_progress = 0

    # Create initial state
    initial_state = ReviewState(
        submission_id=submission_id,
        challenge_md=challenge_md,
        diff_content=diff_content,
        rubric=rubric,
        pr_metadata=pr_metadata,
        pr_files=pr_files,
        errors=[],
        final_content="",
        analysis_path="enhanced"
    )

    # Create and run the graph with streaming
    try:
        graph = create_review_graph()
        final_state = None

        # Stream events
        for event in graph.stream(initial_state, stream_mode="updates"):
            node_name = list(event.keys())[0]  # Node that just executed

            if node_name in step_metadata:
                meta = step_metadata[node_name]
                current_progress += meta["weight"]

                if progress_callback:
                    progress_callback({
                        "step": node_name,
                        "description": meta["description"],
                        "progress": int((current_progress / total_weight) * 100),
                        "status": "running"
                    })

            # Capture final state from the last event
            final_state = event[node_name]

        # Send completion event
        if progress_callback:
            progress_callback({
                "step": "complete",
                "description": "Analysis complete",
                "progress": 100,
                "status": "complete"
            })

        # Return in expected format
        if final_state:
            return {
                'content': final_state.get('final_content', ''),
                'detected_approach': final_state.get('approach_detection', {}).get('approach_id'),
                'evaluation': {
                    'approach_detection': final_state.get('approach_detection'),
                    'architecture': final_state.get('architecture_basic'),
                    'universal_criteria': final_state.get('universal_eval'),
                    'approach_criteria': final_state.get('approach_eval'),
                    'tests': final_state.get('tests_eval'),
                    'security': final_state.get('security_analysis'),
                    'arch_analysis': {
                        'components': final_state.get('arch_components'),
                        'dependencies': final_state.get('arch_dependencies'),
                        'api_changes': final_state.get('arch_api_changes'),
                        'schema_changes': final_state.get('arch_schema_changes'),
                        'impact': final_state.get('arch_impact'),
                    }
                },
                'alternatives': final_state.get('alternatives'),
                'line_references': [],
                'errors': final_state.get('errors', [])
            }

    except Exception as e:
        # Send error event
        if progress_callback:
            progress_callback({
                "step": "error",
                "description": f"Error: {str(e)}",
                "progress": 0,
                "status": "error"
            })

        # Fallback to basic review on error
        print(f"LangGraph streaming error: {e}")
        traceback.print_exc()
        service = AgenticReviewService(submission_id)
        return service.run_full_review(challenge_md, diff_content, rubric)


def orchestrate_review_streaming_generator(submission_id: int, challenge_md: str, diff_content: str,
                                            rubric: Optional[Dict] = None, pr_metadata: Optional[Dict] = None,
                                            pr_files: Optional[List[Dict]] = None):
    """
    Generator version of orchestrate_review_streaming for use with SSE.

    Yields progress events as {"step": str, "description": str, "progress": int, "status": str}
    Final yield is the complete result dict.
    """
    # Fallback if LangGraph not available
    if not LANGGRAPH_AVAILABLE:
        service = AgenticReviewService(submission_id)
        result = service.run_full_review(challenge_md, diff_content, rubric)
        yield {"step": "complete", "description": "Analysis complete", "progress": 100, "status": "complete"}
        yield ("RESULT", result)
        return

    # Define step metadata
    step_metadata = {
        "initialize": {"description": "Setting up analysis", "weight": 5},
        "route_analysis": {"description": "Determining analysis path", "weight": 3},
        "run_basic_review": {"description": "Running core analysis", "weight": 50},
        "run_arch_analysis": {"description": "Analyzing architecture", "weight": 20},
        "enrich_feedback": {"description": "Cross-referencing insights", "weight": 7},
        "synthesize": {"description": "Creating feedback", "weight": 10},
        "save_results": {"description": "Saving results", "weight": 5}
    }

    total_weight = sum(meta["weight"] for meta in step_metadata.values())
    current_progress = 0

    # Create initial state with progress_events
    initial_state = ReviewState(
        submission_id=submission_id,
        challenge_md=challenge_md,
        diff_content=diff_content,
        rubric=rubric,
        pr_metadata=pr_metadata,
        pr_files=pr_files,
        errors=[],
        final_content="",
        analysis_path="enhanced",
        progress_events=[]
    )

    try:
        graph = create_review_graph()
        final_state = None
        last_emitted_event_count = 0

        # Stream events and yield progress
        for event in graph.stream(initial_state, stream_mode="updates"):
            node_name = list(event.keys())[0]
            node_state = event[node_name]

            # Emit high-level node progress
            if node_name in step_metadata:
                meta = step_metadata[node_name]
                current_progress += meta["weight"]

                yield {
                    "step": node_name,
                    "description": meta["description"],
                    "progress": int((current_progress / total_weight) * 100),
                    "status": "running"
                }

            # NEW: Emit sub-step events from progress_events
            if 'progress_events' in node_state:
                new_events = node_state['progress_events'][last_emitted_event_count:]
                for sub_event in new_events:
                    yield sub_event
                last_emitted_event_count = len(node_state['progress_events'])

            final_state = node_state

        # Send completion
        yield {"step": "complete", "description": "Analysis complete", "progress": 100, "status": "complete"}

        # Yield final result
        if final_state:
            result = {
                'content': final_state.get('final_content', ''),
                'detected_approach': final_state.get('approach_detection', {}).get('approach_id'),
                'evaluation': {
                    'approach_detection': final_state.get('approach_detection'),
                    'architecture': final_state.get('architecture_basic'),
                    'universal_criteria': final_state.get('universal_eval'),
                    'approach_criteria': final_state.get('approach_eval'),
                    'tests': final_state.get('tests_eval'),
                    'security': final_state.get('security_analysis'),
                    'arch_analysis': {
                        'components': final_state.get('arch_components'),
                        'dependencies': final_state.get('arch_dependencies'),
                        'api_changes': final_state.get('arch_api_changes'),
                        'schema_changes': final_state.get('arch_schema_changes'),
                        'impact': final_state.get('arch_impact'),
                    }
                },
                'alternatives': final_state.get('alternatives'),
                'line_references': [],
                'errors': final_state.get('errors', [])
            }
            yield ("RESULT", result)

    except Exception as e:
        yield {"step": "error", "description": f"Error: {str(e)}", "progress": 0, "status": "error"}
        # Fallback
        service = AgenticReviewService(submission_id)
        result = service.run_full_review(challenge_md, diff_content, rubric)
        yield ("RESULT", result)


def orchestrate_review(submission_id: int, challenge_md: str, diff_content: str,
                       rubric: Optional[Dict] = None, pr_metadata: Optional[Dict] = None,
                       pr_files: Optional[List[Dict]] = None) -> Dict:
    """
    Orchestrate the complete review workflow using LangGraph.

    Args:
        submission_id: Submission ID
        challenge_md: Challenge description
        diff_content: Unified diff content
        rubric: Challenge rubric dictionary
        pr_metadata: Optional PR metadata from GitHub API
        pr_files: Optional list of file changes from GitHub API

    Returns:
        Dict with review results (same format as AgenticReviewService.run_full_review)
    """
    # Fallback if LangGraph not available
    if not LANGGRAPH_AVAILABLE:
        service = AgenticReviewService(submission_id)
        return service.run_full_review(challenge_md, diff_content, rubric)

    # Create initial state
    initial_state = ReviewState(
        submission_id=submission_id,
        challenge_md=challenge_md,
        diff_content=diff_content,
        rubric=rubric,
        pr_metadata=pr_metadata,
        pr_files=pr_files,
        errors=[],
        final_content="",
        analysis_path="enhanced"
    )

    # Create and run the graph
    try:
        graph = create_review_graph()
        final_state = graph.invoke(initial_state)

        # Return in expected format
        return {
            'content': final_state.get('final_content', ''),
            'detected_approach': final_state.get('approach_detection', {}).get('approach_id'),
            'evaluation': {
                'approach_detection': final_state.get('approach_detection'),
                'architecture': final_state.get('architecture_basic'),
                'universal_criteria': final_state.get('universal_eval'),
                'approach_criteria': final_state.get('approach_eval'),
                'tests': final_state.get('tests_eval'),
                'security': final_state.get('security_analysis'),
                'arch_analysis': {
                    'components': final_state.get('arch_components'),
                    'dependencies': final_state.get('arch_dependencies'),
                    'api_changes': final_state.get('arch_api_changes'),
                    'schema_changes': final_state.get('arch_schema_changes'),
                    'impact': final_state.get('arch_impact'),
                }
            },
            'alternatives': final_state.get('alternatives'),
            'line_references': [],
            'errors': final_state.get('errors', [])
        }

    except Exception as e:
        # Fallback to basic review on error
        print(f"LangGraph orchestration error: {e}")
        traceback.print_exc()
        service = AgenticReviewService(submission_id)
        return service.run_full_review(challenge_md, diff_content, rubric)
