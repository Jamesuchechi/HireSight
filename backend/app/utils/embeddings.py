"""
Embedding and semantic similarity utilities.
Uses Sentence Transformers for high-quality embeddings.
"""
import logging
import hashlib
import pickle
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import settings

def cosine_similarity(a, b):
    """
    Numpy-based cosine similarity compatible with sklearn.metrics.pairwise.cosine_similarity.
    Accepts 1D or 2D arrays and returns an array of shape (n_a, n_b).
    """
    a = np.asarray(a)
    b = np.asarray(b)
    if a.ndim == 1:
        a = a.reshape(1, -1)
    if b.ndim == 1:
        b = b.reshape(1, -1)
    numerator = np.dot(a, b.T)
    denom = np.linalg.norm(a, axis=1, keepdims=True) * np.linalg.norm(b, axis=1, keepdims=True).T
    denom = np.where(denom == 0, 1e-8, denom)
    return numerator / denom

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of Sentence Transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def _get_cache_path(self, text: str) -> Path:
        """
        Get cache file path for a text embedding.
        Uses hash of text as filename.
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return settings.EMBEDDINGS_CACHE_DIR / f"{self.model_name}_{text_hash}.pkl"
    
    def _load_from_cache(self, text: str) -> Optional[np.ndarray]:
        """Load embedding from cache if it exists."""
        cache_path = self._get_cache_path(text)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Error loading from cache: {e}")
                return None
        return None
    
    def _save_to_cache(self, text: str, embedding: np.ndarray):
        """Save embedding to cache."""
        cache_path = self._get_cache_path(text)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")
    
    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding vector (1D numpy array)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return np.zeros(settings.EMBEDDING_DIMENSION)
        
        # Try cache first
        if use_cache:
            cached = self._load_from_cache(text)
            if cached is not None:
                return cached
        
        # Generate embedding
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Save to cache
            if use_cache:
                self._save_to_cache(text, embedding)
            
            return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return np.zeros(settings.EMBEDDING_DIMENSION)
    
    def embed_texts_batch(self, texts: List[str], use_cache: bool = True) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache for all texts
        for idx, text in enumerate(texts):
            if use_cache:
                cached = self._load_from_cache(text)
                if cached is not None:
                    embeddings.append((idx, cached))
                else:
                    texts_to_embed.append(text)
                    indices_to_embed.append(idx)
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(idx)
        
        # Batch encode remaining texts
        if texts_to_embed:
            try:
                batch_embeddings = self.model.encode(texts_to_embed, convert_to_numpy=True)
                
                # Save to cache and collect results
                for idx, text, embedding in zip(indices_to_embed, texts_to_embed, batch_embeddings):
                    if use_cache:
                        self._save_to_cache(text, embedding)
                    embeddings.append((idx, embedding))
            except Exception as e:
                logger.error(f"Error in batch embedding: {e}")
                # Return empty embeddings for failed texts
                for idx in indices_to_embed:
                    embeddings.append((idx, np.zeros(settings.EMBEDDING_DIMENSION)))
        
        # Sort by original index
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        if embedding1.size == 0 or embedding2.size == 0:
            return 0.0
        
        try:
            # Reshape for sklearn if needed
            emb1 = embedding1.reshape(1, -1)
            emb2 = embedding2.reshape(1, -1)
            similarity = cosine_similarity(emb1, emb2)[0][0]
            return float(max(0, min(1, similarity)))  # Clamp to [0, 1]
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def find_similar_texts(
        self, 
        query_embedding: np.ndarray, 
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to a query.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top matches to return
            
        Returns:
            List of (index, similarity_score) tuples sorted by similarity descending
        """
        if not candidate_embeddings:
            return []
        
        try:
            query = query_embedding.reshape(1, -1)
            candidates = np.array(candidate_embeddings)
            similarities = cosine_similarity(query, candidates)[0]
            
            # Get top k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            results = [(int(idx), float(similarities[idx])) for idx in top_indices]
            return results
        except Exception as e:
            logger.error(f"Error finding similar texts: {e}")
            return []


# Global embedding service instance (lazy loaded)
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service (singleton pattern)."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
