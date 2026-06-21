"""
pipeline.py — Backward-compatibility shim.

The original pipeline.py contained the entire orchestration logic.
That logic now lives in supervisor.py (LangGraph StateGraph).

This file keeps the same public function signatures so app.py needs
minimal changes — it just delegates to the new supervisor.
"""

import pypdf
from typing import Optional, Tuple

from agents import ResumeAnalysis, JDAnalysis, SkillGapReport, QuestionList
from supervisor import run_diagnostic_pipeline, AgentState


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from an uploaded PDF file (unchanged from original)."""
    try:
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")


def run_placement_pipeline(
    resume_text: str,
    jd_text: str,
    api_key: Optional[str] = None,
) -> Tuple[ResumeAnalysis, JDAnalysis, SkillGapReport, QuestionList, AgentState]:
    """
    Drop-in replacement for the original run_placement_pipeline().

    Returns the same 4-tuple the original did, PLUS the full AgentState so
    app.py can read execution_log and errors for the sidebar tracker.

    FLAW FIXED: original returned a plain tuple with no metadata about what
    happened inside the pipeline.  Now the caller gets the full state.
    """
    final_state = run_diagnostic_pipeline(resume_text, jd_text, api_key)

    # Surface any errors to the caller
    errors = final_state.get("errors", [])
    if errors:
        # Non-fatal: log but continue — some agents may have succeeded
        import logging
        logging.getLogger(__name__).warning(f"Pipeline completed with errors: {errors}")

    resume_analysis  = final_state.get("resume_analysis")
    jd_analysis      = final_state.get("jd_analysis")
    skill_gap_report = final_state.get("skill_gap_report")
    question_list    = final_state.get("question_list")

    # Hard-fail only if core outputs are missing
    missing = [
        name for name, val in [
            ("resume_analysis",  resume_analysis),
            ("jd_analysis",      jd_analysis),
            ("skill_gap_report", skill_gap_report),
            ("question_list",    question_list),
        ] if val is None
    ]
    if missing:
        raise RuntimeError(
            f"Pipeline failed — missing outputs: {missing}\n"
            f"Errors: {errors}"
        )

    return resume_analysis, jd_analysis, skill_gap_report, question_list, final_state
