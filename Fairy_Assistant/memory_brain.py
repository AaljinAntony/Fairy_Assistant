"""
memory_brain.py - ChromaDB wrapper for persistent memory storage.

Provides a MemoryBrain class to save and recall memories using vector embeddings.
"""

import chromadb
from chromadb.config import Settings
import os
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter

class MemoryBrain:
    def __init__(self):
        """Initialize persistent ChromaDB client."""
        self.db_path = os.path.join(os.path.dirname(__file__), "memory_db")
        
        # Create the ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or create the main memory collection
        self.collection = self.client.get_or_create_collection(
            name="fairy_memory",
            metadata={"description": "Fairy's long-term memory storage"}
        )
        print(f"[MemoryBrain] Initialized at {self.db_path}")

    def store(self, text: str, metadata: dict = None) -> list[str]:
        """
        Save a memory to the vector store with RAG chunking.
        
        Args:
            text: The text content to save as a memory.
            metadata: Optional metadata dict to attach to the memory.
        
        Returns:
            List of IDs of the saved memory chunks.
        """
        if not text:
            return []

        # Initialize splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        
        # Split text into chunks
        chunks = splitter.split_text(text)
        
        chunk_ids = []
        chunk_docs = []
        chunk_metadatas = []
        
        base_id = str(uuid.uuid4())
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{base_id}_{i}"
            chunk_ids.append(chunk_id)
            chunk_docs.append(chunk)
            
            # Prepare metadata for this chunk
            chunk_meta = metadata.copy() if metadata else {}
            chunk_meta['chunk_index'] = i
            chunk_meta['total_chunks'] = len(chunks)
            chunk_meta['source_id'] = base_id
            chunk_metadatas.append(chunk_meta)
        
        if chunk_ids:
            self.collection.add(
                documents=chunk_docs,
                ids=chunk_ids,
                metadatas=chunk_metadatas
            )
        
        print(f"[MemoryBrain] Stored {len(chunks)} chunks.")
        return chunk_ids

    def retrieve(self, query: str, n_results: int = 3) -> list[dict]:
        """
        Recall memories similar to the query.
        
        Args:
            query: The search query to find similar memories.
            n_results: Maximum number of results to return.
        
        Returns:
            List of dicts containing 'document' and 'metadata'.
        """
        if not query:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        memories = []
        if results and results['ids'] and results['ids'][0]:
            for i, _ in enumerate(results['ids'][0]):
                memories.append({
                    'text': results['documents'][0][i] if results['documents'] else "",
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0.0
                })
        
        print(f"[MemoryBrain] Retrieved {len(memories)} memories for query: '{query[:20]}...'")
        return memories

    def get_count(self) -> int:
        """Return the total number of memories stored."""
        return self.collection.count()
