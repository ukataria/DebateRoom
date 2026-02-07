# Courtroom

**Courtroom** is an AI debate engine that turns any decision into a structured, evidence-locked courtroom trial. Users pose a dilemma (e.g. *"Should CMU require AI ethics courses?"*) and a system of specialized AI agents debates both sides in real time, with every factual claim backed by verifiable evidence from web sources, semantic search, and academic papers.

Users can intervene mid-debate — even mid-sentence — to redirect the argument. The output is not just a verdict, but an explanation that can be verified, understood, and believed.

> _Courtroom is adversarial problem solving: AI agents competing on evidence, not rhetoric, to answer your questions._

---

## Key Features

### Citation-Locked Arguments
Every claim must cite real evidence via `[TOOL:id]` references. Agents fetch sources from three MCP tool servers — Brave Search (web/news), Exa (semantic), and Valyu (academic papers from ArXiv, PubMed, and scholarly databases). This grounds model responses and dramatically reduces hallucination compared to standard chat-based LLMs.

### Adversarial Debate with Cross-Examination
A Defense agent argues in favor of the position while a Prosecution agent argues against it, dismantling the other side's reasoning with counter-evidence. After opening statements, a rapid cross-examination phase forces agents into concise, conversational exchanges that stress-test each side's arguments.

### Human-in-the-Loop Intervention
Users can interrupt any agent mid-sentence during opening statements or cross-examination. The system halts the current stream, accepts a user directive, and injects it into the next agent's context — putting humans in control of the debate's direction without restarting.

### Real-Time Streaming UI
A three-panel courtroom interface streams tokens live as agents generate them. Inline citation badges link directly to an evidence trail sidebar that populates in real time as agents discover sources. Expandable evidence cards show full metadata and link to original sources.

### Document Upload
Users can attach PDF documents (contracts, policies, research papers) that are processed via OCR and injected into agent context, enabling evidence-based analysis of specific documents.

---

## How It Works

### Debate Flow

The debate progresses through a structured sequence of phases:

```
INTAKE → DISCOVERY → DEFENSE OPENING → PROSECUTION OPENING
      → CROSS-EXAMINATION (6 rounds) → VERDICT
```

1. **Intake** — User enters a dilemma and optionally uploads a document
2. **Discovery** — The Court Researcher gathers 10+ pieces of evidence from all three MCP servers, building a neutral evidence base for both sides
3. **Defense Opening** — The Defense agent presents structured arguments in favor, citing evidence with confidence ratings
4. **Prosecution Opening** — The Prosecution agent counters with opposing arguments, directly addressing and dismantling the Defense's points
5. **Cross-Examination** — Rapid back-and-forth exchanges (3 rounds, 6 total turns) where agents challenge each other's weakest points using existing evidence only
6. **Verdict** — A neutral Judge analyzes the full transcript and delivers a structured verdict evaluating evidence quality, key exchanges, gaps, and a final recommendation

### Agent Architecture

| Agent | Role | Capabilities |
|-------|------|-------------|
| **Researcher** | Neutral evidence gathering | Searches Brave, Exa, and Valyu; formats evidence with unique IDs |
| **Defense** | Argues FOR the position | Cites evidence, structures arguments with confidence ratings |
| **Prosecution** | Argues AGAINST the position | Counter-argues, dismantles Defense points with opposing evidence |
| **Judge** | Neutral analysis and verdict | Evaluates full transcript, assesses evidence quality, delivers recommendation |

Agents use the Dedalus SDK with handoff model routing — faster models handle tool-heavy research while frontier models handle persuasive reasoning and analysis. The Judge uses a single frontier model with no tools for unbiased evaluation.

### Intervention System

The intervention system uses an `asyncio.Queue` that is checked between every stream chunk:

1. User clicks **Interrupt** — the current agent's stream is halted mid-sentence
2. User types a directive — it is stored as a `CourtDirective`
3. The directive is injected into the next agent's context, steering the debate without restarting

Interruptible phases: Defense Opening, Prosecution Opening, and Cross-Examination.

### WebSocket Protocol

The backend and frontend communicate over a single bidirectional WebSocket connection per session:

- **Server → Client**: Phase changes, streamed agent tokens, tool calls, evidence items, court directives, errors
- **Client → Server**: Start debate, interrupt, intervention content, start cross-examination

All messages are typed as Pydantic models on the backend and TypeScript discriminated unions on the frontend.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python 3.11+, Pydantic, asyncio, structlog |
| **Frontend** | React 19, TypeScript, Tailwind CSS, Vite |
| **AI** | Dedalus Labs SDK with MCP server integration |
| **Communication** | WebSockets (bidirectional streaming) |
| **MCP Servers** | Brave Search, Exa, Valyu (academic) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+
- A [Dedalus](https://dedalus.dev) API key

### Installation

**Backend:**
```bash
uv sync
```

**Frontend:**
```bash
cd frontend && npm install
```

### Environment

Create a `.env` file in the project root:
```bash
DEDALUS_API_KEY=your-key-here
```

### Running Locally

Launch the backend server:
```bash
uv run uvicorn backend.main:app --reload --port 8000
```

Launch the frontend dev server (in a separate terminal):
```bash
cd frontend && npm run dev
```

The frontend connects to the backend WebSocket at `ws://localhost:8000/ws/session` by default.

### Hosted Version

A public deployment is available at [courtroom.up.railway.app](https://courtroom.up.railway.app/).

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app + WebSocket endpoint
│   ├── orchestrator.py      # Debate state machine + phase transitions
│   ├── models.py            # Pydantic message schemas
│   ├── config.py            # Environment config + model constants
│   └── agents/
│       ├── prompts.py       # System prompts for all agents
│       ├── tools.py         # Citation tracking + evidence formatting
│       ├── researcher.py    # Researcher agent
│       ├── defense.py       # Defense agent
│       ├── prosecutor.py    # Prosecution agent
│       └── judge.py         # Judge agent
├── frontend/
│   └── src/
│       ├── App.tsx           # Root layout + routing
│       ├── types.ts          # TypeScript message types
│       ├── hooks/
│       │   └── useDebateSocket.ts  # WebSocket state management
│       └── components/
│           ├── DilemmaInput.tsx     # Input screen + file upload
│           ├── CourtPanel.tsx       # Defense/Prosecution panels
│           ├── EvidenceTrail.tsx    # Evidence sidebar
│           ├── InterventionBar.tsx  # Interrupt controls
│           ├── CrossExamView.tsx    # Cross-exam chat view
│           └── JudgeSummary.tsx     # Verdict display
└── pyproject.toml            # Python dependencies
```

---

## Acknowledgements

Thanks to everyone who helped us on making this project!

- **Scotty Labs** — Tartan Hacks organizers for putting together this project
- **Dedalus** — For providing mentorship on how to use multiple agents and their incredible sdk!
- **Conway** — For helping us work through multi-model debating, and thinking about how to design our UI. 
- Built with FastAPI, React, Dedalus Labs SDK, Tailwind CSS, and Vite

- Authors: Mehul Goel and Utsav Kataria 
