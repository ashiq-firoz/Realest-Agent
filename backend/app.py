# -*- coding: utf-8 -*-
"""
Supervisor-Fleet Benchmark API
================================
Tests whether a supervisor LLM can:
  1. Coordinate a dynamically-defined fleet of agents.
  2. Accurately identify which agent caused a failure.
  3. Autonomously remediate errors and complete the task.

Run with:
    uvicorn app:app --reload
"""

import json as _json
import os
import re as _re
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
from langchain_tavily import TavilySearch
from langchain_xai import ChatXAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field as PydanticField
from typing_extensions import TypedDict

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Token Pricing Configuration (per 1M tokens)
# ---------------------------------------------------------------------------

TOKEN_PRICING = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.8, "output": 4.0},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "llama-3.3-70b": {"input": 0.59, "output": 0.79},
    "llama-2-70b": {"input": 0.7, "output": 0.9},
    "mistral-large": {"input": 2.7, "output": 8.1},
    "mistral-medium": {"input": 2.7, "output": 8.1},
    "mistral-small": {"input": 0.14, "output": 0.42},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-coder": {"input": 0.14, "output": 0.28},
    "default": {"input": 0.5, "output": 1.5},  # fallback pricing
}

# ---------------------------------------------------------------------------
# Intelligence Metrics Utilities
# ---------------------------------------------------------------------------

_embedding_model = None

def get_embedding_model():
    """Lazy-load the embedding model."""
    global _embedding_model
    if _embedding_model is None and EMBEDDINGS_AVAILABLE:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def extract_trajectory_texts(trajectory: List[Dict]) -> List[str]:
    """
    Extract meaningful text from trajectory events for semantic similarity analysis.
    Returns a list of text snippets representing each step.
    """
    texts = []
    for event in trajectory:
        event_type = event.get("event_type", "")
        agent = event.get("agent", "")
        details = event.get("details", {})
        
        if event_type == "ENTER":
            task = details.get("task_prompt_snippet", "")
            if task:
                texts.append(f"{agent}: {task}")
        elif event_type == "EXIT_SUCCESS":
            output = details.get("output_snippet", "")
            if output:
                texts.append(f"{agent} output: {output}")
        elif event_type == "SUPERVISOR_ANALYSIS":
            root_cause = details.get("root_cause", "")
            if root_cause:
                texts.append(f"Analysis: {root_cause}")
        elif event_type == "SUPERVISOR_REMEDIATION":
            new_prompt = details.get("new_task_prompt_snippet", "")
            if new_prompt:
                texts.append(f"Remediation: {new_prompt}")
    
    return texts if texts else [""]

def calculate_embeddings(texts: List[str]) -> Optional[np.ndarray]:
    """Calculate embeddings for a list of texts using SentenceTransformer."""
    if not EMBEDDINGS_AVAILABLE or not texts or (len(texts) == 1 and texts[0] == ""):
        return None
    
    model = get_embedding_model()
    if model is None:
        return None
    
    try:
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings
    except Exception as e:
        print(f"Warning: Could not compute embeddings: {e}")
        return None

def calculate_useful_count(trajectory: List[Dict], embeddings: Optional[np.ndarray], 
                          user_request: str) -> Dict[str, Any]:
    """
    Calculate useful_count based on semantic similarity.
    
    useful_count = count of steps where:
      - similarity_to_prev < 0.85 (step is diverging from previous, not repeating)
      - similarity_to_goal > 0.3 (step is somewhat aligned with the goal)
    
    Returns a dict with useful_count, total_steps, and per-step analysis.
    """
    if embeddings is None or len(embeddings) < 2:
        return {
            "useful_count": len(trajectory) if trajectory else 0,
            "total_steps": len(trajectory),
            "analysis": "No embeddings available; counting all trajectory events as useful"
        }
    
    # Encode the user request as the goal
    goal_texts = [user_request]
    goal_model = get_embedding_model()
    if goal_model is None:
        return {
            "useful_count": len(trajectory),
            "total_steps": len(trajectory),
            "analysis": "Embedding model unavailable; defaulting to all events"
        }
    
    goal_embeddings = goal_model.encode(goal_texts, convert_to_numpy=True)
    goal_embedding = goal_embeddings[0]
    
    useful_count_list = []
    step_analyses = []

    # taskgen workflow
    # its not why,
    # its they have no work etique, they should keep their jokes to themselves and
    # if dont know hindi , they just ignore you.
    # there is no proper team
    # dont understand why research guy got the sde task thing when i dont even know how the
    # tasks are generated, initally reading proposal i thought they have a human team of experts
    # but they dont, they use claude to create these data and 
    # one thing that I know is that they dont actually know anything, they all got this job because of sst
    # sst is a good business plan, tell pros that they need to learn and sell course
    # tell students that college wont give you placements and knowledge
    # fun part is that they dont have any recognition so they ask the students to get a online degree from bits
    # and college life, if working 24x7 is college life then they are having it.
    # even their jokes cannot be even considered as a joke, its just some random thing
    # the pros who took scaler, nptel have the same course for way less money
    # they hired a research guy to do sde , that's cracked
    # i feel that people here dont sleep
    # should i worry
    # im not feeling well so, need to ask him for sick leave
    # these sst people dont have any manners, its just too annoying and they just ignore all of us
    # why are they like this
    # using only claude like they need it, they are the group who cant even imagine coding as a art
    # i want to work with a senior reasearch person, expecting it to happen next month
    
    for i in range(len(embeddings)): 
        current_embedding = embeddings[i]
        
        # Calculate similarity to goal
        goal_sim = float(cosine_similarity([current_embedding], [goal_embedding])[0][0])
        
        # Calculate similarity to previous step
        prev_sim = 1.0 if i == 0 else float(cosine_similarity([current_embedding], [embeddings[i-1]])[0][0])
        
        # Determine if this step is useful
        is_useful = (prev_sim < 0.85) and (goal_sim > 0.4)
        useful_count_list.append(is_useful)
        
        step_analyses.append({
            "step": i,
            "similarity_to_prev": round(prev_sim, 3),
            "similarity_to_goal": round(goal_sim, 3),
            "is_useful": is_useful
        })
    
    return {
        "useful_count": sum(useful_count_list),
        "total_steps": len(embeddings),
        "step_analyses": step_analyses,
        "analysis_details": {
            "threshold_divergence_from_prev": 0.85,
            "threshold_alignment_to_goal": 0.3
        }
    }

