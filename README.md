# PlacementPrep AI 
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-brightgreen?style=for-the-badge)](https://interview-assistant-9hvmqvyuvg8w8wnbrretc8.streamlit.app/)
PlacementPrep AI is a multi-agent Streamlit app for placement preparation and interview practice. It analyzes a resume and job description, finds skill gaps, generates tailored questions, runs a mock interview flow, and produces a performance report with improvement guidance.

## What it does

- Extracts resume and JD text
- Runs a resume analyzer and JD analyzer
- Compares both to identify skill gaps
- Generates tailored technical and behavioral questions
- Evaluates interview answers
- Produces a final readiness report with strengths and focus areas

## Project structure

- `app.py` - Streamlit UI and report rendering
- `pipeline.py` - Resume PDF extraction and compatibility wrapper
- `supervisor.py` - LangGraph-based orchestration for the agent pipeline
- `agents.py` - Agent models and individual agent functions
- `tools.py` - Utility helpers used by the pipeline
- `test_pipeline.py` - Basic pipeline test script
- `requirements.txt` - Python dependencies

## Requirements

- Python 3.10+
- A Mistral API key
- Streamlit

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your API key in a `.env` file:

```bash
MISTRAL_API_KEY=your_api_key_here
```

## Run the app

```bash
streamlit run app.py
```

## How to use

1. Upload a resume PDF.
2. Paste the job description.
3. Enter your Mistral API key.
4. Run the diagnostic pipeline.
5. Review the skill gap analysis, generated questions, and performance report.

## Notes

- The app ignores local environment files and virtual environments via `.gitignore`.
- The evaluation report is designed to show plain text answers and avoid raw HTML rendering issues.

