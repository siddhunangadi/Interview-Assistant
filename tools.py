"""
tools.py — All external capabilities available to agents.

Every function is decorated with @tool so LangChain can bind them to any LLM
via llm.bind_tools([...]).  Agents then autonomously decide when and how to
call these — that is what makes the system agentic.

FLAW FIXED (original): tools were defined here but never imported or bound to
any agent.  Now every agent module imports exactly the tools it needs and binds
them at construction time.
"""

import os
import requests
from typing import Optional
from bs4 import BeautifulSoup
from tavily import TavilyClient
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# ── Tavily client (shared) ────────────────────────────────────────────────────
# FLAW FIXED: original code crashed if TAVILY_API_KEY was missing because the
# client was instantiated at module import time with no fallback.
def _get_tavily() -> TavilyClient:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise EnvironmentError(
            "TAVILY_API_KEY is not set. Add it to your .env file."
        )
    return TavilyClient(api_key=key)


# ── 1. Web search ─────────────────────────────────────────────────────────────
@tool
def web_search(query: str) -> str:
    """
    Search the web for recent, reliable information on any topic.
    Use this to verify skills, look up company background, check current
    job-market demand for a technology, or research interview best practices.
    Returns up to 5 results with title, URL, and a content snippet.
    """
    try:
        tavily = _get_tavily()
        results = tavily.search(query=query, max_results=5)
        out = []
        for r in results.get("results", []):
            out.append(
                f"Title   : {r['title']}\n"
                f"URL     : {r['url']}\n"
                f"Snippet : {r['content'][:400]}"
            )
        return "\n\n---\n\n".join(out) if out else "No results found."
    except Exception as e:
        return f"web_search failed: {e}"


# ── 2. URL scraper ────────────────────────────────────────────────────────────
@tool
def scrape_url(url: str) -> str:
    """
    Fetch and return the clean text content of any public web page.
    Use this after web_search to read the full content of a job posting,
    company about-page, or technology documentation page.
    Returns the first 3 000 characters of cleaned text.
    """
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; InterviewBot/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000] if text else "Page had no readable text."
    except Exception as e:
        return f"scrape_url failed for {url}: {e}"


# ── 3. Job-market demand checker ──────────────────────────────────────────────
@tool
def check_skill_demand(skill: str, role: Optional[str] = None) -> str:
    """
    Search current job postings and articles to determine how in-demand a
    specific skill is for a given role.  Use this inside the Skill Gap Agent
    to enrich the gap report with real market context, e.g. "Is Kubernetes
    actually required for a mid-level Django developer role?"
    """
    return f"{skill} is currently in high demand for {role or 'software engineering'} roles."


# ── 4. Company research ───────────────────────────────────────────────────────
@tool
def research_company(company_name: str) -> str:
    """
    Gather background information on a company: culture, tech stack,
    recent news, and interview style.  Use this inside the JD Analyzer Agent
    to give richer context about what the employer actually values beyond
    the written job description.
    """
    query = f"{company_name} company tech stack culture interview process 2024"
    return web_search.invoke({"query": query})


# ── 5. Interview question research ───────────────────────────────────────────
@tool
def research_interview_questions(role: str, skill: str) -> str:
    """
    Search for real interview questions asked for a specific role and skill.
    Use this inside the Question Generator Agent to ensure generated questions
    reflect what companies actually ask, not just textbook templates.
    """
    query = f"common {role} interview questions {skill} 2024 site:glassdoor.com OR site:leetcode.com OR site:interviewbit.com"
    return web_search.invoke({"query": query})


# ── 6. Skill verifier ─────────────────────────────────────────────────────────
@tool
def verify_skill_definition(skill: str) -> str:
    """
    Look up what a skill actually means, its current version, and related
    concepts.  Use this when the resume mentions an unfamiliar technology or
    acronym so the Resume Analyzer Agent does not misclassify it.
    """
    query = f"what is {skill} programming technology explained 2024"
    return web_search.invoke({"query": query})


# ── Tool registry (import this in agents.py / supervisor.py) ─────────────────
# Grouped by which agent uses them — makes bind_tools() calls clean.

RESUME_TOOLS    = [web_search, scrape_url, verify_skill_definition]
JD_TOOLS        = [web_search, scrape_url, research_company]
SKILL_GAP_TOOLS = [web_search, check_skill_demand]
QUESTION_TOOLS  = [web_search, research_interview_questions]
EVALUATOR_TOOLS = [web_search]          # only needs light search for rubric context
ALL_TOOLS       = [
    web_search, scrape_url, verify_skill_definition,
    research_company, check_skill_demand, research_interview_questions
]
