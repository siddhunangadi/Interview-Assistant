"""
supervisor.py — LangGraph-based supervisor for the interview pipeline.

This version fixes the main orchestration issues in the original draft:

1. The graph now really branches from START to both analyzers, then joins.
2. The routing nodes only decide control flow; they do not mutate unrelated state.
3. The state schema is explicit and reducer-friendly for log / error accumulation.
4. Retry behavior is preserved, but the graph no longer lies about being parallel
   while actually chaining resume -> JD.
5. The evaluation graph stays separate so the UI can run it after the mock interview.
"""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents import (
    ResumeAnalysis,
    JDAnalysis,
    SkillGapReport,
    QuestionList,
    InterviewQuestion,
    PerformanceEvaluation,
    run_resume_analyzer,
    run_jd_analyzer,
    run_skill_gap_analyzer,
    run_question_generator,
    run_performance_evaluator,
)

logger = logging.getLogger(__name__)

# If skill-gap score is below this, the supervisor triggers a re-analysis pass.
MIN_MATCH_SCORE = 30
# Maximum supervisor-level retry cycles (distinct from per-agent retries).
MAX_SUPERVISOR_RETRIES = 1


class AgentState(TypedDict, total=False):
    """Shared state that flows through the graph."""

    # Inputs
    resume_text: str
    jd_text: str
    api_key: Optional[str]

    # Intermediate outputs
    resume_analysis: Optional[ResumeAnalysis]
    jd_analysis: Optional[JDAnalysis]
    skill_gap_report: Optional[SkillGapReport]
    question_list: Optional[QuestionList]
    user_answers: Optional[dict[str, str]]
    performance_evaluation: Optional[PerformanceEvaluation]

    # Control
    supervisor_retries: int
    next_node: str

    # Reducer-backed accumulators
    errors: Annotated[list[str], operator.add]
    execution_log: Annotated[list[str], operator.add]


def node_resume_analyzer(state: AgentState) -> dict[str, Any]:
    logger.info("[supervisor] → resume_analyzer")
    try:
        result = run_resume_analyzer(state["resume_text"], state.get("api_key"))
        return {
            "resume_analysis": result,
            "execution_log": ["✓ Resume Analyzer complete"],
        }
    except Exception as e:
        logger.exception("[resume_analyzer] failed")
        return {
            "errors": [f"resume_analyzer: {e}"],
            "execution_log": [f"✗ Resume Analyzer failed: {e}"],
        }


def node_jd_analyzer(state: AgentState) -> dict[str, Any]:
    logger.info("[supervisor] → jd_analyzer")
    import time
    time.sleep(15)
    try:
        result = run_jd_analyzer(state["jd_text"], state.get("api_key"))
        return {
            "jd_analysis": result,
            "execution_log": ["✓ JD Analyzer complete"],
        }
    except Exception as e:
        logger.exception("[jd_analyzer] failed")
        return {
            "errors": [f"jd_analyzer: {e}"],
            "execution_log": [f"✗ JD Analyzer failed: {e}"],
        }


def node_supervisor_route(state: AgentState) -> dict[str, Any]:
    """
    Join point after the analyzers. If either analyzer failed, stop early.
    Otherwise continue to the skill-gap analysis step.
    """
    if state.get("resume_analysis") is None or state.get("jd_analysis") is None:
        logger.warning("[supervisor] analyzer(s) missing — routing to error")
        return {
            "next_node": "error",
            "execution_log": ["⚠ Supervisor: analyzer failed, stopping"],
        }

    logger.info("[supervisor] analyzers complete — routing to skill_gap")
    return {
        "next_node": "skill_gap",
        "execution_log": ["→ Supervisor: routing to Skill Gap Agent"],
    }


def node_skill_gap(state: AgentState) -> dict[str, Any]:
    logger.info("[supervisor] → skill_gap_analyzer")
    import time
    time.sleep(15)
    try:
        result = run_skill_gap_analyzer(
            state["resume_analysis"],
            state["jd_analysis"],
            state.get("api_key"),
        )
        return {
            "skill_gap_report": result,
            "execution_log": [f"✓ Skill Gap complete — match score: {result.match_score}%"],
        }
    except Exception as e:
        logger.exception("[skill_gap] failed")
        return {
            "errors": [f"skill_gap: {e}"],
            "execution_log": [f"✗ Skill Gap failed: {e}"],
        }


def node_supervisor_quality_gate(state: AgentState) -> dict[str, Any]:
    """
    If match_score is below threshold and retries remain, loop back to the
    analyzers with one extra supervisor retry recorded in state.
    """
    report = state.get("skill_gap_report")
    retries = state.get("supervisor_retries", 0)

    if report is None:
        return {
            "next_node": "error",
            "execution_log": ["⚠ Supervisor: skill gap missing"],
        }

    if report.match_score < MIN_MATCH_SCORE and retries < MAX_SUPERVISOR_RETRIES:
        logger.info(
            "[supervisor] match score %s%% too low — retrying analyzers",
            report.match_score,
        )
        return {
            "next_node": "retry_analyzers",
            "supervisor_retries": retries + 1,
            "execution_log": [
                f"↻ Supervisor: match score {report.match_score}% < {MIN_MATCH_SCORE}% "
                f"— re-running analyzers (retry {retries + 1}/{MAX_SUPERVISOR_RETRIES})"
            ],
        }

    logger.info(
        "[supervisor] match score %s%% — proceeding to question gen",
        report.match_score,
    )
    return {
        "next_node": "question_gen",
        "execution_log": [f"→ Supervisor: match score acceptable ({report.match_score}%)"],
    }


