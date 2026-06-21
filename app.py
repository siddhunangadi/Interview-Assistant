import streamlit as st
import time
import html
import os
import re
from typing import Optional
from pipeline import run_placement_pipeline, extract_text_from_pdf
from supervisor import run_evaluation_pipeline
# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PlacementPrep AI · Career Agent System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,300&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #e8e4dc;
}

.stApp {
    background: #0d0d13;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,110,40,0.1) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,50,50,0.06) 0%, transparent 55%);
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1300px; }

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    position: relative;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #ff6e28;
    margin-bottom: 0.8rem;
    opacity: 0.9;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.4rem, 5vw, 4.2rem);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.03em;
    color: #f0ebe0;
    margin: 0 0 0.8rem;
}
.hero h1 span {
    color: #ff6e28;
}
.hero-sub {
    font-size: 1.02rem;
    font-weight: 300;
    color: #a09890;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,110,40,0.25), transparent);
    margin: 1.8rem 0;
}

/* ── Panels & Cards ── */
.input-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,110,40,0.12);
    border-radius: 16px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.8rem;
    backdrop-filter: blur(8px);
}
.panel-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.2rem;
}
.highlight-border {
    border-color: rgba(255,110,40,0.25) !important;
}

.panel-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #ff6e28;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,110,40,0.12);
}

.ready-gauge {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    padding: 1.5rem 0;
}
.ready-number {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    color: #50c878;
    line-height: 1;
}
.ready-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    color: #a09890;
    margin-top: 0.5rem;
    text-transform: uppercase;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}
