import sys
import os
from dotenv import load_dotenv
load_dotenv(".env")

from pipeline import run_placement_pipeline

resume = """
Jane Doe
jane.doe@example.com
Education: BS in Computer Science from Stanford University (2020-2024)
Experience:
- Software Engineer Intern at Google (Summer 2023)
  - Developed a backend microservice in Python and Go.
  - Used PostgreSQL and Redis.
Skills: Python, Go, SQL, Git, Docker, HTML/CSS.
Projects:
- Personal Portfolio Website (React, HTML/CSS)
- Distributed key-value store in Go
"""

jd = """
Job Title: Software Engineer (Full Stack / Backend Focus)
Company Name: Acme Corp
Required Experience: 1+ years
Required Skills: Python, SQL, Docker, AWS, React.
Preferred Skills: Kubernetes, Go.
Key Responsibilities:
- Design and implement microservices in Python.
- Deploy services using Docker and AWS.
- Work with relational databases like PostgreSQL.
"""

print("Running diagnostics pipeline...")
try:
    resume_analysis, jd_analysis, gap_report, questions, agent_state = run_placement_pipeline(
        resume, jd
    )
    print("Success!")
    print("Candidate:", resume_analysis.candidate_name)
    print("JD Job Title:", jd_analysis.job_title)
    print("Skill Gap Match Score:", gap_report.match_score)
    print("Generated Questions:")
    for q in questions.questions:
        print(f"- [{q.question_type}] {q.question_text}")
except Exception as e:
    print("Failed with exception:")
    import traceback
    traceback.print_exc()
