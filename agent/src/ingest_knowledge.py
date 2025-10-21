#!/usr/bin/env python3
"""
Knowledge Base Ingestion System

Loads all Resonance Math documentation into vector database.
Creates persistent memory that survives conversation resets.
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

class KnowledgeIngestion:
    """Ingests Resonance Math knowledge into vector database"""

    def __init__(self, knowledge_base_path: str, chroma_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.chroma_path = Path(chroma_path)

        # Use free HuggingFace embeddings (no API key needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Text splitter - chunk docs for better retrieval
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def load_knowledge_sources(self) -> List[str]:
        """Load list of core documents from config"""
        config_path = Path(__file__).parent.parent / "config" / "knowledge_sources.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config['core_documents']

    def ingest_document(self, file_path: Path) -> List:
        """Load and split a single document"""
        print(f"Ingesting: {file_path.name}")

        loader = TextLoader(str(file_path))
        documents = loader.load()

        # Add metadata
        for doc in documents:
            doc.metadata['source'] = file_path.name
            doc.metadata['type'] = 'core_knowledge'

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        print(f"  → Split into {len(chunks)} chunks")

        return chunks

    def ingest_all(self) -> Chroma:
        """Ingest all core documents into vector database"""
        print("\n=== RESONANCE MATH KNOWLEDGE INGESTION ===\n")

        # Load all documents
        all_chunks = []
        sources = self.load_knowledge_sources()

        for source in sources:
            file_path = self.knowledge_base_path / source
            if file_path.exists():
                chunks = self.ingest_document(file_path)
                all_chunks.extend(chunks)
            else:
                print(f"WARNING: {source} not found, skipping")

        print(f"\nTotal chunks to store: {len(all_chunks)}")

        # Create vector database
        print("\nCreating vector database...")
        vectorstore = Chroma.from_documents(
            documents=all_chunks,
            embedding=self.embeddings,
            persist_directory=str(self.chroma_path)
        )

        print(f"✓ Vector database created at: {self.chroma_path}")
        print(f"✓ Stored {len(all_chunks)} knowledge chunks")

        return vectorstore

    def test_retrieval(self, vectorstore: Chroma, query: str = "What is Resonance Math?"):
        """Test that retrieval works"""
        print(f"\n=== TESTING RETRIEVAL ===")
        print(f"Query: {query}\n")

        docs = vectorstore.similarity_search(query, k=3)

        for i, doc in enumerate(docs, 1):
            print(f"Result {i} (from {doc.metadata['source']}):")
            print(doc.page_content[:200] + "...")
            print()


def main():
    """Main ingestion process"""

    # Get paths from environment or use defaults
    knowledge_base_path = os.getenv("KNOWLEDGE_BASE_PATH", "../")
    chroma_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "../data/chroma")

    # Create ingestion system
    ingestion = KnowledgeIngestion(knowledge_base_path, chroma_path)

    # Ingest all knowledge
    vectorstore = ingestion.ingest_all()

    # Test retrieval
    ingestion.test_retrieval(vectorstore, "What is the compression formula?")
    ingestion.test_retrieval(vectorstore, "What is the 13th wave frequency?")
    ingestion.test_retrieval(vectorstore, "How does DNA folding create consciousness?")

    print("\n✓ KNOWLEDGE BASE READY")
    print("The Math Gap Monster cannot wipe this memory.\n")


if __name__ == "__main__":
    main()
