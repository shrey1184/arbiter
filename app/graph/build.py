"""LangGraph pipeline.

parse_input -> fan-out (Send) -> 3 critics -> collect -> detect_disagreements
   -> all_clean? -> short_circuit_pass | adjudicate -> synthesize_verdict -> persist
"""
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.critics.runner import run_critic
from app.graph.disagreements import detect_disagreements
from app.graph.state import ArbState
from app.schemas import Critique, Verdict

DIMENSIONS = ["accuracy", "logic", "completeness"]


def parse_input(state: ArbState) -> dict:
    # TODO: validate, truncate long text, log non-English
    return {}


def dispatch(state: ArbState):
    return [Send(f"{d}_critic", state) for d in DIMENSIONS]


def make_critic_node(dim: str):
    async def node(state: ArbState) -> dict:
        res = await run_critic(dim, state["output_text"], state.get("original_prompt"))
        return {"critiques": [res]} if isinstance(res, Critique) else {"failures": [res]}
    return node


def detect(state: ArbState) -> dict:
    return {"disagreements": detect_disagreements(state.get("critiques", []), state["output_text"])}


def route_after_detect(state: ArbState) -> str:
    crit = state.get("critiques", [])
    clean = crit and not state.get("failures") and all(
        c.score == 5 and not c.issues and c.confidence >= 0.8 for c in crit)
    return "short_circuit" if clean else "adjudicate"


def short_circuit(state: ArbState) -> dict:
    return {"verdict": Verdict(summary="All critics found no issues.", overall_score=10, confidence=0.9)}


async def adjudicate(state: ArbState) -> dict:
    # TODO: call app.adjudicator; type-specific resolution strategies
    return {"verdict": Verdict(summary="TODO: adjudicator not implemented", overall_score=5, confidence=0.1,
                               degraded=bool(state.get("failures")))}


def build_graph():
    g = StateGraph(ArbState)
    g.add_node("parse_input", parse_input)
    for d in DIMENSIONS:
        g.add_node(f"{d}_critic", make_critic_node(d))
    g.add_node("detect", detect)
    g.add_node("short_circuit", short_circuit)
    g.add_node("adjudicate", adjudicate)
    g.add_edge(START, "parse_input")
    g.add_conditional_edges("parse_input", dispatch, [f"{d}_critic" for d in DIMENSIONS])
    for d in DIMENSIONS:
        g.add_edge(f"{d}_critic", "detect")      # fan-in
    g.add_conditional_edges("detect", route_after_detect, ["short_circuit", "adjudicate"])
    g.add_edge("short_circuit", END)
    g.add_edge("adjudicate", END)
    return g.compile()
