from app.critics.prompts import build_messages
from app.llm.client import call_structured
from app.schemas import Critique, CriticFailure, Dimension
from app.settings import config


async def run_critic(dimension: Dimension, output: str, prompt: str | None) -> Critique | CriticFailure:
    """Never raises: failures become CriticFailure so the graph can degrade gracefully.
    TODO: tenacity retries, substring validation, latency capture."""
    cfg = config()["critics"][dimension]
    try:
        return await call_structured(
            provider=cfg["provider"], model=cfg["model"], temperature=cfg["temperature"],
            messages=build_messages(dimension, output, prompt),
            response_model=Critique, validation_context={"source": output},
        )
    except Exception as exc:  # noqa: BLE001
        return CriticFailure(dimension=dimension, error=str(exc), attempts=1)