.badge-green { background: rgba(80,200,120,0.1); color: #50c878; border: 1px solid rgba(80,200,120,0.25); }
.badge-red { background: rgba(255,75,75,0.1); color: #ff4b4b; border: 1px solid rgba(255,75,75,0.25); }
.badge-orange { background: rgba(255,110,40,0.1); color: #ff6e28; border: 1px solid rgba(255,110,40,0.25); }
.badge-grey { background: rgba(255,255,255,0.05); color: #a09890; border: 1px solid rgba(255,255,255,0.08); }

/* ── Step checklist cards ── */
.step-card {
    background: rgba(255,255,255,0.015);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.9rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
}
.step-card.active {
    border-color: rgba(255,110,40,0.35);
    background: rgba(255,110,40,0.03);
}
.step-card.done {
    border-color: rgba(80,200,120,0.25);
    background: rgba(80,200,120,0.02);
}
.step-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: 12px 0 0 12px;
    background: rgba(255,255,255,0.04);
}
.step-card.active::before { background: #ff6e28; }
.step-card.done::before   { background: #50c878; }

.step-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    color: #ff6e28;
    opacity: 0.7;
}
.step-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: #f0ebe0;
}
.step-status {
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.08em;
}
.status-waiting  { color: #444; }
.status-running  { color: #ff6e28; animation: pulse 1.5s infinite; }
.status-done     { color: #50c878; }

@keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}

.step-desc {
    font-size: 0.78rem;
    color: #787068;
    margin-top: 0.25rem;
    padding-left: 0.2rem;
}

/* ── Section Heading ── */
.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #f0ebe0;
    margin: 1.8rem 0 0.8rem;
}

/* ── Footer ── */
.notice {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #555;
    text-align: center;
    margin-top: 3.5rem;
    letter-spacing: 0.08em;
}
</style>
""", unsafe_allow_html=True)


# ── Step Card Render Helper ──────────────────────────────────────────────────
def render_step_card(num: str, title: str, state: str, desc: str = ""):
    status_map = {
        "waiting": ("WAITING", "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done":    ("✓ DONE",   "status-done"),
    }
    label, cls = status_map.get(state, ("", ""))
    card_cls = {"running": "active", "done": "done"}.get(state, "")
    st.markdown(f"""
    <div class="step-card {card_cls}">
        <div class="step-header">
            <span class="step-num">{num}</span>
            <span class="step-title">{title}</span>
            <span class="step-status {cls}">{label}</span>
        </div>
        {"<div class='step-desc'>"+desc+"</div>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)


def sanitize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"<[^>]*>", "", value)
    return html.unescape(cleaned)


# ── Session State Initialisation ──────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = "setup"
if "resume_analysis" not in st.session_state:
    st.session_state.resume_analysis = None
if "jd_analysis" not in st.session_state:
    st.session_state.jd_analysis = None
if "skill_gap_report" not in st.session_state:
    st.session_state.skill_gap_report = None
if "questions" not in st.session_state:
    st.session_state.questions = None
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None
if "running_diagnostics" not in st.session_state:
    st.session_state.running_diagnostics = False
if "running_evaluation" not in st.session_state:
    st.session_state.running_evaluation = False
if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
if "execution_log" not in st.session_state:
    st.session_state.execution_log = []


# ── Sidebar Configuration ─────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="text-align: center; margin-bottom: 1.5rem;">
    <h3 style="font-family:'Syne',sans-serif; font-weight:800; color:#f0ebe0; margin:0;">PlacementPrep AI</h3>
    <p style="font-family:'DM Mono',monospace; font-size:0.65rem; color:#ff6e28; text-transform:uppercase; letter-spacing:0.15em;">Multi-Agent Career Engine</p>
</div>
""", unsafe_allow_html=True)

api_key = st.sidebar.text_input(
    "Mistral API Key",
    type="password",
    value=os.getenv("MISTRAL_API_KEY", "")
)
st.sidebar.markdown("""
<div class="divider" style="margin: 1.2rem 0;"></div>
<div style="font-size: 0.8rem; color: #a09890; line-height: 1.5;">
    <h4 style="font-family:'Syne',sans-serif; font-weight:600; color:#f0ebe0; margin: 0 0 0.5rem 0;">System Overview</h4>
    This framework runs 6 sequential agents to accelerate placement preparation:
    <ol style="padding-left: 1.1rem; margin-top: 0.4rem;">
        <li><b>Resume Analyzer</b> extracts skills, experience & profile.</li>
        <li><b>JD Analyzer</b> maps key job roles & technical stacks.</li>
        <li><b>Skill Gap Agent</b> analyzes differences & scores matches.</li>
        <li><b>Question Generator</b> creates 5 personalized questions.</li>
        <li><b>Mock Interview</b> runs interactive sessions.</li>
        <li><b>Performance Evaluator</b> provides grading & improvements.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Add sidebar reset button
if st.sidebar.button("🔄 Reset / Start New session", use_container_width=True):
    for key in ("step", "resume_analysis", "jd_analysis", "skill_gap_report", "questions", "current_question_index", "user_answers", "evaluation", "running_diagnostics", "running_evaluation", "agent_state", "execution_log"):
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ── Execution log in sidebar ──────────────────────────────────────────────────
if st.session_state.execution_log:
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='font-family:DM Mono,monospace;font-size:0.65rem;color:#ff6e28;"
        "text-transform:uppercase;letter-spacing:0.1em;'>Agent execution log</p>",
        unsafe_allow_html=True
    )
    for entry in st.session_state.execution_log:
        color = "#50c878" if entry.startswith("✓") else "#ff4b4b" if entry.startswith("✗") else "#ff6e28" if entry.startswith("↻") else "#a09890"
        st.sidebar.markdown(
            f"<p style='font-family:DM Mono,monospace;font-size:0.68rem;color:{color};"
            f"margin:0.1rem 0;'>{entry}</p>",
            unsafe_allow_html=True
        )


# ── Hero Title ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Interactive Agentic Framework</div>
    <h1>Placement<span>Prep</span> AI</h1>
    <p class="hero-sub">
        Maximize your readiness. An advanced multi-agent system analyzing resume-JD alignments,
        hosting simulated interviews, and detailing targeted improvement tracks.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ── Layout: workspace on the left, checklist tracker on the right ─────────────
col_workspace, col_spacer, col_tracker = st.columns([5, 0.4, 3.8])


# ── Step Resolver for the Checklist Tracker ───────────────────────────────────
def get_step_state(name: str) -> str:
    step = st.session_state.step
    diag_active = st.session_state.running_diagnostics
    eval_active = st.session_state.running_evaluation
    
    if name == "resume":
        if st.session_state.resume_analysis:
            return "done"
        return "running" if diag_active else "waiting"
    elif name == "jd":
        if st.session_state.jd_analysis:
            return "done"
        if diag_active and st.session_state.resume_analysis:
            return "running"
        return "waiting"
    elif name == "gap":
        if st.session_state.skill_gap_report:
            return "done"
        if diag_active and st.session_state.jd_analysis:
            return "running"
        return "waiting"
    elif name == "questions":
        if st.session_state.questions:
            return "done"
        if diag_active and st.session_state.skill_gap_report:
            return "running"
        return "waiting"
    elif name == "interview":
        if step == "evaluation_complete":
            return "done"
        if step == "interviewing":
            return "running"
        return "waiting"
    elif name == "eval":
        if st.session_state.evaluation:
            return "done"
        return "running" if eval_active else "waiting"
    return "waiting"


# ── Render Checklist Tracker on the right column ──────────────────────────────
with col_tracker:
    st.markdown('<div class="section-heading">Agent Pipeline</div>', unsafe_allow_html=True)
    render_step_card("01", "Resume Analyzer Agent", get_step_state("resume"), "Extracts skills, experience, and key projects.")
    render_step_card("02", "JD Analyzer Agent", get_step_state("jd"), "Extracts core responsibilities and technical stack requirements.")
    render_step_card("03", "Skill Gap Agent", get_step_state("gap"), "Compares resume features against JD to score alignment.")
    render_step_card("04", "Question Generator Agent", get_step_state("questions"), "Generates 5 tailored technical & behavioral questions.")
    render_step_card("05", "Mock Interview Agent", get_step_state("interview"), "Guides the candidate through responses.")
    render_step_card("06", "Performance Evaluator Agent", get_step_state("eval"), "Grades answers and constructs action plan.")


# ── Main Workspace Logic on the left column ───────────────────────────────────
with col_workspace:

    # ── Phase 1: Setup Workspace ──
    if st.session_state.step == "setup":
        st.markdown('<div class="section-heading">Diagnostics Setup</div>', unsafe_allow_html=True)
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        
        # Resume input
        st.markdown("<p style='font-family:\"DM Mono\",monospace; font-size:0.75rem; color:#ff6e28; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.4rem;'>1. Submit Resume</p>", unsafe_allow_html=True)
        resume_source = st.radio("Choose Input Method:", ("PDF File Upload", "Copy & Paste Text"), horizontal=True)
        
        resume_text_content = ""
        if resume_source == "PDF File Upload":
            uploaded_pdf = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
            if uploaded_pdf is not None:
                try:
                    resume_text_content = extract_text_from_pdf(uploaded_pdf)
                    st.success("Resume text extracted successfully from PDF!")
                except Exception as e:
                    st.error(f"Error reading PDF: {str(e)}")
        else:
            resume_text_content = st.text_area("Paste Resume Text Here", height=180, placeholder="John Doe\nSoftware Engineer...\nSkills: Python, Javascript...")
            
        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
        
        # JD input
        st.markdown("<p style='font-family:\"DM Mono\",monospace; font-size:0.75rem; color:#ff6e28; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.4rem;'>2. Job Description (JD)</p>", unsafe_allow_html=True)
        jd_text_content = st.text_area("Paste Job Description Here", height=150, placeholder="We are looking for a Software Engineer proficient in Python, SQL, and AWS to design scalable services...")
        
        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
        
        # Action button
        run_btn = st.button("⚡ Run Diagnostics & Generate Interview", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if run_btn:
            if not api_key:
                st.warning("Please supply a Mistral API Key in the sidebar first.")
            elif not resume_text_content.strip():
                st.warning("Please upload a resume or paste your resume content.")
            elif not jd_text_content.strip():
                st.warning("Please supply a Job Description.")
            else:
                st.session_state.running_diagnostics = True
                
                # Dynamic Spinner Progress
                with st.spinner("Analyzing profile and Job Description..."):
                    try:
                        r_analysis, jd_analysis, gap_report, questions, agent_state = run_placement_pipeline(
                            resume_text_content,
                            jd_text_content,
                            api_key
                        )
                        st.session_state.resume_analysis = r_analysis
                        st.session_state.jd_analysis = jd_analysis
                        st.session_state.skill_gap_report = gap_report
                        st.session_state.questions = questions.questions
                        st.session_state.agent_state = agent_state
                        st.session_state.execution_log = agent_state.get("execution_log", [])

                        st.session_state.running_diagnostics = False
                        st.session_state.step = "diagnostics_complete"
                        st.rerun()
                    except Exception as e:
                        st.session_state.running_diagnostics = False
                        st.error(f"An error occurred in the multi-agent pipeline: {str(e)}")


    # ── Phase 2: Diagnostics Dashboard ──
    elif st.session_state.step == "diagnostics_complete":
        st.markdown('<div class="section-heading">Diagnostic Assessment Findings</div>', unsafe_allow_html=True)
        
        # Skill Match gauge card
        match_score = st.session_state.skill_gap_report.match_score
        st.markdown(f"""
        <div class="panel-card highlight-border" style="display:flex; align-items:center; justify-content:space-between; gap:2rem;">
            <div class="ready-gauge" style="flex: 1;">
                <span class="ready-number">{match_score}%</span>
                <span class="ready-label">Resume Alignment Index</span>
            </div>
            <div style="flex: 2; border-left:1px solid rgba(255,255,255,0.06); padding-left:2rem;">
                <h4 style="font-family:'Syne',sans-serif; color:#f0ebe0; margin:0 0 0.5rem 0;">Profile Matching Profile</h4>
                <p style="font-size:0.88rem; color:#a09890; margin:0; line-height:1.5;">
                    The Skill Gap Agent has calculated a match score based on overlapping keywords, project context, and estimated experience compared to the Job Description requirements. Review detailed breakdown below or start your interactive session.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for details
        tab_skills, tab_profile, tab_bridging = st.tabs(["📊 Skill Alignment", "👤 Extracted Profiles", "💡 Bridging Strategy"])
        
        with tab_skills:
            gap = st.session_state.skill_gap_report
            st.markdown("<p style='font-size:0.9rem; font-weight:700; color:#50c878; margin-bottom:0.5rem;'>Matched Qualifications</p>", unsafe_allow_html=True)
            if gap.matching_skills:
                m_badges = "".join([f'<span class="badge badge-green">{s}</span>' for s in gap.matching_skills])
                st.markdown(f"<div>{m_badges}</div>", unsafe_allow_html=True)
            else:
                st.info("No explicit skills matched between the Resume and the JD.")
                
            st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.9rem; font-weight:700; color:#ff4b4b; margin-bottom:0.5rem;'>Critical Skill Gaps (Missing from Resume)</p>", unsafe_allow_html=True)
            if gap.missing_skills:
                ms_badges = "".join([f'<span class="badge badge-red">{s}</span>' for s in gap.missing_skills])
                st.markdown(f"<div>{ms_badges}</div>", unsafe_allow_html=True)
            else:
                st.success("No missing required skills! Excellent profile alignment.")
                
            if gap.nice_to_have_matches:
                st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
                st.markdown("<p style='font-size:0.9rem; font-weight:700; color:#ff6e28; margin-bottom:0.5rem;'>Nice-To-Have Skills Matched</p>", unsafe_allow_html=True)
                nth_badges = "".join([f'<span class="badge badge-orange">{s}</span>' for s in gap.nice_to_have_matches])
                st.markdown(f"<div>{nth_badges}</div>", unsafe_allow_html=True)

        with tab_profile:
            r = st.session_state.resume_analysis
            jd = st.session_state.jd_analysis
            
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.markdown(f"""
                <div class="panel-card" style="height: 100%;">
                    <div class="panel-title">Resume Analyzer Output</div>
                    <p><b>Candidate:</b> {r.candidate_name}</p>
                    <p><b>Experience:</b> {r.experience_years} years</p>
                    <p><b>Education:</b> {", ".join(r.education)}</p>
                    <p style="margin-bottom:0.2rem;"><b>Extracted Key Strengths:</b></p>
                    <ul style="padding-left:1.2rem; margin-top:0; font-size:0.85rem; color:#a09890;">
                        {"".join([f'<li>{s}</li>' for s in r.strengths])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            with p_col2:
                st.markdown(f"""
                <div class="panel-card" style="height: 100%;">
                    <div class="panel-title">JD Analyzer Output</div>
                    <p><b>Job Title:</b> {jd.job_title}</p>
                    <p><b>Target Company:</b> {jd.company_name or 'N/A'}</p>
                    <p><b>Required Experience:</b> {jd.required_experience_years} years</p>
                    <p style="margin-bottom:0.2rem;"><b>Key Responsibilities:</b></p>
                    <ul style="padding-left:1.2rem; margin-top:0; font-size:0.85rem; color:#a09890;">
                        {"".join([f'<li>{s}</li>' for s in jd.key_responsibilities[:4]])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
        with tab_bridging:
            gap = st.session_state.skill_gap_report
            st.markdown("<p style='font-size:0.9rem; font-weight:700; color:#ff6e28; margin-bottom:0.5rem;'>Actionable Preparation Guidelines</p>", unsafe_allow_html=True)
            strategies = "".join([f"<li style='margin-bottom:0.5rem; font-size:0.9rem; color:#cdc8bf;'>{s}</li>" for s in gap.bridging_strategy])
            st.markdown(f"<ul style='padding-left:1.2rem; margin-top:0.3rem;'>{strategies}</ul>", unsafe_allow_html=True)
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # CTA button
        if st.button("🚀 Proceed to Interactive Mock Interview", use_container_width=True):
            st.session_state.step = "interviewing"
            st.session_state.current_question_index = 0
            st.session_state.user_answers = {}
            st.rerun()


    # ── Phase 3: Interactive Interview Workspace ──
    elif st.session_state.step == "interviewing":
        questions = st.session_state.questions
        idx = st.session_state.current_question_index
        q = questions[idx]
        
        st.markdown(f'<div class="section-heading">Mock Interview · Question {idx+1} of {len(questions)}</div>', unsafe_allow_html=True)
        
        # Progress bar
        st.progress((idx) / len(questions))
        
        st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
        
        # Question display
        st.markdown(f"""
        <div class="panel-card highlight-border">
            <span class="badge badge-orange">{q.question_type}</span>
            <div style="font-size:1.15rem; font-weight:700; color:#f0ebe0; margin-top:0.8rem; margin-bottom:0.5rem; line-height:1.5;">
                "{q.question_text}"
            </div>
            <p style="font-size:0.82rem; color:#787068; margin:0; font-family:'DM Mono',monospace;">
                TIPS: Explain your thought process, use the STAR methodology if it is situational, and target details.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Answer text area
        ans_key = f"answer_box_{idx}"
        user_response = st.text_area(
            "Your Response:",
            height=160,
            key=ans_key,
            placeholder="Type your response here..."
        )
        
        st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)
        
        # Navigation buttons
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if idx > 0:
                if st.button("⬅ Previous Question", use_container_width=True):
                    # Save progress first
                    st.session_state.user_answers[str(q.question_id)] = user_response
                    st.session_state.current_question_index -= 1
                    st.rerun()
            else:
                st.markdown("<div style='height:1px;'></div>", unsafe_allow_html=True)
                
        with col_next:
            if idx < len(questions) - 1:
                if st.button("Submit Answer & Next Question ➡️", use_container_width=True):
                    st.session_state.user_answers[str(q.question_id)] = user_response
                    st.session_state.current_question_index += 1
                    st.rerun()
            else:
                if st.button("Submit Final Answer & Run Evaluation 🎓", use_container_width=True):
                    st.session_state.user_answers[str(q.question_id)] = user_response
                    st.session_state.running_evaluation = True
                    
                    with st.spinner("Evaluating your responses..."):
                        try:
                            evaluation_state = run_evaluation_pipeline(
                                st.session_state.agent_state,
                                st.session_state.user_answers,
                                api_key
                            )
                            evaluation = evaluation_state["performance_evaluation"]
                            st.session_state.evaluation = evaluation
                            st.session_state.running_evaluation = False
                            st.session_state.step = "evaluation_complete"
                            st.rerun()
                        except Exception as e:
                            st.session_state.running_evaluation = False
                            st.error(f"Error evaluating answers: {str(e)}")


    # ── Phase 4: Performance Evaluation Dashboard ──
    elif st.session_state.step == "evaluation_complete":
        st.markdown('<div class="section-heading">Interview Performance Report</div>', unsafe_allow_html=True)
        
        eval_report = st.session_state.get("evaluation")

        if eval_report is None:
            st.error("Performance evaluation was not generated.")
            st.stop()

        overall_score = eval_report.overall_readiness_score
        
        # Overall readiness metric card
        color_class = "#50c878" if overall_score >= 75 else "#ff6e28" if overall_score >= 50 else "#ff4b4b"
        st.markdown(f"""
        <div class="panel-card highlight-border" style="display:flex; align-items:center; justify-content:space-between; gap:2rem;">
            <div class="ready-gauge" style="flex: 1;">
                <span class="ready-number" style="color:{color_class};">{overall_score}%</span>
                <span class="ready-label">Placement Readiness Score</span>
            </div>
            <div style="flex: 2; border-left:1px solid rgba(255,255,255,0.06); padding-left:2rem;">
                <h4 style="font-family:'Syne',sans-serif; color:#f0ebe0; margin:0 0 0.5rem 0;">Performance Verdict</h4>
                <p style="font-size:0.88rem; color:#cdc8bf; margin:0; line-height:1.6; font-style:italic;">
                    "{html.escape(sanitize_text(eval_report.final_verdict))}"
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for detailed breakdown
        tab_eval_breakdown, tab_synthesis = st.tabs(["📋 Answers Analysis", "📈 Strengths & Focus Areas"])
        
        with tab_eval_breakdown:
            questions_list = st.session_state.questions
            for idx, q_eval in enumerate(eval_report.evaluations):
                # Find matching question type
                q_type = "Question"
                if idx < len(questions_list):
                    q_type = questions_list[idx].question_type

                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                            <span class="badge badge-grey">Question {q_eval.question_id} ({q_type})</span>
                            <span class="badge badge-orange" style="font-weight:700; font-size:0.8rem;">Score: {q_eval.score}/10</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"**Q:** {sanitize_text(q_eval.question_text or '')}",
                    )
                    st.markdown("**Your Answer:**")
                    st.write(sanitize_text(q_eval.user_answer) or "No answer provided.")

                    st.markdown("**✓ Strengths:**")
                    if q_eval.strengths:
                        st.markdown("\n".join(f"- {sanitize_text(s)}" for s in q_eval.strengths))
                    else:
                        st.caption("None noted.")

                    st.markdown("**✗ Areas of Improvement:**")
                    if q_eval.weaknesses:
                        st.markdown("\n".join(f"- {sanitize_text(w)}" for w in q_eval.weaknesses))
                    else:
                        st.caption("None noted.")

                    st.markdown(f"**💡 How to Improve:** {sanitize_text(q_eval.suggested_improvement)}")
                
                # Show model answer
                if idx < len(questions_list):
                    with st.expander(f"📖 View Expected Points & Model Answer (Question {q_eval.question_id})", expanded=False):
                        st.markdown(
                            f"**Expected Key Points:** {', '.join(sanitize_text(point) for point in questions_list[idx].expected_key_points)}"
                        )
                        st.markdown("**Model Answer:**")
                        st.write(sanitize_text(questions_list[idx].model_answer))
                        
        with tab_synthesis:
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                with st.container(border=True):
                    st.markdown("#### Top Strengths")
                    if eval_report.key_strengths:
                        for strength in eval_report.key_strengths:
                            st.write(f"- {sanitize_text(strength)}")
                    else:
                        st.caption("No strengths were identified.")
            with s_col2:
                with st.container(border=True):
                    st.markdown("#### Development Focus Areas")
                    if eval_report.key_development_areas:
                        for area in eval_report.key_development_areas:
                            st.write(f"- {sanitize_text(area)}")
                    else:
                        st.caption("No development areas were identified.")
                
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Download summary report
        md_report = f"""# Placement Readiness Report
Generated by PlacementPrep AI on {time.strftime("%Y-%m-%d %H:%M:%S")}

## Overall Score: {overall_score}%

### General Verdict:
{eval_report.final_verdict}

### Overarching Key Strengths:
{chr(10).join([f"- {s}" for s in eval_report.key_strengths])}

### Top Development Focus Areas:
{chr(10).join([f"- {d}" for d in eval_report.key_development_areas])}

---

## Detailed Question & Answer Evaluation
"""
        for q_eval in eval_report.evaluations:
            md_report += f"""
### Question {q_eval.question_id}: {q_eval.question_text}
- **Grade:** {q_eval.score}/10
- **Candidate Answer:** {q_eval.user_answer}
- **Strengths:** {", ".join(q_eval.strengths)}
- **Areas of Improvement:** {", ".join(q_eval.weaknesses)}
- **Suggested Improvement:** {q_eval.suggested_improvement}
"""
        
        st.download_button(
            label="⬇  Download Full Performance Report (.md)",
            data=md_report,
            file_name=f"placement_evaluation_report_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True
        )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="notice">
    PlacementPrep AI · Powered by LangChain multi-agent structured executor · Built with Streamlit
</div>
""", unsafe_allow_html=True)
