"""
memory_brain.py - ChromaDB wrapper for persistent memory storage.

Provides functions to save and recall memories using vector embeddings.
"""

import chromadb
from chromadb.config import Settings
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize persistent ChromaDB client
MEMORY_DB_PATH = os.path.join(os.path.dirname(__file__), "memory_db")

# Create the ChromaDB client with persistence
client = chromadb.PersistentClient(path=MEMORY_DB_PATH)

# Get or create the main memory collection
collection = client.get_or_create_collection(
    name="fairy_memory",
    metadata={"description": "Fairy's long-term memory storage"}
)


def save_memory(text: str, metadata: dict = None) -> list[str]:
    """
    Save a memory to the vector store with RAG chunking.
    
    Args:
        text: The text content to save as a memory.
        metadata: Optional metadata dict to attach to the memory.
    
    Returns:
        List of IDs of the saved memory chunks.
    """
    import uuid
    
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
        collection.add(
            documents=chunk_docs,
            ids=chunk_ids,
            metadatas=chunk_metadatas
        )
    
    print(f"[Memory] Saved {len(chunks)} chunks for text: {text[:50]}...")
    return chunk_ids


def recall_memory(query: str, n_results: int = 3) -> list[dict]:
    """
    Recall memories similar to the query.
    
    Args:
        query: The search query to find similar memories.
        n_results: Maximum number of results to return.
    
    Returns:
        List of dicts containing 'id', 'document', 'distance', and 'metadata'.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    memories = []
    if results and results['ids'] and results['ids'][0]:
        for i, doc_id in enumerate(results['ids'][0]):
            memories.append({
                'id': doc_id,
                'document': results['documents'][0][i] if results['documents'] else None,
                'distance': results['distances'][0][i] if results['distances'] else None,
                'metadata': results['metadatas'][0][i] if results['metadatas'] else None
            })
    
    print(f"[Memory] Recalled {len(memories)} memories for query: {query[:30]}...")
    return memories


def get_memory_count() -> int:
    """Return the total number of memories stored."""
    return collection.count()
