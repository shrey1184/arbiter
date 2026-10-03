import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException

from app.graph.build import build_graph
from app.schemas import ArbitrateRequest, ArbitrateResponse
from app.settings import env
from app.storage.db import init_db

app = FastAPI(title="Arbiter", version="0.1.0", description="LLM Output Arbitration System")
graph = build_graph()


@app.on_event("startup")
def _startup() -> None:
    init_db()


def auth(x_api_key: str = Header(default="")) -> None:
    if x_api_key != env().arbiter_api_key:
        raise HTTPException(401, "invalid API key")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/arbitrate", response_model=ArbitrateResponse, dependencies=[Depends(auth)])
async def arbitrate(req: ArbitrateRequest) -> ArbitrateResponse:
    t0 = time.perf_counter()
    aid = str(uuid.uuid4())
    state = await graph.ainvoke({"arbitration_id": aid, "output_text": req.output,
                                 "original_prompt": req.prompt, "critiques": [], "failures": []})
    if not state.get("critiques"):
        raise HTTPException(503, "all critics failed")
    # TODO: persist to SQLite
    return ArbitrateResponse(arbitration_id=aid, verdict=state["verdict"], critiques=state["critiques"],
                             disagreements=state.get("disagreements", []),
                             latency_ms=int((time.perf_counter() - t0) * 1000))


# TODO: POST /v1/arbitrate/batch, GET /v1/batches/{id}, GET /v1/arbitrations/{id}, GET /v1/analytics/summary
