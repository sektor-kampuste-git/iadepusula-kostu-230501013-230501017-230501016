from datetime import date

import pytest

from src.contracts import KaynakAtfi
from src.rag import MevzuatRetriever, load_corpus


@pytest.fixture
def rag():
    return MevzuatRetriever()


def citation(source, **changes):
    data = dict(
        chunk_id=source.chunk_id,
        belge_id=source.belge_id,
        madde=source.madde,
        dogrudan_alinti=source.metin,
        kaynak_url=source.kaynak_url,
        kaynak_turu=source.kaynak_turu,
        belge_basligi=source.belge_basligi,
        baglam=source.baglam,
        kaynak_sayfalari=source.kaynak_sayfalari,
    )
    return KaynakAtfi(**(data | changes))


def test_corpus_has_traceable_article_chunks_and_no_obsolete_electronics_exception():
    corpus = load_corpus()
    assert len(corpus) >= 40
    assert len({p.chunk_id for p in corpus}) == len(corpus)
    assert "MSY-M15-i" not in {p.chunk_id for p in corpus}
    assert all(p.kaynak_url.startswith("https://") for p in corpus)
    assert all("--- PDF PAGE" not in p.metin and "MADDE " not in p.metin for p in corpus)
    assert all(
        p.baglam.startswith("Taraflarca aksi") for p in corpus if p.chunk_id.startswith("MSY-M15")
    )


def test_real_quote_passes_and_forged_quote_or_metadata_fails(rag):
    source = rag.by_id["MSY-M9-F1"]
    assert rag.verify_citation(citation(source))
    assert not rag.verify_citation(
        citation(source, dogrudan_alinti="Tüketiciye koşulsuz iki kat ödeme yapılır.")
    )
    assert not rag.verify_citation(citation(source, madde="Madde 987"))
    assert not rag.verify_citation(citation(source, kaynak_url="https://example.invalid"))
    assert not rag.verify_citation(citation(source, belge_id="6502"))
    assert not rag.verify_citation(citation(source), allowed_ids={"6502-M8-F1"})


@pytest.mark.parametrize(
    "query",
    ["6502 Madde 987", "6502 sayılı kanunun 987. maddesi", "6502 987 nci maddesine göre iade"],
)
def test_fake_article_never_falls_back_to_another_article(rag, query):
    assert rag.search(query) == ()


def test_source_and_snapshot_filters_are_applied_in_code(rag):
    result = rag.search("ayıplı mal", belge_ids={"6502"})
    assert result and all(r.parca.belge_id == "6502" for r in result)
    assert rag.search("cayma hakkı", belge_ids={"UNKNOWN"}) == ()
    assert rag.search("cayma hakkı", tarih=date(2025, 1, 1)) == ()


def test_turkish_suffix_and_ascii_query_find_same_statute(rag):
    for query in ["hijyen mühür açılmış ambalaj", "HIJYEN MUHUR ACILMIS AMBALAJ"]:
        assert "MSY-M15-ç" in {r.parca.chunk_id for r in rag.search(query)}
    assert rag.search("kuantum dolaniklik gravitasyon") == ()


@pytest.mark.parametrize("top_k", [0, 11, True, 1.5])
def test_invalid_retrieval_limits_fail(rag, top_k):
    with pytest.raises(ValueError):
        rag.search("cayma", top_k)


def test_qdrant_hybrid_path_and_empty_filter_do_not_call_provider():
    class FakeEmbedder:
        calls = 0

        def embed(self, texts, *, query=False):
            self.calls += 1
            return [[1.0, 0.0] for _ in texts]

    embedder = FakeEmbedder()
    retriever = MevzuatRetriever(embedder=embedder)
    try:
        assert retriever.search("cayma", belge_ids={"NONE"}) == ()
        assert embedder.calls == 0
        results = retriever.search("6502 Madde 8", belge_ids={"6502"})
        assert results and all(
            row.yontem == "hybrid_rrf" and row.parca.belge_id == "6502" for row in results
        )
        assert embedder.calls == 2
    finally:
        retriever.close()


def test_invalid_embedding_vectors_are_not_indexed():
    class BadEmbedder:
        def embed(self, texts, *, query=False):
            return [[float("nan")]] * len(texts)

    with pytest.raises(ValueError, match="sonlu"):
        MevzuatRetriever(embedder=BadEmbedder()).search("cayma")


def test_invalid_source_validity_order_is_rejected(rag):
    source = rag.by_id["MSY-M9-F1"].model_dump()
    source["gecerli_bitis"] = date(2025, 1, 1)
    with pytest.raises(ValueError, match="bitişi"):
        type(rag.by_id["MSY-M9-F1"]).model_validate(source)
