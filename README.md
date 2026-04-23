# 🎯 PrepAI — AI-Powered Resume & Interview Coach

An LLM-powered career tool that analyzes your resume against a job description to generate a full ATS report, actionable resume improvements, and tailored STAR-method interview answers — in seconds.

🔗 **Live App:** [interviewcoach-ai.streamlit.app](https://interviewcoach-ai.streamlit.app)
🌐 **Landing Page:** [ai-interviewer-three-phi.vercel.app](https://ai-interviewer-three-phi.vercel.app)

---

<img width="1915" height="986" alt="image" src="https://github.com/user-attachments/assets/bb30eb3f-2d26-4aeb-92fc-6b056afe9bfb" />
<br>
<img width="1209" height="883" alt="image" src="https://github.com/user-attachments/assets/451f929f-bf95-4818-b45a-4f215a8a3523" />
<br>
<img width="850" height="992" alt="image" src="https://github.com/user-attachments/assets/9f40067f-7e98-444d-8e4c-5b440ce2ca59" />

---

## What It Does

PrepAI performs a 10-section resume analysis split across a free and paid tier:

### Free Tier
- **ATS Match Score** — percentage score showing how well your resume matches the job description
- **Missing Keywords** — exact keywords from the JD absent from your resume
- **Resume Strengths** — specific strengths relative to the role
- **Tailored Resume Summary** — a ready-to-copy professional summary written for this specific role

### Pro Tier
- **Quantification Suggestions** — rewrites vague bullet points with suggested metrics
- **Action Verb Upgrades** — replaces weak verbs with powerful alternatives
- **Resume Gaps** — areas where the resume falls short of the JD requirements
- **Role Seniority Alignment** — honest assessment of competitiveness for the role
- **Top 3 Resume Improvements** — highest-impact changes ranked by priority
- **Interview Q&A (STAR Method)** — 5 tailored interview questions with full STAR-method answers grounded in the user's actual experience

---

## Architecture Overview

```
User Input
    ├── Resume (PDF / DOCX / Pasted text)
    └── Job Description (pasted text)
            ↓
    Document Parser
    (pypdf / python-docx)
            ↓
    Prompt Builder
    (10-section structured prompt)
            ↓
    Groq API — LLaMA 3.3 70B
            ↓
    Section Parser
    (extracts and routes each section to its renderer)
            ↓
    Streamlit UI
    (free sections rendered / paid sections locked behind auth tier)
            ↓
    Supabase
    (user auth, tier management, daily usage tracking)
```

---

## Project Structure

```
ai-interviewer/
│
├── app.py              # Streamlit UI + render helpers + routing
├── auth.py             # Supabase auth, session management, usage tracking
├── llm.py              # Groq API call + 10-section prompt + section parser
├── parser.py           # PDF / DOCX / plain text resume parsing
├── styles/
│   └── main.css        # Full dark theme UI (Deep Sea palette)
├── index.html          # Landing page (deployed on Vercel)
├── requirements.txt
├── vercel.json         # Vercel static deploy config
└── .env                # API keys (never commit this)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| LLM | Groq API — LLaMA 3.3 70B |
| Resume Parsing | pypdf / python-docx |
| UI | Streamlit |
| Auth & Database | Supabase (PostgreSQL + Google OAuth) |
| Landing Page | HTML/CSS/JS deployed on Vercel |
| Hosting | Streamlit Cloud |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/tonyranye/ai-interviewer.git
cd ai-interviewer
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your_groq_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SITE_URL=http://localhost:8501
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### 5. Run the app

```bash
streamlit run app.py
```

---

## Database Schema

```sql
create table profiles (
  id uuid references auth.users on delete cascade,
  email text,
  tier text default 'free',
  analyses_today integer default 0,
  last_analysis_date date,
  created_at timestamp default now(),
  primary key (id)
);
```

Free users are limited to **3 analyses per day**. Paid users have unlimited access. Tier is managed directly in the `profiles` table.

---

## Prompt Design

The core of the app is a structured 10-section prompt that combines resume and JD inputs:

```python
FULL_PROMPT = """
You are an expert career coach and ATS optimization specialist.

## Match Score
Give a percentage (0-100%).

## Missing ATS Keywords
Comma-separated list only.

## Resume Strengths
3-4 bullet points of strengths relative to the job description.

## Tailored Resume Summary
2-3 sentence professional summary tailored to this specific role.

## Quantification Suggestions
Find 3-4 bullet points lacking metrics. Suggest improved versions.

## Action Verb Upgrades
Find 3-4 weak verbs. Suggest stronger replacements.

## Resume Gaps
2-3 bullet points of gaps relative to the job description.

## Role Seniority Alignment
Honest assessment of competitiveness for this role.

## Top 3 Resume Improvements
3 highest-impact changes ranked by priority.

## Interview Questions & STAR Answers
5 tailored questions with full STAR-method answers.

---
Job Description: {jd_text}
Resume: {resume_text}
"""
```

---

## Authentication Flow

```
User visits app
      ↓
Not logged in → Login screen (email/password or Google OAuth)
      ↓
Supabase authenticates → session stored in st.session_state
      ↓
Profile fetched from profiles table
      ↓
Tier checked → free or paid
      ↓
Free: 3 analyses/day enforced, paid sections locked
Paid: unlimited analyses, all sections unlocked
```

---

## Requirements

```
streamlit
groq
pypdf
python-docx
python-dotenv
supabase
```

---

## Roadmap

- [x] Resume parser — PDF, DOCX, plain text
- [x] 10-section LLM analysis prompt
- [x] Full Streamlit UI with custom dark theme
- [x] Supabase auth — email/password + Google OAuth
- [x] Free/paid tier enforcement with daily usage limits
- [x] Landing page deployed on Vercel
- [ ] Stripe payments — enforce paid tier via subscription
- [ ] Personal score history — track resume improvements over time
- [ ] Job market keyword trends — aggregate insights from user JDs
- [ ] Migrate frontend to Next.js + FastAPI for production

---

## What Type of AI Is This?

PrepAI is an **NLP application powered by a Large Language Model**. It uses structured prompt engineering to combine resume and job description inputs and generate contextually grounded career insights and interview responses. It is not a fine-tuned model or a RAG system — the intelligence lives in the prompt design and the underlying LLaMA 3.3 70B model served via Groq.

---

## License

MIT
