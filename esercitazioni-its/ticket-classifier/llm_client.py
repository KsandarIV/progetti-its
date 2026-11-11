import os
import ollama

MODEL = os.getenv("LLM_MODEL", "gemma4-coder:latest")

def call_llm(system: str, messages: list[dict], max_tokens: int = 1500) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": system}] + messages,
        format="json",
        think=False,  # evita che i token di ragionamento consumino num_predict
        options={"num_predict": max_tokens, "temperature": 0},
    )
    return response.message.content