from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

OPENAI_CHAT_MODEL_ENV = "OPENAI_CHAT_MODEL"
OPENAI_CHAT_MODEL = "gpt-4.1-mini"

# SAMPLE_FILES = [
#     "data/python_intro.txt",
#     "data/vector_store_notes.md",
#     "data/rag_system_design.md",
#     "data/customer_support_playbook.txt",
#     "data/chunking_experiment_report.md",
#     "data/vi_retrieval_notes.md",
# ]

SAMPLE_FILES = [
    "data/1.md", 
    "data/2.md", 
    "data/3.md", 
    "data/4.md", 
    "data/5.md", 
    "data/6.md", 
    "data/7.md", 
    "data/8.md", 
    "data/9.md", 
    "data/10.md", 
    
]

def extract_document_title(content: str, fallback: str) -> str:
    """Use the first markdown H1 as the document title when available."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_documents_from_files(file_paths: list[str]) -> list[Document]:
    """Load documents from file paths for the manual demo."""
    allowed_extensions = {".md", ".txt"}
    documents: list[Document] = []

    for raw_path in file_paths:
        path = Path(raw_path)

        if path.suffix.lower() not in allowed_extensions:
            print(f"Skipping unsupported file type: {path} (allowed: .md, .txt)")
            continue

        if not path.exists() or not path.is_file():
            print(f"Skipping missing file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        title = extract_document_title(content, path.stem)
        documents.append(
            Document(
                id=path.stem,
                content=content,
                metadata={
                    "source": str(path),
                    "extension": path.suffix.lower(),
                    "doc_title": title,
                },
            )
        )

    return documents


def chunk_documents(docs: list[Document], max_sentences_per_chunk: int = 3) -> list[Document]:
    """Split each loaded document into sentence-based chunks for retrieval."""
    chunker = SentenceChunker(max_sentences_per_chunk=max_sentences_per_chunk)
    chunked_documents: list[Document] = []

    for doc in docs:
        chunks = chunker.chunk(doc.content)
        total_chunks = len(chunks)
        for index, chunk in enumerate(chunks):
            chunked_documents.append(
                Document(
                    id=f"{doc.id}_chunk_{index}",
                    content=chunk,
                    metadata={
                        **doc.metadata,
                        "doc_id": doc.id,
                        "chunk_index": index,
                        "total_chunks": total_chunks,
                        "chunk_char_count": len(chunk),
                    },
                )
            )

    return chunked_documents


def demo_llm(prompt: str) -> str:
    """A simple mock LLM for manual RAG testing."""
    preview = prompt[:400].replace("\n", " ")
    return f"[DEMO LLM] Generated answer from prompt preview: {preview}..."


def make_openai_llm(model_name: str = OPENAI_CHAT_MODEL):
    """Create a real LLM callable backed by the OpenAI Responses API."""
    from openai import OpenAI

    client = OpenAI()

    def _llm(prompt: str) -> str:
        response = client.responses.create(model=model_name, input=prompt)
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()

        parts: list[str] = []
        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []):
                text = getattr(content, "text", None)
                if text:
                    parts.append(text.strip())
        return "\n".join(part for part in parts if part).strip() or "No answer generated."

    return _llm


def run_manual_demo(question: str | None = None, sample_files: list[str] | None = None) -> int:
    files = sample_files or SAMPLE_FILES
    query = question or "Summarize the key information from the loaded files."

    print("=== Manual File Test ===")
    print("Accepted file types: .md, .txt")
    print("Input file list:")
    for file_path in files:
        print(f"  - {file_path}")

    docs = load_documents_from_files(files)
    if not docs:
        print("\nNo valid input files were loaded.")
        print("Create files matching the sample paths above, then rerun:")
        print("  python3 main.py")
        return 1

    print(f"\nLoaded {len(docs)} documents")
    for doc in docs:
        print(f"  - {doc.id}: {doc.metadata['source']}")

    chunked_docs = chunk_documents(docs)
    print(f"Created {len(chunked_docs)} chunks with SentenceChunker")

    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            embedder = LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    elif provider == "openai":
        try:
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    print(f"\nEmbedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

    llm_fn = demo_llm
    llm_backend_name = "demo_llm"
    if provider == "openai":
        try:
            llm_model_name = os.getenv(OPENAI_CHAT_MODEL_ENV, OPENAI_CHAT_MODEL).strip() or OPENAI_CHAT_MODEL
            llm_fn = make_openai_llm(model_name=llm_model_name)
            llm_backend_name = llm_model_name
        except Exception:
            llm_fn = demo_llm
            llm_backend_name = "demo_llm (fallback)"

    print(f"LLM backend: {llm_backend_name}")

    store = EmbeddingStore(collection_name="manual_test_store", embedding_fn=embedder)
    store.add_documents(chunked_docs)

    print(f"\nStored {store.get_collection_size()} documents in EmbeddingStore")
    print("\n=== EmbeddingStore Search Test ===")
    print(f"Query: {query}")
    search_results = store.search(query, top_k=10)
    for index, result in enumerate(search_results, start=1):
        print(f"{index}. score={result['score']:.3f} source={result['metadata'].get('source')}")
        print(f"   content preview: {result['content'][:120].replace(chr(10), ' ')}...")

    print("\n=== KnowledgeBaseAgent Test ===")
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)
    print(f"Question: {query}")
    print("Agent answer:")
    print(agent.answer(query, top_k=1))
    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else None
    return run_manual_demo(question=question)


if __name__ == "__main__":
    raise SystemExit(main())
