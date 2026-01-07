import json
from typing import List, Optional
from sqlalchemy.exc import OperationalError

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except Exception:
    Vector = None
    HAS_PGVECTOR = False

from . import models


class VectorStore:
    """Abstract vector storage with optional pgvector support.

    Usage:
      store = VectorStore()
      store.save_embedding(db, resume_id, vector)
    """

    def save_embedding(self, db, resume_id: int, vector: List[float]):
        vec_json = json.dumps(vector)
        emb = models.Embedding(vector=vec_json)
        db.add(emb)
        db.commit()
        db.refresh(emb)

        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if resume:
            resume.embedding_id = emb.id
            db.add(resume)
            db.commit()
        return emb

    def get_embedding(self, db, resume_id: int) -> Optional[List[float]]:
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if not resume or not resume.embedding_id:
            return None
        emb = db.query(models.Embedding).filter(models.Embedding.id == resume.embedding_id).first()
        if not emb:
            return None
        try:
            return json.loads(emb.vector)
        except Exception:
            return None
