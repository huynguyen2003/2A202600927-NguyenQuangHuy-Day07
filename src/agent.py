from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 1) -> str:
        retrieved_chunks = self.store.search(question, top_k=max(1, top_k))
        best_chunk = retrieved_chunks[0] if retrieved_chunks else None

        if best_chunk is None:
            context = "No relevant context found."
        else:
            source = best_chunk.get("metadata", {}).get("source", "unknown")
            context = (
                f"[Top 1 Chunk | source={source} | score={best_chunk['score']:.3f}]\n"
                f"{best_chunk['content']}"
            )

        prompt = (
            "You are a retrieval-augmented assistant.\n"
            "Answer in Vietnamese.\n"
            "Use only the top retrieved chunk below as context.\n"
            "If the top chunk does not contain enough information, say that the answer cannot be confirmed.\n"
            "Keep the answer concise and grounded in the provided context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
