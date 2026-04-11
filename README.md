# 🇦🇺 Aussie Real Estate Agent AI

**Aussie Real Estate Agent AI** is a premium, AI-powered proptech platform designed for the Australian property market. It leverages advanced LLMs (Gemini, GPT-4, Claude) and specialized real estate data tools to provide high-value insights for investors, developers, and first-home buyers.

The application combines a modern React/Next.js frontend with a robust FastAPI backend powered by LangGraph for complex agentic workflows.

---

## 🚀 Key Features

- **🏠 Smart Property Search**: Search for live listings on Domain and Realestate.com.au using natural language.
- **🏗️ Development Feasibility**: Instantly calculate the potential for subdivisions or duplexes based on site area, zoning (e.g., R2, R3), and purchase price.
- **📈 Suburb Growth Engine**: Analyze growth potential using ABS data trends, local infrastructure projects, and vacancy rates.
- **📊 Portfolio Advisor**: Manage and optimize your property portfolio with LVR (Loan-to-Value Ratio) analysis and equity release suggestions.
- **📄 Document Intelligence**: Automatically extract risks and key conditions from Contracts of Sale, Strata Reports, and Building & Pest reports.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Orchestration**: [LangGraph](https://www.langchain.com/langgraph) & [LangChain](https://www.langchain.com/)
- **Models**: Google Gemini (Flash/Pro), OpenAI, Anthropic
- **Search**: [Tavily AI](https://tavily.com/)
- **Data Handling**: Pandas, NumPy

### Frontend
- **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Maps**: [Leaflet](https://leafletjs.com/) & React Leaflet
- **Icons**: [Lucide React](https://lucide.dev/)

---

## ⚙️ Getting Started

### Prerequisites
- Docker & Docker Compose
- API Keys for:
    - Google AI (Gemini)
    - Tavily (for web search)
    - (Optional) Groq / OpenAI / Anthropic

### 1. Environment Configuration

Create a `.env` file in the `backend/` directory based on the following template:

```env
GOOGLE_API_KEY=your_google_key
TAVILY_API_KEY=your_tavily_key
MODEL_NAME=gemini-1.5-flash
# Optional
GROQ_API_KEY=your_groq_key
```

### 2. Run with Docker (Recommended)

The easiest way to start the entire stack is using Docker Compose:

```bash
docker-compose up --build
```

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Manual Installation

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Project Structure

```text
.
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── app.py               # Main API logic & routing
│   ├── agent_engine.py      # LangGraph agent configuration
│   ├── tools_realestate.py  # Specialized PropTech tools
│   ├── models.py            # Pydantic schemas
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/app/             # Next.js App Router (Pages & Components)
│   ├── public/              # Static assets
│   └── package.json         # Node.js dependencies
└── docker-compose.yml       # Container orchestration
```

---

## 🧠 Architecture

The system uses a **ReAct Agent** architecture via LangGraph:
1. **User Query**: Received via the Next.js frontend.
2. **Agent Engine**: Parses the intent and decides which tool to use.
3. **Tool Execution**:
   - `search_properties`: Scrapes/Searches market listings.
   - `calculate_feasibility`: Runs geometric and financial models for development.
   - `analyze_suburb_growth`: Fetches infrastructure and economic data.
4. **Contextual Reasoning**: The LLM synthesizes tool outputs with current economic news to provide a professional response.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built with ❤️ for the Australian PropTech community.*
