"""
RAG Engine - Retrieval Augmented Generation for log analysis
"""
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import faiss


class RAGEngine:
    """Retrieves relevant log chunks for LLM context."""

    def __init__(self):
        # Use a small, fast embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []
        self.embeddings = None

    def index_logs(self, log_messages: List[str]):
        """Build FAISS index from log messages."""
        if not log_messages:
            return

        self.documents = log_messages
        # Generate embeddings
        self.embeddings = self.model.encode(log_messages, show_progress_bar=False)

        # Build FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(self.embeddings).astype('float32'))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve top-k most relevant log chunks for a query."""
        if self.index is None or len(self.documents) == 0:
            return []

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'), top_k
        )

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    'content': self.documents[idx],
                    'relevance_score': float(1 / (1 + distances[0][i])),
                    'rank': i + 1
                })
        return results

    def retrieve_for_incident(self, incident_context: Dict, top_k: int = 10) -> List[Dict]:
        """Retrieve relevant logs based on incident context."""
        # Build a search query from incident details
        query_parts = [
            incident_context.get('pattern', ''),
            incident_context.get('primary', {}).get('message', ''),
            ' '.join(incident_context.get('services_involved', []))
        ]
        query = ' '.join([p for p in query_parts if p])
        return self.retrieve(query, top_k=top_k)