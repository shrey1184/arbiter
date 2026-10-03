"""One interface for all providers. All outputs are validated via instructor."""
from typing import TypeVar

import instructor
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.settings import env

T = TypeVar("T", bound=BaseModel)


def _client(provider: str):
    e = env()
    if provider == "openai":
        return instructor.from_openai(AsyncOpenAI(api_key=e.openai_api_key))
    if provider == "anthropic":
        return instructor.from_anthropic(AsyncAnthropic(api_key=e.anthropic_api_key))
    if provider == "ollama":
        return instructor.from_openai(
            AsyncOpenAI(base_url=e.ollama_base_url, api_key="ollama"),
            mode=instructor.Mode.JSON,
        )
    raise ValueError(f"unknown provider: {provider}")


async def call_structured(
    *, provider: str, model: str, messages: list[dict], response_model: type[T],
    temperature: float = 0.1, max_retries: int = 2, validation_context: dict | None = None,
) -> T:
    """TODO: add token/latency logging; pass validation_context={'source': text}
    so a Pydantic validator can reject quotes that are not real substrings."""
    client = _client(provider)
    kwargs = dict(model=model, messages=messages, response_model=response_model,
                  temperature=temperature, max_retries=max_retries,
                  validation_context=validation_context)
    if provider == "anthropic":
        kwargs["max_tokens"] = 2000
    return await client.chat.completions.create(**kwargs)
