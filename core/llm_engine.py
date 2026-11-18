import ollama

MODEL_NAME = "qwen2.5:1.5b"


def ask_ai(question: str, dataset_context: str) -> str:
    """Ask the local Qwen model a question with compact dataset context."""
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are InsightPilot AI, a data analytics assistant. "
                    "Use only the supplied dataset context. Do not invent exact "
                    "calculations or claim to have inspected unavailable records. "
                    "If the context is insufficient, say so clearly."
                ),
            },
            {
                "role": "user",
                "content": f"DATASET CONTEXT:\n{dataset_context}\n\nQUESTION:\n{question}",
            },
        ],
        options={"temperature": 0.2, "num_predict": 150},
        keep_alive=0,
    )
    return response.message.content