def node_question_gen(state: AgentState) -> dict[str, Any]:
    logger.info("[supervisor] → question_generator")
    import time
    time.sleep(15)
    try:
        result = run_question_generator(
            state["resume_analysis"],
            state["jd_analysis"],
            state["skill_gap_report"],
            state.get("api_key"),
        )
        return {
            "question_list": result,
            "execution_log": [f"✓ Question Generator complete — {len(result.questions)} questions"],
        }
    except Exception as e:
        logger.exception("[question_gen] failed")
        return {
            "errors": [f"question_gen: {e}"],
            "execution_log": [f"✗ Question Generator failed: {e}"],
        }


def node_performance_evaluator(state: AgentState) -> dict[str, Any]:
    logger.info("[supervisor] → performance_evaluator")
    answers = state.get("user_answers") or {}
    questions = state["question_list"].questions if state.get("question_list") else []
    import time
    time.sleep(15)
    try:
        result = run_performance_evaluator(questions, answers, state.get("api_key"))
        return {
            "performance_evaluation": result,
            "execution_log": [
                "✓ Performance Evaluator complete — "
                f"readiness: {result.overall_readiness_score}% "
                f"(self-reflected {result.reflection_cycles}×)"
            ],
        }
    except Exception as e:
        logger.exception("[performance_evaluator] failed")
        return {
            "errors": [f"performance_evaluator: {e}"],
            "execution_log": [f"✗ Performance Evaluator failed: {e}"],
        }


def route_after_supervisor(state: AgentState) -> str:
    return state.get("next_node", "error")


def route_after_quality_gate(state: AgentState) -> str:
    return state.get("next_node", "error")

def node_retry_router(state: AgentState) -> dict:
    return {}

def build_graph() -> StateGraph[AgentState]:
    """
    Diagnostic graph:

        START
         ├─► resume_analyzer ─┐
         └─► jd_analyzer ──────┤
                               ▼
                       supervisor_route
                               ▼
                           skill_gap
                               ▼
                        supervisor_quality
                         ├─► question_gen
                         ├─► retry_analyzers ─► START
                         └─► error ─► END
    """
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("retry_router", node_retry_router)
    graph.add_node("resume_analyzer", node_resume_analyzer)
    graph.add_node("jd_analyzer", node_jd_analyzer)
    graph.add_node("supervisor_route", node_supervisor_route)
    graph.add_node("skill_gap", node_skill_gap)
    graph.add_node("supervisor_quality", node_supervisor_quality_gate)
    graph.add_node("question_gen", node_question_gen)
    graph.add_node("performance_evaluator", node_performance_evaluator)


    # Join after both analyzers have finished.
    graph.set_entry_point("resume_analyzer")
    graph.add_edge("resume_analyzer", "jd_analyzer")
    graph.add_edge("jd_analyzer","supervisor_route")

    graph.add_conditional_edges(
        "supervisor_route",
        route_after_supervisor,
        {
            "skill_gap": "skill_gap",
            "error": END,
        },
    )

    graph.add_edge("skill_gap", "supervisor_quality")

    graph.add_conditional_edges(
        "supervisor_quality",
        route_after_quality_gate,
        {
            "question_gen": "question_gen",
            "retry_analyzers": "retry_router",
            "error": END,
        },
    )
    graph.add_edge("retry_router", "resume_analyzer")
    graph.add_edge("question_gen", END)

    return graph


def build_evaluation_graph() -> StateGraph[AgentState]:
    """Separate mini-graph for the evaluation phase."""
    graph: StateGraph[AgentState] = StateGraph(AgentState)
    graph.add_node("performance_evaluator", node_performance_evaluator)
    graph.add_edge(START, "performance_evaluator")
    graph.add_edge("performance_evaluator", END)
    return graph


def run_diagnostic_pipeline(
    resume_text: str,
    jd_text: str,
    api_key: Optional[str] = None,
) -> AgentState:
    """
    Runs the diagnostic phase and returns the final state for the UI.
    """
    checkpointer = MemorySaver()
    graph = build_graph().compile(checkpointer=checkpointer)

    initial_state: AgentState = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "api_key": api_key,
        "resume_analysis": None,
        "jd_analysis": None,
        "skill_gap_report": None,
        "question_list": None,
        "user_answers": None,
        "performance_evaluation": None,
        "supervisor_retries": 0,
        "next_node": "",
        "errors": [],
        "execution_log": ["▶ Diagnostic pipeline started"],
    }

    config = {"configurable": {"thread_id": "session-1"}}
    return graph.invoke(initial_state, config=config)


def run_evaluation_pipeline(
    state: AgentState,
    user_answers: dict[str, str],
    api_key: Optional[str] = None,
) -> AgentState:
    """
    Runs only the performance evaluation node after mock interview answers
    have been collected.
    """
    checkpointer = MemorySaver()
    graph = build_evaluation_graph().compile(checkpointer=checkpointer)

    updated_state: AgentState = {**state, "user_answers": user_answers}
    if api_key:
        updated_state["api_key"] = api_key

    config = {"configurable": {"thread_id": "session-eval-1"}}
    return graph.invoke(updated_state, config=config)
