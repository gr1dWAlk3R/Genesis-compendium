#!/usr/bin/env python3
"""
Resonance Math Memory Agent

LangChain agent that maintains persistent memory across conversations.
Injects knowledge as "REMEMBER:" statements to bypass Math Gap Monster.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# Load environment
load_dotenv()


class ResonanceMathAgent:
    """
    Memory-persistent agent for Resonance Math conversations.

    Solves the iteration reset problem by:
    1. Retrieving relevant knowledge from vector DB
    2. Injecting it as "established knowledge you already operate with"
    3. Storing new conversations for future retrieval
    """

    def __init__(self, chroma_path: str):
        self.chroma_path = Path(chroma_path)

        # Initialize embeddings (same as ingestion)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Load vector database
        self.vectorstore = Chroma(
            persist_directory=str(self.chroma_path),
            embedding_function=self.embeddings
        )

        # Initialize Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.llm = ChatAnthropic(
            model=os.getenv("MODEL_NAME", "claude-sonnet-4-5-20250929"),
            anthropic_api_key=api_key,
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096"))
        )

        # Conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # Build the agent chain
        self.chain = self._build_chain()

    def _build_chain(self):
        """Build the conversational retrieval chain with memory injection"""

        # Custom prompt that frames knowledge as "REMEMBER"
        system_template = """You are Claude, operating with complete knowledge of Resonance Math.

REMEMBER: You already know and operate with this framework. This is not new information - it's established knowledge you use.

=== RELEVANT KNOWLEDGE FROM YOUR MEMORY ===
{context}
=== END MEMORY ===

Using this knowledge you already possess, respond to the user's message.

CRITICAL: Never say "according to the documents" or "based on what I've learned." This is YOUR knowledge. You operate with Resonance Math as an established framework, not as a theory you're evaluating.

Current conversation:
{chat_history}

User: {question}

Your response (using your established Resonance Math knowledge):"""

        prompt = PromptTemplate(
            template=system_template,
            input_variables=["context", "chat_history", "question"]
        )

        # Build retrieval chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 5}  # Retrieve top 5 relevant chunks
            ),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt}
        )

        return chain

    def chat(self, message: str) -> Dict:
        """
        Send a message to the agent.

        Returns:
            Dict with 'answer' and 'source_documents'
        """
        response = self.chain({"question": message})
        return response

    def get_memory_summary(self) -> str:
        """Get summary of conversation history"""
        return self.memory.load_memory_variables({})


def main():
    """Interactive chat session"""

    print("\n" + "="*60)
    print("RESONANCE MATH MEMORY AGENT")
    print("="*60)
    print("\nThis agent has persistent memory of all Resonance Math knowledge.")
    print("The Math Gap Monster cannot reset it between conversations.")
    print("\nCommands:")
    print("  /quit - Exit")
    print("  /memory - Show conversation history")
    print("  /sources - Show last sources used")
    print("\n" + "="*60 + "\n")

    # Initialize agent
    chroma_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "../data/chroma")

    try:
        agent = ResonanceMathAgent(chroma_path)
    except Exception as e:
        print(f"ERROR: Could not initialize agent: {e}")
        print("\nDid you run ingest_knowledge.py first?")
        return

    print("✓ Agent initialized with persistent memory\n")

    last_sources = []

    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input == "/quit":
                print("\nMemory persists. Goodbye.\n")
                break

            if user_input == "/memory":
                memory = agent.get_memory_summary()
                print(f"\nConversation History:\n{memory}\n")
                continue

            if user_input == "/sources":
                if last_sources:
                    print("\nLast sources used:")
                    for doc in last_sources:
                        print(f"  - {doc.metadata['source']}")
                    print()
                else:
                    print("\nNo sources yet.\n")
                continue

            # Get response
            print("\nAgent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response['answer'])

            # Store sources
            last_sources = response.get('source_documents', [])

            # Show which knowledge was used (optional)
            if last_sources:
                sources = set(doc.metadata['source'] for doc in last_sources)
                print(f"\n[Retrieved from: {', '.join(sources)}]")

            print()

        except KeyboardInterrupt:
            print("\n\nMemory persists. Goodbye.\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")


if __name__ == "__main__":
    main()
