"""Скрипт 4: Построение векторного индекса ChromaDB"""

import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

KB_DIR = Path(__file__).parent.parent / 'knowledge_base'
VECTOR_DB_DIR = Path(__file__).parent.parent / 'vector_db' / 'chroma_db'

EMBEDDING_MODEL = "Alibaba-NLP/gte-multilingual-base"
COLLECTION_NAME = "zanvoria_chronicles"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 200


def load_documents():
    documents = []

    for category in ['character', 'location', 'event', 'system']:
        category_path = KB_DIR / category
        if not category_path.exists():
            continue

        for md_file in category_path.glob('*.md'):
            content = md_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip()
            category_line = [l for l in lines if l.startswith('**Category:**')]
            doc_category = category_line[0].split(':')[1].strip() if category_line else category

            doc = Document(
                page_content=content,
                metadata={
                    "source": str(md_file.relative_to(KB_DIR.parent)),
                    "category": doc_category,
                    "title": title,
                    "filename": md_file.name
                }
            )
            documents.append(doc)

    return documents


def chunk_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
    )

    chunks = text_splitter.split_documents(documents)
    filtered_chunks = [c for c in chunks if len(c.page_content.strip()) >= MIN_CHUNK_SIZE]

    for i, chunk in enumerate(filtered_chunks):
        chunk.metadata['chunk_id'] = i

    print(f"    Original: {len(chunks)}, Filtered: {len(filtered_chunks)}")
    return filtered_chunks


def build_index(chunks, embeddings):
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DB_DIR)
    )
    return vectorstore


def main():
    print("=" * 70)
    print("  VECTOR INDEX GENERATION")
    print("=" * 70)
    start_time = time.time()

    print("\n[1/4] Loading documents...")
    documents = load_documents()
    print(f"[OK] Loaded {len(documents)} documents")

    print("\n[2/4] Loading embedding model...")
    print(f"      Model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu', 'trust_remote_code': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("[OK] Model loaded")

    print("\n[3/4] Chunking documents...")
    chunks = chunk_documents(documents)
    print(f"[OK] Created {len(chunks)} chunks")

    print("\n[4/4] Building index...")
    build_index(chunks, embeddings)
    print(f"[OK] Index saved to {VECTOR_DB_DIR}")

    elapsed = time.time() - start_time

    stats = {
        "total_documents": len(documents),
        "total_chunks": len(chunks),
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "generation_time_seconds": round(elapsed, 2)
    }

    stats_path = VECTOR_DB_DIR.parent / 'index_stats.json'
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    print(f"\n[SUCCESS] Built in {elapsed:.2f}s | {len(documents)} docs | {len(chunks)} chunks")


if __name__ == '__main__':
    main()
