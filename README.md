# Synapse

**AI-Powered Codebase & Meeting Intelligence Platform**

`next.js` `fastapi` `pinecone` `assemblyai` `groq` `postgresql`

Synapse is a full-stack AI productivity tool for development teams. It reads your entire GitHub codebase and answers natural-language questions about it, generates AI summaries of commits, transcribes team meetings, and lets you ask questions about what was discussed — all powered by a Retrieval-Augmented Generation (RAG) pipeline so answers stay grounded in your actual code and conversations, not generic guesses.

🔗 [Live Demo](#)

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Screenshots](#-screenshots)
- [Tech Stack](#️-tech-stack)
- [Key Features](#-key-features)
- [How the AI Pipeline Works](#-how-the-ai-pipeline-works)
- [Architecture Highlights](#️-architecture-highlights)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Future Improvements](#-future-improvements)
- [Author](#-author)

---

## 🤖 Overview

Synapse takes the guesswork out of understanding a new codebase or catching up on a meeting you missed. Instead of manually digging through files or replaying recordings, it lets you just *ask*.

- **Link a Repo** — connect any GitHub repository and Synapse clones it, reads every file, and builds a searchable knowledge base of the code
- **Codebase Q&A** — ask plain-English questions like *"which file handles authentication?"* and get an answer grounded in the actual source
- **Commit Summaries** — poll recent commits and get AI-generated, plain-English summaries of what changed and why
- **Meeting Transcription** — upload a recording and Synapse transcribes it, extracts chapters, and makes it fully searchable
- **Meeting Q&A** — ask questions about anything discussed in a past meeting and get an answer with the relevant snippet as context

Built with **Next.js** on the frontend and **FastAPI (Python)** on the backend, with **AssemblyAI** for transcription, **Sentence-Transformers** for embeddings, **Pinecone** for vector search, and **Groq / Cohere** powering answer generation.

---

## 📸 Screenshots


*Ask a question, upload a meeting, and poll commits — all from one screen.*

![Synapse home dashboard](./assets/home-dashboard.png)

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend Framework | Next.js (App Router) + TypeScript | UI, routing, server components |
| API Layer | tRPC | Type-safe client–server communication |
| Database ORM | Prisma | Schema + queries for Postgres |
| Database | Neon (PostgreSQL) | Users, projects, meetings |
| Auth | Clerk | Authentication & session management |
| State Management | Jotai | Global client state |
| Styling | Tailwind CSS | UI styling |
| Backend | Python + FastAPI (async) | REST API, orchestration |
| Transcription | AssemblyAI | Audio → text + auto chapters |
| Text Chunking | LangChain | Splitting long text for embedding |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) | Local, free text-to-vector conversion |
| Vector Database | Pinecone | Similarity search over embeddings |
| LLM Providers | Groq (Llama) / Cohere | Answer generation |
| File Storage | Supabase | Uploaded audio storage |
| Codebase Access | GitPython | Clones and reads linked GitHub repos |

---

## 🔋 Key Features

### 🔍 Codebase Intelligence
- **Repo Linking** — connect a GitHub repository by URL; Synapse clones it and indexes the code
- **Natural-Language Q&A** — ask questions about structure, logic, or specific files
- **Automatic Documentation** — AI-generated summaries of source files for faster onboarding

### 📝 Commit Insights
- **Poll Commits** — pull recent commits from the linked repo
- **AI Summaries** — plain-English explanation of each commit's changes, generated from the diff

### 🎙️ Meeting Intelligence
- **Upload & Transcribe** — drop in an audio file, get a full transcript with auto-generated chapters (title, timestamp range, gist, headline, summary)
- **Ask Follow-Up Questions** — query anything said in the meeting and get an answer grounded in the transcript
- **Per-Meeting Namespaces** — each meeting's embeddings are isolated so answers never mix context across meetings

### 👥 Team Collaboration
- **Multi-Project Support** — manage several linked repos/projects from one dashboard
- **Invite Team Members** — bring collaborators into a project
- **Avatars & Activity** — see who's on a project and recent commit activity at a glance

---

## 🧠 How the AI Pipeline Works

```
Audio file uploaded
      │
      ▼
Stored in Supabase → URL passed to backend
      │
      ▼
AssemblyAI transcribes audio → chapters extracted
      │
      ▼
Transcript split into ~800-char chunks (130-char overlap)
      │
      ▼
Each chunk embedded in parallel (Sentence-Transformers, 384-dim)
      │
      ▼
Chunks + embeddings upserted into Pinecone (per-meeting namespace)
      │
      ▼
User asks a question
      │
      ├─ Question embedded
      ├─ Top-k similar chunks retrieved from Pinecone
      └─ Chunks passed as context to LLM (Groq/Cohere)
      │
      ▼
Grounded answer returned to user
```

The same retrieve → augment → generate pattern powers codebase Q&A: the repo's files replace the meeting transcript as the source content that gets chunked, embedded, and searched.

---

## 🏗️ Architecture Highlights

- **Separate Frontend/Backend Services** — Next.js client talks to a standalone FastAPI service over HTTP; each can be deployed and scaled independently
- **Async-First Backend** — FastAPI routes use `async`/`await` throughout, with `asyncio.gather` to generate embeddings for multiple chunks concurrently instead of sequentially
- **Local Embeddings, No Per-Query API Cost** — embeddings run on-device via Sentence-Transformers rather than a paid API, since the chosen LLM provider (Groq) doesn't offer an embeddings endpoint
- **Per-Namespace Vector Isolation** — each meeting gets its own Pinecone namespace so retrieval never leaks context between unrelated meetings
- **Type-Safe API Layer** — tRPC gives end-to-end TypeScript types between frontend and the Node-side API layer, catching mismatches at compile time

---

## 📁 Project Structure

```
Synapse/
│
├── backend/
│   ├── main.py             # FastAPI entry point — all API routes
│   ├── assembly.py         # Meeting transcription + Q&A (AssemblyAI, Pinecone, embeddings)
│   ├── _openai.py          # LLM (Groq) + local embeddings (sentence-transformers)
│   ├── cohere.py           # Cohere LLM integration
│   ├── GithubLoader.py     # Clones & loads GitHub repos for codebase Q&A
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                # API keys (not committed)
│
└── webapp/
    ├── src/
    │   ├── app/             # Next.js App Router pages
    │   │   ├── projects/[projectId]/
    │   │   ├── meetings/[projectId]/
    │   │   ├── meeting/[meetingId]/
    │   │   ├── documentation/[projectId]/
    │   │   ├── qna/[projectId]/
    │   │   └── favicon.ico
    │   ├── components/      # Reusable React components (MeetingCard, etc.)
    │   ├── server/          # tRPC routers, Prisma client
    │   └── styles/globals.css
    ├── prisma/
    │   └── schema.prisma
    └── .env                 # Database URL, Clerk keys (not committed)
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js v18+
- Python 3.10
- Git
- API keys/accounts: Pinecone, AssemblyAI, Groq, Cohere (optional), Clerk, Neon, Supabase

### 1. Clone
```bash
git clone https://github.com/<your-username>/Synapse.git
cd Synapse
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows
pip install -r requirements.txt
pip install pinecone sentence-transformers
```

### 3. Frontend Setup
```bash
cd ../webapp
npm install
```

### 4. Environment Variables
See [Environment Variables](#-environment-variables) below.

### 5. Run

```bash
# Terminal 1 — backend
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd webapp
npm run dev
```

Open `http://localhost:3000`.

---

## 🔐 Environment Variables

**`backend/.env`**

| Variable | Description |
|---|---|
| `PINECONE_API_KEY` | Pinecone vector database API key |
| `AAI_TOKEN` | AssemblyAI transcription API key |
| `OPENAI_API_KEY` | Groq API key (used via OpenAI-compatible endpoint) |
| `COHERE_API_KEY` | Cohere API key (optional, alternate LLM) |

**`webapp/.env`**

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk public key |
| `CLERK_SECRET_KEY` | Clerk secret key |

---

## 🔭 Future Improvements

- Multi-repo codebase Q&A that reasons across linked projects together
- Speaker diarization for meeting transcripts (who said what)
- Slack/Discord integration for commit and meeting summaries
- Exportable PDF reports for meeting summaries and codebase docs
- Support for additional embedding/LLM providers as fallback
- Real-time collaborative Q&A sessions on the same project

---

## 👨‍💻 Author

**[Your Name]**

- GitHub: [@your-username](#)
- Repository: [Synapse](#)
