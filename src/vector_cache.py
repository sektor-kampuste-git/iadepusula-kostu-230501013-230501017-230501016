"""JSON cache of public corpus embeddings. User queries are never written here."""

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from time import time


def _finite_number(value) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def valid_vectors(vectors, count: int) -> bool:
    return (
        isinstance(vectors, list)
        and len(vectors) == count
        and bool(vectors)
        and isinstance(vectors[0], list)
        and bool(vectors[0])
        and all(
            isinstance(vector, list)
            and len(vector) == len(vectors[0])
            and all(_finite_number(value) for value in vector)
            and any(value != 0 for value in vector)
            for vector in vectors
        )
    )


class CorpusEmbeddingCache:
    def __init__(
        self, directory: Path, encoder: str, texts: list[str], max_age_seconds: int = 86400
    ):
        identity = {"format": 1, "encoder": encoder, "texts": texts}
        self.key = hashlib.sha256(
            json.dumps(identity, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        self.path = Path(directory) / (self.key + ".json")
        self.count = len(texts)
        self.max_age_seconds = max_age_seconds

    def read(self) -> list[list[float]] | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            age = time() - data["created_at"]
            if (
                data["key"] == self.key
                and data["format"] == 1
                and 0 <= age <= self.max_age_seconds
                and valid_vectors(data["vectors"], self.count)
            ):
                return data["vectors"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return None

    def write(self, vectors: list[list[float]]) -> bool:
        if not valid_vectors(vectors, self.count):
            raise ValueError("Geçersiz vektörler önbelleğe yazılamaz")
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".embedding-",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(
                    {"format": 1, "key": self.key, "created_at": time(), "vectors": vectors}, stream
                )
            os.replace(temporary, self.path)
            return True
        except OSError:
            return False  # Cache is optional; a read-only disk does not invalidate retrieval.
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
