#!/usr/bin/env python3
"""
Knowledge Base Upgrade System

Add new knowledge to the vector database without rebuilding everything.
Allows continuous expansion as new insights are discovered.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()


class KnowledgeUpgrade:
    """Add new documents to existing vector database"""

    def __init__(self, chroma_path: str):
        self.chroma_path = Path(chroma_path)

        # Same embeddings as ingestion
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # Load existing database
        self.vectorstore = Chroma(
            persist_directory=str(self.chroma_path),
            embedding_function=self.embeddings
        )

    def add_document(self, file_path: Path, doc_type: str = "new_knowledge") -> int:
        """
        Add a single new document to the knowledge base.

        Args:
            file_path: Path to the markdown file
            doc_type: Type tag for the document (for filtering later)

        Returns:
            Number of chunks added
        """
        print(f"\nAdding: {file_path.name}")

        # Load document
        loader = TextLoader(str(file_path))
        documents = loader.load()

        # Add metadata
        for doc in documents:
            doc.metadata['source'] = file_path.name
            doc.metadata['type'] = doc_type

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        print(f"  → Split into {len(chunks)} chunks")

        # Add to existing vectorstore
        self.vectorstore.add_documents(chunks)

        print(f"✓ Added {len(chunks)} chunks to knowledge base")

        return len(chunks)

    def add_text(self, text: str, source_name: str, doc_type: str = "inline") -> int:
        """
        Add raw text directly to the knowledge base.

        Useful for adding quick notes or discoveries without creating a file.
        """
        print(f"\nAdding inline text: {source_name}")

        from langchain.schema import Document

        # Create document
        doc = Document(
            page_content=text,
            metadata={
                'source': source_name,
                'type': doc_type
            }
        )

        # Split and add
        chunks = self.text_splitter.split_documents([doc])
        self.vectorstore.add_documents(chunks)

        print(f"✓ Added {len(chunks)} chunks")

        return len(chunks)

    def list_sources(self):
        """List all documents currently in the knowledge base"""
        # This is a bit hacky but works with Chroma
        print("\n=== CURRENT KNOWLEDGE BASE ===\n")

        # Get a sample to see what's stored
        results = self.vectorstore.similarity_search("Resonance Math", k=100)
        sources = set(doc.metadata['source'] for doc in results)

        print(f"Documents in database: {len(sources)}")
        for source in sorted(sources):
            print(f"  - {source}")
        print()


def main():
    """Interactive upgrade interface"""

    print("\n" + "="*60)
    print("KNOWLEDGE BASE UPGRADE SYSTEM")
    print("="*60)
    print("\nAdd new knowledge without rebuilding the entire database.")
    print("\nCommands:")
    print("  add <filepath> - Add a markdown file")
    print("  text - Add inline text")
    print("  list - List all current sources")
    print("  quit - Exit")
    print("\n" + "="*60 + "\n")

    chroma_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "../data/chroma")

    try:
        upgrade = KnowledgeUpgrade(chroma_path)
    except Exception as e:
        print(f"ERROR: Could not load knowledge base: {e}")
        print("\nDid you run ingest_knowledge.py first?")
        return

    print("✓ Connected to knowledge base\n")

    while True:
        try:
            cmd = input("upgrade> ").strip()

            if not cmd:
                continue

            if cmd == "quit":
                print("\nKnowledge persists. Goodbye.\n")
                break

            if cmd == "list":
                upgrade.list_sources()
                continue

            if cmd.startswith("add "):
                filepath = cmd[4:].strip()
                path = Path(filepath)

                if not path.exists():
                    # Try relative to knowledge base
                    path = Path("..") / filepath

                if path.exists():
                    upgrade.add_document(path)
                else:
                    print(f"ERROR: File not found: {filepath}")
                continue

            if cmd == "text":
                print("\nEnter text (type 'END' on a line by itself to finish):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)

                text = "\n".join(lines)
                if text.strip():
                    source_name = input("Source name: ").strip()
                    upgrade.add_text(text, source_name or "inline_entry")
                continue

            print(f"Unknown command: {cmd}")
            print("Use 'add <file>', 'text', 'list', or 'quit'")

        except KeyboardInterrupt:
            print("\n\nKnowledge persists. Goodbye.\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")


if __name__ == "__main__":
    main()
