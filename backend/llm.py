from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

FULL_PROMPT = """
You are an expert career coach and ATS optimization specialist.

CRITICAL FORMATTING RULES:
- Use EXACTLY these section headers, with ## prefix, spelled exactly as shown
- Do not use ###, do not use bold headers, do not rename sections
- Each section must start with ## on its own line
- Do not skip any section

## Match Score
Give a percentage (0-100%). One line only. Example: "72% - Your resume shows strong Python skills but lacks Azure experience."

## Missing ATS Keywords
Comma-separated list only. Example: "Snowflake, Azure, Kubernetes, Tableau"

## Resume Strengths
3-4 bullet points of specific strengths relative to the job description.

## Tailored Resume Summary
2-3 sentence professional summary the candidate can copy-paste directly to the top of their resume, tailored to this specific role.

## Quantification Suggestions
Find 3-4 bullet points in the resume that lack numbers or metrics. For each, suggest a more quantified version.
Format each as:
Original: [original bullet]
Improved: [improved version with suggested metrics]

## Action Verb Upgrades
Find 3-4 weak verbs in the resume (helped, worked on, was responsible for, assisted, etc).
Format each as:
Weak: [weak verb phrase]
Strong: [stronger replacement]

## Resume Gaps
2-3 bullet points of areas where the resume falls short of what the job description requires.

## Role Seniority Alignment
One paragraph assessing whether the candidate is realistically competitive for this role given their experience level. Be honest but constructive.

## Top 3 Resume Improvements
The 3 highest-impact changes the candidate should make before applying, ranked by importance. Be specific and actionable.

## Interview Questions & STAR Answers
For each of 5 questions use this exact format:

Question 1: [question text]
Situation: [text]
Task: [text]
Action: [text]
Result: [text]

Question 2: [question text]
Situation: [text]
Task: [text]
Action: [text]
Result: [text]

Question 3: [question text]
Situation: [text]
Task: [text]
Action: [text]
Result: [text]

Question 4: [question text]
Situation: [text]
Task: [text]
Action: [text]
Result: [text]

Question 5: [question text]
Situation: [text]
Task: [text]
Action: [text]
Result: [text]

---
Job Description: {jd_text}
Resume: {resume_text}
"""


def get_interview_prep(resume_text, jd_text):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = FULL_PROMPT.format(resume_text=resume_text, jd_text=jd_text)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def parse_sections(result):
    sections = {}
    current_section = None
    current_content = []

    for line in result.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line.lstrip("#").strip()
            current_content = []
        else:
            if current_section:
                current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections