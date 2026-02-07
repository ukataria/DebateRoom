# Court Room

**Courtroom** is an adversarial evidence-locked decision engine. A user poses any dilemma ("Should CMU require AI ethics courses?"), and a system of AI agents debates it like a courtroom trial — except every claim must be backed by real evidence fetched via MCP tool calls. Users can intervene mid-debate _even mid-sentence_ to shift the argument. The output is not just a verdict, but an explanation that can be verified, understood, and believed.

More simply: _Courtroom is adversarial problem solving: AI agents competing on evidence, not rhetoric to answer your questions._

## How to use Court Room

The website is being hosted publically [here](https://debateroom-production.up.railway.app/).

### Host Locally
To host locally, you need to install the prequisite instructions (TODO: Fill this out)

To run this website locally, it consists of a backend and frontend server, all connected through fast api. 

To launch backend python server: 
```
uv run uvicorn backend.main:app --reload --port 8000
```

To launch the frontend React website:
```
npm run dev
```

## Key Features: 
(TODO: Elaborate)

1. Citation based arguments (leads to grounded reasoning and heightened LLM performance) 
2. Adversarial debate, leads to reasoning understandings and better arguments between LLMs (Include crossfire)
3. Interruption, allows puting humans in the loop. 
4. Rich feature support: Multi modal documents, confidence intervals, user focused UI

## How it works
TODO: Quick system design explanation


### Explanation of models
TODO: Fill this out

### Fast API Handshake
TODO: Fill this out

### React Frontend
TODO: Fill this out

## Acknowledgements (TODO: Fill out)
- Scotty Labs (Tartan Hacks Organizers)
- Dedalus for api credits + mentorship on api
- Conway for mentorship on multi modal debate
- React etc. frameworks