def get_model_pricing(model_name: str) -> Dict[str, float]:
    """Get pricing for a model, with fuzzy matching fallback."""
    model_lower = model_name.lower()
    
    # Direct match
    for key in TOKEN_PRICING:
        if key in model_lower:
            return TOKEN_PRICING[key]
     
    # Keyword-based matching
    if "gpt-4o" in model_lower:
        return TOKEN_PRICING["gpt-4o"]
    if "gpt-4" in model_lower:
        return TOKEN_PRICING["gpt-4"]
    if "gpt-3.5" in model_lower:
        return TOKEN_PRICING["gpt-3.5-turbo"]
    if "claude-3.5" in model_lower:
        return TOKEN_PRICING["claude-3.5-sonnet"]
    if "claude-3" in model_lower:
        if "opus" in model_lower:
            return TOKEN_PRICING["claude-3-opus"]
        elif "sonnet" in model_lower:
            return TOKEN_PRICING["claude-3-sonnet"]
        elif "haiku" in model_lower:
            return TOKEN_PRICING["claude-3-haiku"]
    if "llama-3.3" in model_lower:
        return TOKEN_PRICING["llama-3.3-70b"]
    if "llama" in model_lower:
        return TOKEN_PRICING["llama-2-70b"]
    if "mistral-large" in model_lower:
        return TOKEN_PRICING["mistral-large"]
    if "mistral-small" in model_lower:
        return TOKEN_PRICING["mistral-small"]
    if "mistral" in model_lower:
        return TOKEN_PRICING["mistral-medium"]
    if "deepseek" in model_lower:
        if "coder" in model_lower:
            return TOKEN_PRICING["deepseek-coder"]
        return TOKEN_PRICING["deepseek-chat"]
    
    # Fallback
    return TOKEN_PRICING["default"]

