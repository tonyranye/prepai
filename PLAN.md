# PrepAI — Streamlit → Next.js 16 + TypeScript + FastAPI Migration Plan

> **Goal:** A fully functional Next.js frontend talking to a FastAPI backend, with Supabase auth, before any deployment work begins.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Python |
| Auth | Supabase (email/password + Google OAuth PKCE) |
| LLM | Groq (llama-3.3-70b) |
| File Parsing | pypdf, python-docx |
| Deployment (later) | Vercel (frontend) + Railway or Render (backend) |

---

## Current State Snapshot

| File | Status | Notes |
|---|---|---|
| `backend/main.py` | ✅ Done | FastAPI routes wired up |
| `backend/parser.py` | ✅ Done | PDF/DOCX parsing works |
| `backend/llm.py` | ✅ Done | Groq call + section parser |
| `backend/auth.py` | ⚠️ Needs refactor | Hardcoded Streamlit redirect URL, no JWT middleware |
| `frontend/` | 🏗️ Scaffolded | Next.js 16 + React 19 + Tailwind 4 + TypeScript bootstrapped |

---

## Project Folder Structure (target)

```
prepai/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── llm.py
│   ├── parser.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── app/
    │   ├── layout.tsx            # root layout, fonts, global providers
    │   ├── page.tsx              # landing / home page
    │   ├── login/
    │   │   └── page.tsx
    │   ├── signup/
    │   │   └── page.tsx
    │   ├── auth/
    │   │   └── callback/
    │   │       └── page.tsx      # handles ?code= from Google OAuth
    │   ├── dashboard/
    │   │   └── page.tsx          # protected — resume + JD input
    │   └── results/
    │       └── page.tsx          # protected — shows all 10 sections
    ├── components/
    │   ├── Navbar.tsx
    │   ├── ResumeInput.tsx       # paste text OR file upload toggle
    │   ├── JDInput.tsx
    │   ├── UsageBanner.tsx       # shows X/3 free analyses remaining
    │   ├── MatchScore.tsx
    │   └── ResultsSections.tsx   # renders all 10 parsed sections
    ├── lib/
    │   ├── api.ts                # fetch wrapper with base URL + auth header
    │   ├── auth.ts               # Supabase client-side helpers
    │   └── types.ts              # shared TypeScript interfaces
    ├── context/
    │   └── AuthContext.tsx       # React context for user/session state
    ├── hooks/
    │   └── useAuth.ts            # convenience hook wrapping AuthContext
    ├── middleware.ts             # route protection (place at frontend root)
    ├── next.config.ts
    ├── tsconfig.json
    └── package.json
```

---

## Phase 1 — Fix the Backend (Python)

### 1A. Refactor `auth.py`

**Problems to fix:**
- `redirect_to` is hardcoded to `https://interviewcoach-ai.streamlit.app` — replace with env var pointing to Next.js
- No JWT verification helper for protecting FastAPI routes

**What to add:**
```python
# New helper — verify Bearer token from Next.js and extract user
def get_user_from_token(token: str):
    try:
        res = supabase.auth.get_user(token)
        return res.user
    except Exception:
        return None
```

**Updated redirect URL in `sign_in_with_google()`:**
```python
"redirect_to": os.getenv("OAUTH_REDIRECT_URL", "http://localhost:3000/auth/callback"),
```

**Backend `.env` — add:**
```
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback
```

---

### 1B. Add Auth Middleware to `main.py`

Add a reusable FastAPI dependency to protect routes:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import get_user_from_token, check_and_increment_usage

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
```

Protect the analyze routes:
```python
@app.post("/api/analyze/text")
async def analyze_text(request: AnalyzeTextRequest, user=Depends(get_current_user)):
    usage = check_and_increment_usage(user.id)
    if not usage["allowed"]:
        raise HTTPException(status_code=429, detail="Daily analysis limit reached. Upgrade to continue.")
    ...
```

---

### 1C. Add Auth Routes to `main.py`

Next.js needs these endpoints to drive the auth flow:

```
POST /api/auth/signup        { email, password }
POST /api/auth/signin        { email, password }
POST /api/auth/google        → returns { url } to redirect browser to Google
GET  /api/auth/callback?code=... → exchanges PKCE code, returns { session, user }
POST /api/auth/signout
GET  /api/auth/me            → returns profile (protected)
```

---

### 1D. Add a `/api/usage` Route

```
GET /api/usage   (protected)  → { analyses_today, remaining, tier }
```

---

### 1E. Update CORS in `main.py`

Change the allowed origins from port 5173 (old Vue plan) to port 3000 (Next.js):

```python
allow_origins=[
    "http://localhost:3000",   # Next.js dev server
],
```

---

### Backend `.env` (full list):
```
SUPABASE_URL=
SUPABASE_ANON_KEY=
GROQ_API_KEY=
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback
```

---

## Phase 2 — Frontend Setup

### 2A. Install Additional Dependencies

The scaffold is ready — just add Supabase:

```bash
cd frontend
npm install @supabase/supabase-js
```

> No Axios needed — Next.js uses the native `fetch` API.

---

### 2B. Environment Variables

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

> `NEXT_PUBLIC_` prefix is required for values accessible in the browser.

---

### 2C. Auth Strategy

**Approach:** Supabase client-side auth with React Context

- Store session in memory via `AuthContext.tsx`
- Persist the access token in `sessionStorage` (cleared on tab close — more secure than `localStorage`)
- Pass `Authorization: Bearer <token>` header on every FastAPI call via `lib/api.ts`
- Set a lightweight cookie on login for Next.js `middleware.ts` to read (middleware runs on the Edge and cannot access `sessionStorage`)

```typescript
// middleware.ts  (place at frontend root, next to package.json)
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('sb-token')?.value
  const protectedPaths = ['/dashboard', '/results']
  const isProtected = protectedPaths.some(p => request.nextUrl.pathname.startsWith(p))

  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/results/:path*'],
}
```

---

### 2D. `lib/api.ts` — Fetch Wrapper

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem('sb-token')
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({}))
    throw new Error(error.detail ?? `API error ${res.status}`)
  }
  return res.json()
}
```

