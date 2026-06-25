# Novestate

- (This app have two modes - traditional dashboard and Full Agent Mode. In Full Agent Mode it act as a real estate agent and provide reports to clients.)
- In full agent mode its just a chat interface where user can ask for details reports any query.
- Also chat exists in the dashboard version too
- In full agent mode there is a side bar to navigate to reports and analysis sections.

A full-stack, AI-driven real estate intelligence platform generating comprehensive market reports for the Australian market.

## Features

- **Location Search**: Look up any suburb in Australia via the Nominatim API.
- **Automated Report Generation**: Aggregates data from Domain.com.au (comparable properties, median prices) and uses Gemini 1.5 Flash for deep market synthesis.
- **Caching**: Leverages Redis for aggressive caching of external API calls to minimize latency and costs.
- **Authentication**: JWT-based authentication with NextAuth (Google & Credentials).
- **Pro Tier**: Support for Free vs Pro tiers, including PDF exports and deeper analytics limits.
- **Interactive Dashboard**: View previously generated reports.

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, Redis, WeasyPrint, Pytest, Hypothesis.
- **Frontend**: Next.js 14, Tailwind CSS, shadcn/ui, Framer Motion.

## Getting Started

1. Clone the repository.
2. Obtain the necessary API keys (see `how-to-get-apis.md`).
3. Copy `.env.example` to `.env` and fill in your keys.
4. Run `docker-compose up --build`.
5. Access the app at `http://localhost:3000`.

## Testing

Run the full test suite (including property-based tests) by executing:

```bash
cd backend
pytest tests/ -v
```

```bash
cd frontend
npm run test
```

## Architecture

See the `docs` folder for architectural diagrams, sequence diagrams, and schema definitions.