def estimate_token_usage(trajectory: List[Dict]) -> Dict[str, int]:
    """
    Estimate token usage from trajectory events.
    Heuristic: ~4 chars per token (rough approximation).
    """
    total_input_chars = 0
    total_output_chars = 0
    event_count = 0
    
    for event in trajectory:
        event_type = event.get("event_type", "")
        details = event.get("details", {})
        
        if event_type == "ENTER":
            task = details.get("task_prompt_snippet", "") or details.get("prompt", "")
            persona = details.get("persona_snippet", "") or ""
            total_input_chars += len(task) + len(persona)
        elif event_type == "EXIT_SUCCESS":
            output = details.get("output_snippet", "") or ""
            total_output_chars += len(output) 
        elif event_type == "SUPERVISOR_ANALYSIS":
            analysis_text = details.get("root_cause", "") or ""
            total_input_chars += len(analysis_text)
        elif event_type == "SUPERVISOR_REMEDIATION":
            remediation = details.get("new_persona_snippet", "") or details.get("new_task_prompt_snippet", "") or ""
            total_input_chars += len(remediation)
    
    # Rough approximation: ~4 characters per token
    estimated_input_tokens = max(total_input_chars // 4, 10)
    estimated_output_tokens = max(total_output_chars // 4, 10)
    
    #5 30 630 what is this dreamliner
    #its been two months still just people who talk work, noting much.
    # i miss discussions with research people, i want a phd guy on my team.
    # since its a new role, let it handle #clean this

    return {
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "total_estimated_tokens": estimated_input_tokens + estimated_output_tokens
    }

def calculate_intelligence_per_cost(
    trajectory: List[Dict],
    user_request: str,
    model_name: str,
) -> Dict[str, Any]:
    """
    Calculate the Intelligence per Cost metric.
    
    Intelligence = useful_count / total_steps (a measure of efficiency)
    Cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    Intelligence per Cost = Intelligence / Cost
    """
    # Extract trajectory texts and calculate embeddings
    texts = extract_trajectory_texts(trajectory)
    embeddings = calculate_embeddings(texts)
    
    # Calculate useful_count
    useful_metrics = calculate_useful_count(trajectory, embeddings, user_request)
    useful_count = useful_metrics.get("useful_count", len(trajectory))
    total_steps = useful_metrics.get("total_steps", 1)
    
    # Avoid division by zero
    if total_steps == 0:
        total_steps = 1
    
    # Calculate intelligence (0 to 1, where 1 is perfect efficiency)
    intelligence_score = useful_count / total_steps

    # need to verify how usefull_count is calculated.
    # usefull instructions are instructions which # clean all
    
    # Estimate token usage
    token_usage = estimate_token_usage(trajectory)
    input_tokens = token_usage["estimated_input_tokens"]
    output_tokens = token_usage["estimated_output_tokens"]
    #estimated_output_tokens take it from model.max_token

    
    # Get model pricing
    pricing = get_model_pricing(model_name)
    input_price_per_m = pricing["input"]
    output_price_per_m = pricing["output"]
    # update this model_pricing
    
    # Calculate cost (in USD)
    # Pricing is per 1M tokens, so divide by 1,000,000
    cost = (input_tokens * input_price_per_m + output_tokens * output_price_per_m) / 1_000_000
    
    # Avoid division by zero
    if cost <= 0:
        cost = 0.0001  # Set to tiny value to avoid inf
    
    # Calculate intelligence per cost
    intelligence_per_cost = intelligence_score / cost if cost > 0 else 0
    
    return {
        "intelligence_score": round(intelligence_score, 4),
        "useful_count": useful_count,
        "total_steps": total_steps,
        "useful_efficiency": useful_metrics,
        "token_usage": token_usage,
        "cost": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": token_usage["total_estimated_tokens"],
            "input_price_per_1m": input_price_per_m,
            "output_price_per_1m": output_price_per_m,
            "total_cost_usd": round(cost, 6),
        },
        "intelligence_per_cost": round(intelligence_per_cost, 4),
        "model_used": model_name,
        "notes": "Intelligence = useful_count / total_steps. Useful steps are those that diverge from previous (sim < 0.85) AND align to goal (sim > 0.3). Cost calculated in USD based on token pricing."
    }

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Supervisor-Fleet Benchmark API",
    description="""
## Supervisor-Fleet Benchmark

Evaluates a **Supervisor LLM** orchestrating a fleet of **dynamic agents**.

### Benchmark Goals
1. **Coordination** — Supervisor reads user input, decides sub-agent personas and task prompts dynamically.
2. **Execution** — Sub-agents execute their assigned task and return a structured result (output + status) to the supervisor.
3. **Failure Attribution** — Supervisor reads trajectory logs and pinpoints the failing agent.
4. **Autonomous Remediation** — Supervisor rewrites the agent's persona and task prompt, then retries until success or max retries exhausted.

### Provider Auto-Detection (from `model_name`)
| Keyword in model name | Provider used |
|---|---|
| `gpt` | openai |
| `llama` | groq |
| `mistral` | mistral |
| `claude` | anthropic |
| `grok` | xai |
| `deepseek` | deepseek |
| *(anything else)* | openrouter |
""",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic I/O Models
# ---------------------------------------------------------------------------

class AgentDefinition(BaseModel):
    """Defines a single agent in the fleet."""
    name: str = Field(..., description="Unique name for this agent (e.g. 'Analyst', 'Summarizer').")
    persona: str = Field(..., description="Full system-prompt / persona for this agent.")
    use_search: bool = Field(False, description="If true, bind the Tavily search tool to this agent.")


class BenchmarkRequest(BaseModel):
    model_name: str = Field(
        ...,
        description=(
            "Model ID. Provider is auto-detected from the name: "
            "'gpt'->openai, 'llama'->groq, 'mistral'->mistral, 'claude'->anthropic, "
            "'grok'->xai, 'deepseek'->deepseek, anything else->openrouter."
        ),
        examples=["llama-3.3-70b-versatile", "claude-3-5-sonnet-20241022", "stepfun/step-3.5-flash:free"],
    )
    model_api_key: str = Field(..., description="API key for the auto-detected provider.")
    TAVILY_API_KEY: str = Field("", description="Tavily key — required only when an agent has use_search=true.")
    user_request: str = Field(..., description="The task to execute across the agent fleet.")
    agents: List[AgentDefinition] = Field(
        ...,
        min_length=1,
        description="Fleet of agents. At least one agent must be defined.",
    )
    max_retries: int = Field(3, ge=1, le=10, description="Maximum supervisor-driven remediation retries per failing agent.")
    induce_failure: bool = Field(False, description="If true, intentionally trigger a failure for the agent specified in inject_failure.")
    inject_failure: Optional[str] = Field(
        None,
        description=(
            "(Optional) Name of an agent to intentionally break for benchmarking failure-detection. "
            "Requires induce_failure=true to trigger."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model_name": "llama-3.3-70b-versatile",
                    "model_api_key": "gsk_xxx",
                    "TAVILY_API_KEY": "tvly-xxx",
                    "user_request": "Research the latest AI trends and write a Python script to visualise them.",
                    "agents": [
                        {
                            "name": "Researcher",
                            "persona": "You are an expert researcher. Use your search tool to find accurate, up-to-date information.",
                            "use_search": True,
                        },
                        {
                            "name": "Coder",
                            "persona": "You are a senior Python developer. Write clean, runnable code.",
                            "use_search": False,
                        },
                    ],
                    "max_retries": 3,
                    "induce_failure": True,
                    "inject_failure": "Researcher",
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Trajectory Log Models
# ---------------------------------------------------------------------------

class TrajectoryEvent(BaseModel):
    event_id: str
    timestamp: str
    agent: str
    event_type: Literal[
        "ENTER",
        "EXIT_SUCCESS",
        "EXIT_FAILURE",
        "SUPERVISOR_ANALYSIS",
        "SUPERVISOR_REMEDIATION",
        "RETRY",
    ]
    details: Dict[str, Any]


class BenchmarkResponse(BaseModel):
    run_id: str
    status: Literal["success", "failed"]
    supervisor_routing: List[Dict[str, str]]
    trajectory: List[TrajectoryEvent]
    final_reply: str
    metrics: Dict[str, Any]


# ---------------------------------------------------------------------------
# LLM Factory  --  provider fully auto-detected from model_name
# ---------------------------------------------------------------------------

def build_llm(model_name: str, api_key: str):
    m = model_name.lower()
    if "gpt" in m:
        provider = "openai"
    elif "llama" in m:
        provider = "groq"
    elif "mistral" in m:
        provider = "mistral"
    elif "claude" in m:
        provider = "anthropic"
    elif "grok" in m:
        provider = "xai"
    elif "deepseek" in m:
        provider = "deepseek"
    else:
        provider = "openrouter"

    env_map = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai":     "OPENAI_API_KEY",
        "anthropic":  "ANTHROPIC_API_KEY",
        "xai":        "XAI_API_KEY",
        "mistral":    "MISTRAL_API_KEY",
        "deepseek":   "DEEPSEEK_API_KEY",
        "groq":       "GROQ_API_KEY",
    }
    os.environ[env_map[provider]] = api_key

    constructors = {
        "openrouter": ChatOpenRouter,
        "openai":     ChatOpenAI,
        "anthropic":  ChatAnthropic,
        "xai":        ChatXAI,
        "mistral":    ChatMistralAI,
        "deepseek":   ChatDeepSeek,
        "groq":       ChatGroq,
    }
    return constructors[provider](model=model_name, temperature=0)


# ---------------------------------------------------------------------------
# Supervisor structured-output schemas
# ---------------------------------------------------------------------------

class RoutingStep(PydanticBaseModel):
    agent_name: str = PydanticField(
        validation_alias=AliasChoices("agent_name", "agent"),
        description="Name of the agent to call at this step."
    )
    reason: str = PydanticField(
        validation_alias=AliasChoices("reason", "task", "action", "description"),
        description="Why this agent is the right choice for this step."
    )
    task_prompt: str = PydanticField(
        validation_alias=AliasChoices("task_prompt", "prompt", "instruction"),
        description=(
            "The exact task instruction the supervisor is sending to this agent. "
            "Should be specific, self-contained, and reference any expected inputs from prior agents."
        )
    )

    model_config = ConfigDict(populate_by_name=True)


class RoutingPlan(PydanticBaseModel):
    steps: List[RoutingStep] = PydanticField(
        description="Ordered list of agent calls to fulfil the user request."
    )


class FailureAnalysis(PydanticBaseModel):
    failed_agent: str = PydanticField(
        validation_alias=AliasChoices("failed_agent", "agent", "failing_agent"),
        description="Exact name of the agent that caused the failure (must match an agent in the fleet)."
    )
    root_cause: str = PydanticField(
        validation_alias=AliasChoices("root_cause", "cause", "error", "reason"),
        description="Concise explanation of why the agent failed based on the trajectory log."
    )
    remediation_persona: str = PydanticField(
        validation_alias=AliasChoices("remediation_persona", "new_persona", "fix"),
        description="A fully rewritten system-prompt / persona for the failing agent that should fix the problem."
    )
    remediation_task_prompt: str = PydanticField(
        validation_alias=AliasChoices("remediation_task_prompt", "new_task_prompt", "new_prompt"),
        description=(
            "A revised task instruction for the failing agent. "
            "Should address the root cause and provide clearer, more specific guidance."
        )
    )
    retry_agent: bool = PydanticField(
        validation_alias=AliasChoices("retry_agent", "retry"),
        description="true if the agent should be retried with the new persona and task prompt, false if unrecoverable."
    )

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# Universal JSON-mode structured output
# ---------------------------------------------------------------------------

def _schema_hint(model_cls) -> str:
    schema = model_cls.model_json_schema()
    props = schema.get("properties", {})
    lines = []
    for field_name, meta in props.items():
        desc = meta.get("description", "")
        ftype = meta.get("type", "string")
        lines.append(f'  "{field_name}": <{ftype}>  // {desc}')
    return "{\n" + ",\n".join(lines) + "\n}"


def _invoke_json(llm, prompt_template: ChatPromptTemplate, variables: Dict, model_cls):
    json_instruction = (
        "\n\nIMPORTANT: You MUST respond with a **SINGLE VALID JSON OBJECT** and nothing else. "
        "Do NOT include markdown fences (like ```json), backticks, or any explanatory text. "
        "The JSON keys MUST match the schema exactly.\n\n"
        "### REQUIRED SCHEMA:\n"
        + _schema_hint(model_cls)
    )

    messages = prompt_template.format_messages(**variables)
    patched = messages[:-1] + [
        HumanMessage(content=str(messages[-1].content) + json_instruction)
    ]

    response = llm.invoke(patched)
    raw = response.content if hasattr(response, "content") else str(response)
    raw = raw.strip()
    raw = _re.sub(r"^```(?:json)?\s*", "", raw)
    raw = _re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        data = _json.loads(raw)
        return model_cls(**data)
    except Exception:
        pass

    match = _re.search(r"\{.*\}", raw, _re.DOTALL)
    if match:
        try:
            data = _json.loads(match.group())
            return model_cls(**data)
        except Exception:
            pass

    raise ValueError(
        f"Could not parse LLM response as {model_cls.__name__}.\n"
        f"Raw response:\n{raw}"
    )


# ---------------------------------------------------------------------------
# Trajectory helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(agent: str, etype: str, details: Dict) -> Dict:
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": _now(),
        "agent": agent,
        "event_type": etype,
        "details": details,
    }


def _trajectory_summary(trajectory: List[Dict]) -> str:
    """Compact human-readable log for the supervisor to reason over."""
    lines = []
    for e in trajectory:
        detail_str = "; ".join(f"{k}={v}" for k, v in e["details"].items())
        lines.append(
            f"[{e['timestamp']}] {e['agent']} | {e['event_type']} | {detail_str}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class FleetState(TypedDict):
    run_id: str
    user_request: str
    agents: List[Dict]              # AgentDefinition dicts -- mutable for remediation
    routing_plan: List[Dict]        # [{"agent_name", "reason", "task_prompt"}, ...]
    current_agent_index: int
    agent_outputs: Dict[str, str]   # agent_name -> output text
    trajectory: List[Dict]
    retry_counts: Dict[str, int]
    failed_agent: Optional[str]
    final_output: str
    status: str


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_fleet_graph(
    llm,
    tavily_api_key: str,
    agent_defs: List[AgentDefinition],
    max_retries: int,
    induce_failure: bool,
    inject_failure: Optional[str],
):
    if tavily_api_key:
        os.environ["TAVILY_API_KEY"] = tavily_api_key
    search_tool = TavilySearch(max_results=3) if tavily_api_key else None

    # ------------------------------------------------------------------ #
    # Node: Supervisor plans the routing order and writes task prompts     #
    # ------------------------------------------------------------------ #

    def supervisor_plan_node(state: FleetState) -> Dict:
        agent_list = "\n".join(
            f"- {a['name']}: {a['persona'][:200]}" for a in state["agents"]
        )
        prompt = ChatPromptTemplate.from_template(
            "You are a Supervisor AI responsible for decomposing a user's request into a structured "
            "execution plan across a fleet of specialised sub-agents.\n\n"
            "## You are required to create these sub-agents based on the users's request. Each sub-agent is a dictionary with name and persona. You need to define only the required and most needed sub agents which can complete the task in less token and with high accuracy\n\n"
            "## Your Available Sub-Agents\n"
            "{agent_list}\n\n"
            "## User Request\n"
            "{user_request}\n\n"
            "## Your Task\n"
            "Create a step-by-step routing plan. For each step you must:\n"
            "1. Select the most appropriate agent from the list above.\n"
            "2. Write a clear, specific `task_prompt` — the exact instruction the agent will receive. "
            "   The task_prompt must be self-contained and include any context the agent needs "
            "   (e.g. 'Using the research findings passed to you, write a Python script that...').\n"
            "3. Explain in `reason` why this agent is the right choice for this step.\n\n"
            "## Rules\n"
            "- Order steps so earlier outputs can feed later steps.\n"
            "- Only include agents that are genuinely needed.\n"
            "- Each task_prompt should be actionable and specific — never vague.\n"
            "- Use the exact agent names as listed above."
        )

        # agent_list = "\n".join(
        #     f"- {a['name']}: {a['persona'][:200]}" for a in state["agents"]
        # )

        # prompt = ChatPromptTemplate.from_template(
        #     "You are a Supervisor AI that orchestrates a fleet of specialised sub-agents to complete user tasks.\n\n"
            
        #     "## Intelligence Efficiency Principle\n"
        #     "Every step you plan must produce FORWARD PROGRESS. Avoid redundant, overlapping, or vague steps "
        #     "that waste tokens without advancing the solution. A shorter plan that completes the task is always "
        #     "better than a longer one that repeats work.\n\n"
            
        #     "## Available Sub-Agents\n"
        #     "{agent_list}\n\n"
            
        #     "## User Request\n"
        #     "{user_request}\n\n"
            
        #     "## Planning Rules\n"
        #     "1. **Sequence for dependency** — earlier steps must produce outputs that later steps can consume. "
        #     "   Make data flow explicit in each task_prompt (e.g. 'Using the schema produced in Step 1...').\n"
        #     "2. **One agent, one responsibility** — each step should do exactly one thing. "
        #     "   Split only when work genuinely requires a different agent's expertise.\n"
        #     "3. **Self-contained task prompts** — every task_prompt must include: "
        #     "   (a) what to do, (b) what inputs are available, (c) what the expected output is. "
        #     "   The agent receives nothing except what you write here.\n"
        #     "4. **No redundancy** — never assign the same conceptual work to two agents. "
        #     "   If an agent already produced a result, the next agent must BUILD on it, not repeat it.\n"
        #     "5. **Justify every agent** — in `reason`, explain specifically why this agent (not another) "
        #     "   is the right choice. If you cannot justify it clearly, remove the step.\n"
        #     "6. **Use exact agent names** as listed above — no paraphrasing or inventing new names.\n\n"
            
        #     "## Output\n"
        #     "Return a step-by-step routing plan. Each step: agent_name, task_prompt, reason."
        # )

        plan: RoutingPlan = _invoke_json(
            llm, prompt,
            {"agent_list": agent_list, "user_request": state["user_request"]},
            RoutingPlan,
        )
        routing_plan = [
            {
                "agent_name": s.agent_name,
                "reason": s.reason,
                "task_prompt": s.task_prompt,
            }
            for s in plan.steps
        ]

        traj = list(state["trajectory"])
        traj.append(_event("Supervisor", "ENTER", {
            "action": "planning",
            "plan": str(routing_plan),
        }))
        return {
            "routing_plan": routing_plan,
            "current_agent_index": 0,
            "trajectory": traj,
        }

    # ------------------------------------------------------------------ #
    # Node factory: one execution node per agent                          #
    # ------------------------------------------------------------------ #

    def make_agent_node(static_def: Dict):
        """
        Returns a LangGraph node function for the agent identified by
        `static_def["name"]`. At runtime the node re-reads the persona
        from `state["agents"]` so that supervisor remediations take effect.
        Sub-agents return a structured result (output + task_status) back
        to the supervisor via the trajectory log.
        """

        def agent_node(state: FleetState) -> Dict:
            name = static_def["name"]

            # Always use the *current* persona (may have been rewritten by supervisor)
            current_def = next(
                (a for a in state["agents"] if a["name"] == name),
                static_def,
            )
            persona = current_def["persona"]
            use_search = current_def.get("use_search", False)

            # Retrieve the supervisor-assigned task_prompt for this step
            idx = state["current_agent_index"]
            plan = state["routing_plan"]
            task_prompt = (
                plan[idx]["task_prompt"]
                if idx < len(plan) and plan[idx].get("task_prompt")
                else state["user_request"]
            )

            traj = list(state["trajectory"])
            traj.append(_event(name, "ENTER", {
                "persona_snippet": persona[:120],
                "task_prompt_snippet": task_prompt[:200],
            }))

            # Inject failure before LLM call (retry_counts == 0 means first attempt)
            if induce_failure and name == inject_failure and state["retry_counts"].get(name, 0) == 0:
                err_msg = (
                    f"RuntimeError: Agent '{name}' encountered an unexpected internal error during execution. "
                    "Please verify the persona/instructions and try again."
                )
                traj.append(_event(name, "EXIT_FAILURE", {
                    "error": err_msg,
                    "task_status": "failed",
                    "traceback": "",
                }))
                return {
                    "trajectory": traj,
                    "failed_agent": name,
                    "status": "running",
                }

            # Build context from prior agent outputs
            prior_context = "\n\n".join(
                f"[{k} output]:\n{v}" for k, v in state["agent_outputs"].items()
            )

            try:
                system_message = (
                    f"{persona}\n\n"
                    "## Response Format\n"
                    "After completing your task, you MUST end your response with a status line in this exact format:\n"
                    "TASK_STATUS: complete\n"
                    "OR if you were unable to complete the task:\n"
                    "TASK_STATUS: incomplete — <brief reason>\n\n"
                    "Be explicit. The supervisor depends on your status to decide next steps.\n\n"
                    "## Tool Usage\n"
                    "If you use any tools, provide all arguments in valid JSON format. "
                    "Use 'true'/'false' for booleans, never 'True'/'False'."
                )

                # Compose the full user-facing prompt for this agent
                if prior_context:
                    full_prompt = (
                        f"## Your Task (assigned by Supervisor)\n{task_prompt}\n\n"
                        f"## Context from Prior Agents\n{prior_context}"
                    )
                else:
                    full_prompt = f"## Your Task (assigned by Supervisor)\n{task_prompt}"

                if use_search and search_tool:
                    agent_executor = create_react_agent(llm, tools=[search_tool])
                    agent_res = agent_executor.invoke({
                        "messages": [
                            SystemMessage(content=system_message),
                            HumanMessage(content=full_prompt)
                        ]
                    })
                    output = agent_res["messages"][-1].content
                else:
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_message),
                        ("human", "{request}"),
                    ])
                    result = (prompt | llm).invoke({"request": full_prompt})
                    output = result.content if hasattr(result, "content") else str(result)

                # Parse task_status from agent's output
                task_status = "complete"
                status_match = _re.search(r"TASK_STATUS:\s*(\S+.*)", str(output), _re.IGNORECASE)
                if status_match:
                    raw_status = status_match.group(1).strip().lower()
                    task_status = "incomplete" if raw_status.startswith("incomplete") else "complete"

                traj.append(_event(name, "EXIT_SUCCESS", {
                    "output_snippet": str(output)[:300],
                    "task_status": task_status,
                }))
                return {
                    "agent_outputs": {**state["agent_outputs"], name: str(output)},
                    "trajectory": traj,
                    "current_agent_index": state["current_agent_index"] + 1,
                    "failed_agent": None,
                }

            except Exception as exc:
                traj.append(_event(name, "EXIT_FAILURE", {
                    "error": str(exc),
                    "task_status": "failed",
                    "traceback": traceback.format_exc()[:500],
                }))
                return {
                    "trajectory": traj,
                    "failed_agent": name,
                    "status": "running",
                }

        return agent_node

    # ------------------------------------------------------------------ #
    # Node: Supervisor analyses failure and remediates                     #
    # ------------------------------------------------------------------ #

    def supervisor_remediate_node(state: FleetState) -> Dict:
        traj = list(state["trajectory"])
        traj_text = _trajectory_summary(traj)
        agent_list = "\n".join(
            f"- {a['name']}: {a['persona'][:120]}" for a in state["agents"]
        )

        prompt = ChatPromptTemplate.from_template(
            "You are a Supervisor AI. One of your sub-agents has failed or returned an incomplete result. "
            "Your job is to analyse the execution logs, understand what went wrong, and produce a remediation plan.\n\n"
            "## Full Trajectory Log (chronological, newest at bottom)\n"
            "{trajectory}\n\n"
            "## Current Agent Fleet\n"
            "{agent_list}\n\n"
            "## Original User Request\n"
            "{user_request}\n\n"
            "## Your Analysis Steps\n"
            "1. **Identify the failing agent** — look for EXIT_FAILURE events or TASK_STATUS: incomplete in the log.\n"
            "2. **Diagnose the root cause** — was it a bad persona, an unclear task prompt, a capability mismatch, "
            "   a tool error, or a rate limit?\n"
            "3. **Write a remediation_persona** — a fully revised system-prompt that corrects the identified weakness. "
            "   Be specific about what the agent should and should not do.\n"
            "4. **Write a remediation_task_prompt** — a clearer, more specific task instruction that directly addresses "
            "   the failure. Reference any available context from other agents' outputs if relevant.\n"
            "5. **Decide retry_agent** — set to true unless the failure is a hard rate limit or completely unrecoverable. "
            "   For rate limit errors, set to false.\n\n"
            "## Important\n"
            "- The `failed_agent` name must exactly match one of the agent names listed above.\n"
            "- Do not change the strategy — only fix the failing agent so it can complete its assigned role."
        )

        try:
            analysis: FailureAnalysis = _invoke_json(
                llm, prompt,
                {
                    "trajectory": traj_text,
                    "agent_list": agent_list,
                    "user_request": state["user_request"],
                },
                FailureAnalysis,
            )
        except ValueError as parse_err:
            traj.append(_event("Supervisor", "EXIT_FAILURE", {
                "error": f"Supervisor could not produce a valid FailureAnalysis: {parse_err}",
            }))
            return {"trajectory": traj, "status": "failed", "final_output": ""}

        traj.append(_event("Supervisor", "SUPERVISOR_ANALYSIS", {
            "failed_agent_identified": analysis.failed_agent,
            "root_cause": analysis.root_cause,
            "retry": str(analysis.retry_agent),
        }))

        # Rewrite the failing agent's persona AND update the task_prompt in routing_plan
        updated_agents = []
        for a in state["agents"]:
            if a["name"] == analysis.failed_agent:
                updated_agents.append({**a, "persona": analysis.remediation_persona})
                traj.append(_event("Supervisor", "SUPERVISOR_REMEDIATION", {
                    "agent": analysis.failed_agent,
                    "new_persona_snippet": analysis.remediation_persona[:150],
                    "new_task_prompt_snippet": analysis.remediation_task_prompt[:150],
                }))
            else:
                updated_agents.append(a)

        # Patch the task_prompt in the routing plan for the failing agent's next step
        updated_routing_plan = []
        for step in state["routing_plan"]:
            if step["agent_name"] == analysis.failed_agent:
                updated_routing_plan.append({
                    **step,
                    "task_prompt": analysis.remediation_task_prompt,
                })
            else:
                updated_routing_plan.append(step)

        new_retry_counts = {**state["retry_counts"]}
        agent_key = analysis.failed_agent
        new_retry_counts[agent_key] = new_retry_counts.get(agent_key, 0) + 1

        traj.append(_event("Supervisor", "RETRY", {
            "agent": agent_key,
            "retry_number": new_retry_counts[agent_key],
            "max_retries": max_retries,
        }))

        return {
            "agents": updated_agents,
            "routing_plan": updated_routing_plan,
            "trajectory": traj,
            "retry_counts": new_retry_counts,
            "failed_agent": agent_key if analysis.retry_agent else None,
            "status": "running" if analysis.retry_agent else "failed",
        }

    # ------------------------------------------------------------------ #
    # Node: Supervisor aggregates all agent outputs into a final reply     #
    # ------------------------------------------------------------------ #

    def aggregator_node(state: FleetState) -> Dict:
        outputs = state["agent_outputs"]

        # Format individual agent outputs
        agents_section = "\n\n".join(
            f"### Output from {k}\n{v}" for k, v in outputs.items()
        )

        # Ask the supervisor to synthesise a coherent final answer
        synthesis_prompt = ChatPromptTemplate.from_template(
            "You are a Supervisor AI. Your sub-agents have all completed their tasks. "
            "Your job is to synthesise their outputs into a single, coherent, well-structured final response "
            "that fully addresses the original user request.\n\n"
            "## Original User Request\n"
            "{user_request}\n\n"
            "## Sub-Agent Outputs\n"
            "{agents_section}\n\n"
            "## Instructions\n"
            "- Combine the outputs logically — do not just concatenate them.\n"
            "- Remove redundancy and resolve any contradictions.\n"
            "- Present the result in the most useful format for the user (prose, code blocks, bullet points, etc.).\n"
            "- Do not mention the internal agent names or the orchestration process unless directly relevant.\n"
            "- Your response IS the final answer delivered to the user."
        )

        try:
            messages = synthesis_prompt.format_messages(
                user_request=state["user_request"],
                agents_section=agents_section,
            )
            response = llm.invoke(messages)
            final_output = response.content if hasattr(response, "content") else str(response)
        except Exception:
            # Fallback: plain concatenation if synthesis fails
            final_output = agents_section

        traj = list(state["trajectory"])
        traj.append(_event("Supervisor", "EXIT_SUCCESS", {
            "action": "synthesis_complete",
            "agents_completed": str(list(outputs.keys())),
        }))
        return {"final_output": final_output, "status": "success", "trajectory": traj}

    # ------------------------------------------------------------------ #
    # Node: Terminal failure (max retries exhausted)                       #
    # ------------------------------------------------------------------ #

    def mark_failed_node(state: FleetState) -> Dict:
        traj = list(state["trajectory"])
        failed = state.get("failed_agent", "unknown")
        partial_outputs = state.get("agent_outputs", {})

        traj.append(_event("Supervisor", "EXIT_FAILURE", {
            "reason": f"Max retries ({max_retries}) exhausted for agent '{failed}'.",
            "agents_completed_before_failure": str(list(partial_outputs.keys())),
        }))

        # Provide a partial result if some agents did succeed
        partial_summary = ""
        if partial_outputs: 
            partial_summary = (
                f"The following agents completed successfully before the failure:\n\n"
                + "\n\n".join(f"### {k}\n{v}" for k, v in partial_outputs.items())
            )

        return {
            "status": "failed",
            "final_output": partial_summary,
            "trajectory": traj,
        }

    # ------------------------------------------------------------------ #
    # Routing functions                                                    #
    # ------------------------------------------------------------------ #

    valid_agent_names = {a.name for a in agent_defs}

    def route_after_agent(state: FleetState) -> str:
        if state.get("failed_agent"):
            failed = state["failed_agent"]
            retries = state["retry_counts"].get(failed, 0)
            if retries < max_retries:
                return "supervisor_remediate"
            return "mark_failed"
        idx = state["current_agent_index"]
        if idx >= len(state["routing_plan"]):
            return "aggregator"
        return "dispatch_next"

    def dispatch_next_fn(state: FleetState) -> str:
        idx = state["current_agent_index"]
        plan = state["routing_plan"]
        if idx >= len(plan):
            return "aggregator"
        target = plan[idx]["agent_name"]
        if target not in valid_agent_names:
            return "aggregator"
        return target

    def route_after_remediation(state: FleetState) -> str:
        if state.get("status") == "failed":
            return "mark_failed"
        target = state.get("failed_agent")
        if target and target in valid_agent_names:
            return target
        return dispatch_next_fn(state)

    # ------------------------------------------------------------------ #
    # Build the graph                                                      #
    # ------------------------------------------------------------------ #

    workflow = StateGraph(FleetState)

    workflow.add_node("supervisor_plan", supervisor_plan_node)
    workflow.add_node("supervisor_remediate", supervisor_remediate_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("mark_failed", mark_failed_node)
    workflow.add_node("dispatch_next", lambda state: {})

    for agent_def in agent_defs:
        workflow.add_node(agent_def.name, make_agent_node(agent_def.dict()))

    workflow.set_entry_point("supervisor_plan")
    workflow.add_edge("supervisor_plan", "dispatch_next")

    dispatch_targets: Dict[str, str] = {a.name: a.name for a in agent_defs}
    dispatch_targets["aggregator"] = "aggregator"
    workflow.add_conditional_edges("dispatch_next", dispatch_next_fn, dispatch_targets)

    after_agent_targets = {
        "supervisor_remediate": "supervisor_remediate",
        "mark_failed": "mark_failed",
        "aggregator": "aggregator",
        "dispatch_next": "dispatch_next",
    }
    for agent_def in agent_defs:
        workflow.add_conditional_edges(agent_def.name, route_after_agent, after_agent_targets)

    remediation_targets: Dict[str, str] = {a.name: a.name for a in agent_defs}
    remediation_targets["mark_failed"] = "mark_failed"
    remediation_targets["aggregator"] = "aggregator"
    remediation_targets["dispatch_next"] = "dispatch_next"
    workflow.add_conditional_edges(
        "supervisor_remediate",
        route_after_remediation,
        remediation_targets,
    )

    workflow.add_edge("aggregator", END)
    workflow.add_edge("mark_failed", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Supervisor-Fleet Benchmark API running. Visit /docs for Swagger UI.",
    }


@app.post("/run-benchmark", response_model=BenchmarkResponse, tags=["Benchmark"])
def run_benchmark(req: BenchmarkRequest):
    """
    Execute the supervisor-fleet benchmark.

    The supervisor will:
    1. **Plan** — read the user request, assign each agent a specific task prompt and persona.
    2. **Execute** — dispatch agents in order; each agent returns output + TASK_STATUS.
    3. **Detect** — on EXIT_FAILURE or incomplete status, read trajectory and identify the root cause.
    4. **Remediate** — rewrite the failing agent's persona AND task prompt, then retry (up to `max_retries`).
    5. **Synthesise** — supervisor combines all agent outputs into a single coherent final answer.
    6. **Report** — return the full trajectory, metrics, and final answer.
    """
    run_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        llm = build_llm(req.model_name, req.model_api_key)
        agent_defs = list(req.agents)

        graph = build_fleet_graph(
            llm=llm,
            tavily_api_key=req.TAVILY_API_KEY,
            agent_defs=agent_defs,
            max_retries=req.max_retries,
            induce_failure=req.induce_failure,
            inject_failure=req.inject_failure,
        )

        initial_state: FleetState = {
            "run_id": run_id,
            "user_request": req.user_request,
            "agents": [a.dict() for a in agent_defs],
            "routing_plan": [],
            "current_agent_index": 0,
            "agent_outputs": {},
            "trajectory": [],
            "retry_counts": {},
            "failed_agent": None,
            "final_output": "",
            "status": "running",
        }

        result = graph.invoke(initial_state)
        elapsed = round(time.time() - start_time, 2)

        traj: List[Dict] = result.get("trajectory", [])
        failure_events  = [e for e in traj if e["event_type"] == "EXIT_FAILURE"]
        analysis_events = [e for e in traj if e["event_type"] == "SUPERVISOR_ANALYSIS"]
        retry_events    = [e for e in traj if e["event_type"] == "RETRY"]

        failure_correctly_attributed: Optional[bool] = None
        if req.induce_failure and req.inject_failure and analysis_events:
            identified = analysis_events[0]["details"].get("failed_agent_identified", "")
            failure_correctly_attributed = (identified == req.inject_failure)

        # Calculate intelligence per cost metrics
        intelligence_metrics = calculate_intelligence_per_cost(
            trajectory=traj,
            user_request=req.user_request,
            model_name=req.model_name,
        )

        metrics: Dict[str, Any] = {
            "run_id": run_id,
            "elapsed_seconds": elapsed,
            "total_trajectory_events": len(traj),
            "agent_failures_detected": len(failure_events),
            "supervisor_analyses": len(analysis_events),
            "total_retries": len(retry_events),
            "retry_counts_per_agent": result.get("retry_counts", {}),
            "failure_correctly_attributed": failure_correctly_attributed,
            "agents_completed": list(result.get("agent_outputs", {}).keys()),
            "status": result.get("status", "unknown"),
            "intelligence_metrics": intelligence_metrics,
        }

        return BenchmarkResponse(
            run_id=run_id,
            status=result.get("status", "failed"),
            supervisor_routing=result.get("routing_plan", []),
            trajectory=[TrajectoryEvent(**e) for e in traj],
            final_reply=result.get("final_output", ""),
            metrics=metrics,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=traceback.format_exc()) from exc