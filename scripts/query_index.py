"""Интерактивный поиск по векторному индексу"""

from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

VECTOR_DB_DIR = Path(__file__).parent.parent / 'vector_db' / 'chroma_db'
EMBEDDING_MODEL = "Alibaba-NLP/gte-multilingual-base"


def load_index():
    print("[*] Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'trust_remote_code': True}
    )

    print("[*] Connecting to ChromaDB...")
    vectorstore = Chroma(
        collection_name="zanvoria_chronicles",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DB_DIR)
    )

    return vectorstore


def print_results(results, query):
    print("\n" + "=" * 80)
    print(f"Query: {query}")
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    for i, (doc, score) in enumerate(results, 1):
        print(f"\n[{i}] Distance: {score:.4f}")
        print(f"    Source: {doc.metadata.get('source', 'N/A')}")
        print(f"    Title: {doc.metadata.get('title', 'N/A')}")
        print("-" * 80)

        content = doc.page_content.replace('\n', ' ').strip()
        if len(content) > 500:
            content = content[:500] + "..."
        content = content.encode('ascii', 'replace').decode('ascii')
        print(f"    {content}")

    print("\n" + "=" * 80)


def main():
    print("=" * 80)
    print("  ZANVORIA CHRONICLES - Interactive Search")
    print("=" * 80)

    vectorstore = load_index()
    print("[OK] Ready!\n")
    print("Commands: k=N (results), q (quit)\n")

    k = 3

    while True:
        try:
            query = input(f"[k={k}] > ").strip()

            if not query:
                continue

            if query.lower() in ('q', 'exit', 'quit'):
                print("Goodbye!")
                break

            if query.lower().startswith('k='):
                try:
                    k = int(query.split('=')[1])
                    print(f"[OK] k={k}")
                except ValueError:
                    print("[!] Use k=N format")
                continue

            results = vectorstore.similarity_search_with_score(query, k=k)
            print_results(results, query)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == '__main__':
    main()
