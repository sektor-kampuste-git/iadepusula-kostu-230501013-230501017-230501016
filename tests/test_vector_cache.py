import json

import pytest

from src.rag import MevzuatRetriever, load_corpus
from src.vector_cache import CorpusEmbeddingCache


class CountingEmbedder:
    cache_identity = "test.invalid|model-v1"

    def __init__(self):
        self.corpus_calls = 0
        self.query_calls = 0

    def embed(self, texts, *, query=False):
        if query:
            self.query_calls += 1
        else:
            self.corpus_calls += 1
        return [[1.0, 0.0] for _ in texts]


def search(cache, encoder):
    retriever = MevzuatRetriever(embedder=encoder, cache_dir=cache)
    try:
        assert retriever.search("14 gün cayma hakkı")
        return retriever.cache_status
    finally:
        retriever.close()


def test_new_retriever_reuses_public_vectors_but_never_caches_query(tmp_path):
    first = CountingEmbedder()
    assert search(tmp_path, first) == "stored"
    assert first.corpus_calls == first.query_calls == 1
    second = CountingEmbedder()
    assert search(tmp_path, second) == "hit"
    assert second.corpus_calls == 0 and second.query_calls == 1
    data = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert set(data) == {"format", "key", "created_at", "vectors"}
    assert not list(tmp_path.glob("*.tmp"))


def test_model_or_corpus_change_invalidates_cache(tmp_path):
    assert search(tmp_path, CountingEmbedder()) == "stored"
    different = CountingEmbedder()
    different.cache_identity = "test.invalid|model-v2"
    assert search(tmp_path, different) == "stored"
    assert different.corpus_calls == 1
    corpus = list(load_corpus())
    corpus[0] = corpus[0].model_copy(update={"baglam": "New source context"})
    encoder = CountingEmbedder()
    rag = MevzuatRetriever(corpus, embedder=encoder, cache_dir=tmp_path)
    try:
        rag.search("cayma")
        assert encoder.corpus_calls == 1
    finally:
        rag.close()


@pytest.mark.parametrize(
    "mutation", ["invalid_json", "expired", "wrong_count", "nan", "zero", "huge_integer"]
)
def test_corrupt_or_expired_cache_is_rebuilt(tmp_path, mutation):
    search(tmp_path, CountingEmbedder())
    path = next(tmp_path.glob("*.json"))
    data = json.loads(path.read_text())
    if mutation == "invalid_json":
        path.write_text("broken")
    else:
        if mutation == "expired":
            data["created_at"] = 0
        elif mutation == "wrong_count":
            data["vectors"] = [[1, 0]]
        elif mutation == "nan":
            data["vectors"][0][0] = float("nan")
        elif mutation == "huge_integer":
            data["vectors"][0][0] = 10**400
        else:
            data["vectors"][0] = [0, 0]
        path.write_text(json.dumps(data))
    encoder = CountingEmbedder()
    assert search(tmp_path, encoder) == "stored"
    assert encoder.corpus_calls == 1


def test_failed_cache_write_is_optional(tmp_path):
    path = tmp_path / "file"
    path.write_text("not a directory")
    cache = CorpusEmbeddingCache(path, "encoder", ["public law"])
    assert cache.write([[1.0]]) is False
    assert cache.read() is None


def test_large_corpus_is_embedded_in_bounded_batches():
    corpus = load_corpus()
    large = [
        p.model_copy(update={"chunk_id": f"COPY-{i}-{p.chunk_id}"})
        for i in range(2)
        for p in corpus
    ]

    class BoundedEmbedder(CountingEmbedder):
        def embed(self, texts, *, query=False):
            assert len(texts) <= 64
            return super().embed(texts, query=query)

    encoder = BoundedEmbedder()
    retriever = MevzuatRetriever(large, embedder=encoder)
    try:
        retriever.search("cayma")
        assert encoder.corpus_calls == 2 and encoder.query_calls == 1
    finally:
        retriever.close()