---

### 2E. `lib/types.ts` — Shared Interfaces

```typescript
export interface AnalysisSections {
  'Match Score': string
  'Missing ATS Keywords': string
  'Resume Strengths': string
  'Tailored Resume Summary': string
  'Quantification Suggestions': string
  'Action Verb Upgrades': string
  'Resume Gaps': string
  'Role Seniority Alignment': string
  'Top 3 Resume Improvements': string
  'Interview Questions & STAR Answers': string
}

export interface AnalyzeResponse {
  sections: AnalysisSections
  raw: string
}

export interface UserProfile {
  id: string
  email: string
  tier: 'free' | 'paid'
  analyses_today: number
  remaining: number
}
```

---

## Phase 3 — Pages Build Order (recommended sequence)

Build and test each page before moving to the next:

1. **`/login` + `/signup`** — email/password forms → calls FastAPI auth endpoints → stores token in `sessionStorage`, sets `sb-token` cookie → redirects to `/dashboard`
2. **`/auth/callback`** — reads `?code=` from URL → calls `GET /api/auth/callback` → stores session → redirects to `/dashboard`
3. **`/dashboard`** — protected — usage banner, resume input (text/file toggle), JD textarea, submit → calls `/api/analyze/text` or `/api/analyze/file` → navigates to `/results`
4. **`/results`** — protected — renders all 10 sections from stored analysis state
5. **`Navbar`** — email display, logout button (clears token + cookie → redirects to `/login`)

---

## Phase 4 — Integration Testing Checklist

Before deployment, verify each flow manually:

- [ ] Sign up with email → profile row created in Supabase `profiles` table
- [ ] Sign in with email → token stored, `/dashboard` accessible
- [ ] Unauthenticated visit to `/dashboard` → redirected to `/login`
- [ ] Sign in with Google → browser redirected to Google → callback page → session stored → `/dashboard`
- [ ] Sign out → token cleared, cookie cleared, redirect to `/login`
- [ ] Free user: 3 analyses allowed, 4th returns 429 with upgrade message
- [ ] Paid user: unlimited analyses
- [ ] Paste resume text + JD → all 10 sections render correctly
- [ ] Upload PDF → text extracted → results render correctly
- [ ] Upload DOCX → text extracted → results render correctly
- [ ] Refresh `/results` page → doesn't crash (handle missing state gracefully)

---

## Phase 5 — Deployment (do this last)

### Backend (FastAPI)
- Deploy to **Railway** (recommended) or **Render**
- Set all backend `.env` vars in the platform dashboard
- Update `OAUTH_REDIRECT_URL` to your production frontend URL (e.g. `https://prepai.vercel.app/auth/callback`)
- Update CORS `allow_origins` to include your production frontend domain

### Frontend (Next.js)
- Deploy to **Vercel** — native Next.js support, zero config
- Set env vars in Vercel dashboard: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- In Supabase dashboard → Auth → Redirect URLs: add `https://prepai.vercel.app/auth/callback`

---

## Immediate Next Steps (start here)

```
Step 1 → Refactor backend/auth.py
         - Replace hardcoded Streamlit redirect with OAUTH_REDIRECT_URL env var
         - Add get_user_from_token() helper

Step 2 → Update backend/main.py
         - Change CORS origin to http://localhost:3000
         - Add get_current_user() dependency
         - Add /api/auth/* routes
         - Add /api/usage route
         - Protect /api/analyze/* with Depends(get_current_user)

Step 3 → Frontend scaffolding
         - npm install @supabase/supabase-js
         - Create .env.local
         - Create lib/api.ts, lib/types.ts, lib/auth.ts
         - Create context/AuthContext.tsx + hooks/useAuth.ts
         - Add middleware.ts for route protection

Step 4 → Build /login + /signup, test email auth end-to-end

Step 5 → Build /auth/callback, test Google OAuth end-to-end

Step 6 → Build /dashboard (resume + JD inputs, call analyze API)

Step 7 → Build /results (render all 10 sections)
```

---

## Key Decisions

| Decision | Choice | Notes |
|---|---|---|
| Frontend framework | Next.js 16 App Router | Already scaffolded ✅ |
| Token storage | `sessionStorage` + cookie | Cookie for middleware guards, sessionStorage for API calls |
| State management | React Context | No Redux/Zustand needed at this scale |
| File upload | Native `fetch` with `FormData` | No extra libraries needed |
| Paid tier billing | Stripe | Defer until after MVP |
| Production backend host | Railway | Easiest FastAPI deployment DX |
