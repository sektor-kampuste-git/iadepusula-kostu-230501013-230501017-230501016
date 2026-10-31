"""Turkish lexical retrieval plus optional EVREN embeddings/Qdrant hybrid search.

Scores rank evidence; they are not legal confidence probabilities. Citation
verification binds every quote to the actual retrieved passage and its metadata.
"""

import hashlib
import json
import re
import unicodedata
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Protocol

from rank_bm25 import BM25Okapi

from src.contracts import AramaSonucu, KaynakAtfi, KaynakParcasi
from src.paths import CORPUS
from src.references import parse_references
from src.vector_cache import CorpusEmbeddingCache, valid_vectors

STOPWORDS = set("ve veya ile bir bu da de için olan olarak ise mi mı mu mü bana benim göre".split())
ALIASES = {
    "bozuk": "ayıplı mal arıza",
    "arizali": "ayıplı mal",
    "kirik": "ayıplı mal hasar",
    "calismiyor": "ayıplı mal arıza",
    "bozuldu": "ayıplı mal arıza",
    "kusurlu": "ayıplı mal",
    "14": "on dört",
    "ondort": "on dört",
    "cayma": "on dört gün",
    "vazgectim": "cayma hakkı",
    "begenmedim": "cayma hakkı",
    "isim": "kişisel ihtiyaç",
    "baskili": "kişisel ihtiyaç",
    "kisisellestirilmis": "kişisel ihtiyaç",
    "pasta": "çabuk bozulabilen",
    "muhur": "koruyucu unsurları hijyen",
    "kutusu": "ambalaj",
    "kargo": "taşıyıcı teslim",
    "fatura": "bedel ödeme",
    "tazminat": "seçimlik hak",
    "garanti": "zamanaşımı",
}


def normalize(text: str) -> str:
    text = text.replace("İ", "i").replace("I", "ı").lower()
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", text.replace("ı", "i"))
        if not unicodedata.combining(c)
    )


STOPWORDS = {normalize(word) for word in STOPWORDS}


def tokenize(text: str, *, expand: bool = False) -> list[str]:
    words = re.findall(r"[a-z0-9]+", normalize(text))
    if expand:
        extra = " ".join(ALIASES.get(word, "") for word in words)
        if re.search(r"teslimden once|henuz.{0,30}teslim|teslim edilmedi", normalize(text)):
            extra += " sözleşmenin kurulmasından malın teslimine kadar"
        words += re.findall(r"[a-z0-9]+", normalize(extra))
    tokens = []
    for word in words:
        if word in STOPWORDS or len(word) < 2:
            continue
        tokens.append(word)
        # Prefix features help Turkish suffix variation without altering quoted source text.
        if len(word) >= 5:
            tokens.append(word[:5] + "*")
    return tokens


def load_corpus(directory: Path | str = CORPUS) -> tuple[KaynakParcasi, ...]:
    records = []
    for path in sorted(Path(directory).glob("*.json")):
        records.extend(
            KaynakParcasi.model_validate(row)
            for row in json.loads(path.read_text(encoding="utf-8"))
        )
    if not records:
        raise ValueError("Mevzuat derlemi boş")
    ids = [record.chunk_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Tekrarlanan kaynak parçası kimliği")
    for record in records:
        if not record.kaynak_url.startswith("https://") or not re.fullmatch(
            r"[a-f0-9]{64}", record.kaynak_sha256
        ):
            raise ValueError("Kaynak URL veya içerik özeti geçersiz")
    return tuple(records)


class Embedder(Protocol):
    def embed(self, texts: Sequence[str], *, query: bool = False) -> list[list[float]]: ...


class MevzuatRetriever:
    def __init__(
        self,
        corpus: Sequence[KaynakParcasi] | None = None,
        *,
        embedder: Embedder | None = None,
        cache_dir: Path | None = None,
    ):
        self.corpus = tuple(corpus) if corpus is not None else load_corpus()
        if not self.corpus:
            raise ValueError("Mevzuat derlemi boş")
        self.by_id = {record.chunk_id: record for record in self.corpus}
        if len(self.by_id) != len(self.corpus):
            raise ValueError("Tekrarlanan kaynak parçası kimliği")
        self.fingerprint = hashlib.sha256(
            "\n".join(p.model_dump_json() for p in self.corpus).encode()
        ).hexdigest()
        self._bm25 = BM25Okapi(
            [
                tokenize(
                    f"{p.baslik} {p.madde} {' '.join(p.anahtar_kelimeler)} {p.baglam or ''} {p.metin}"
                )
                for p in self.corpus
            ]
        )
        self._embedder = embedder
        self._qdrant = None
        self._cache_dir = cache_dir
        self.cache_status = "disabled"
        self.configuration = {"version": 2, "backend": "hybrid_rrf" if embedder else "bm25"}

    def _ensure_vectors(self):
        if self._qdrant is not None:
            return
        from qdrant_client import QdrantClient, models

        texts = [f"{p.baslik}\n{p.baglam or ''}\n{p.metin}" for p in self.corpus]
        identity = getattr(self._embedder, "cache_identity", None)
        cache = (
            CorpusEmbeddingCache(self._cache_dir, identity, texts)
            if self._cache_dir and isinstance(identity, str)
            else None
        )
        vectors = cache.read() if cache else None
        self.cache_status = "hit" if vectors is not None else "miss" if cache else "disabled"
        if vectors is None:
            vectors = []
            for start in range(0, len(texts), 64):
                vectors.extend(self._embedder.embed(texts[start : start + 64]))
        if not valid_vectors(vectors, len(self.corpus)):
            raise ValueError("Geçersiz gömme boyutu veya sonlu olmayan değer")
        if cache and self.cache_status != "hit":
            self.cache_status = "stored" if cache.write(vectors) else "write_failed"
        dim = len(vectors[0])
        client = QdrantClient(":memory:")
        try:
            client.create_collection(
                "mevzuat",
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )
            client.upsert(
                "mevzuat",
                points=[
                    models.PointStruct(id=i, vector=v, payload={"chunk_id": p.chunk_id})
                    for i, (p, v) in enumerate(zip(self.corpus, vectors, strict=True))
                ],
            )
        except Exception:
            client.close()
            raise
        self._qdrant = client

    def search(
        self,
        sorgu: str,
        top_k: int = 3,
        *,
        belge_ids: set[str] | None = None,
        tarih: date | None = None,
    ) -> tuple[AramaSonucu, ...]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
            raise ValueError("top_k 1 ile 10 arasında olmalıdır")
        if not isinstance(sorgu, str) or len(sorgu) > 4000:
            raise ValueError("Sorgu en fazla 4000 karakter olmalıdır")
        tokens = tokenize(sorgu, expand=True)
        if not tokens:
            return ()
        scores = self._bm25.get_scores(tokens)
        eligible = [
            i
            for i, p in enumerate(self.corpus)
            if p.kaynak_turu != "demo_politika"
            and (belge_ids is None or p.belge_id in belge_ids)
            and (
                tarih is None
                or p.gecerli_baslangic <= tarih
                and (p.gecerli_bitis is None or tarih <= p.gecerli_bitis)
            )
        ]
        references = parse_references(sorgu)
        if references:
            if any(ref.document is None for ref in references) and not (
                belge_ids and len(belge_ids) == 1
            ):
                return ()  # A bare article number cannot resolve the intended instrument.
            groups = [
                [i for i in eligible if ref.matches(self.corpus[i].belge_id, self.corpus[i].madde)]
                for ref in references
            ]
            if any(not group for group in groups):
                return ()  # Never silently discard an unknown requested provision.
            eligible = sorted({i for group in groups for i in group})
        lexical = sorted(
            (i for i in eligible if scores[i] > 0),
            key=lambda i: (-scores[i], self.corpus[i].chunk_id),
        )
        method = "bm25"
        final = {i: float(scores[i]) for i in lexical}
        if self._embedder and eligible:
            self._ensure_vectors()
            vector = self._embedder.embed([sorgu], query=True)[0]
            hits = self._qdrant.query_points("mevzuat", query=vector, limit=len(self.corpus)).points
            # Cosine threshold is a retrieval heuristic, not a calibrated confidence score.
            eligible_set = set(eligible)
            dense = [
                int(hit.id) for hit in hits if int(hit.id) in eligible_set and hit.score >= 0.55
            ]
            final = {}
            for ranking in [lexical, dense]:
                for rank, i in enumerate(ranking):
                    final[i] = final.get(i, 0.0) + 1 / (60 + rank + 1)
            method = "hybrid_rrf"
        ranked = sorted(final, key=lambda i: (-final[i], self.corpus[i].chunk_id))[:top_k]
        if references:
            # Reserve one result for every requested provision before filling by relevance.
            leaders = []
            for group in groups:
                available = [i for i in group if i in final]
                if available:
                    best = min(available, key=lambda i: (-final[i], self.corpus[i].chunk_id))
                    if best not in leaders:
                        leaders.append(best)
            ranked = (
                leaders
                + [
                    i
                    for i in sorted(final, key=lambda i: (-final[i], self.corpus[i].chunk_id))
                    if i not in leaders
                ]
            )[:top_k]
        return tuple(
            AramaSonucu(
                parca=self.corpus[i],
                skor=final[i],
                yontem=method,
                istek_eslesme_sayisi=len(eligible) if references else None,
                istek_kirpildi=bool(references and len(eligible) > len(ranked)),
            )
            for i in ranked
        )

    def citation_for(self, chunk_id: str, quote: str | None = None) -> KaynakAtfi:
        source = self.by_id[chunk_id]
        citation = KaynakAtfi(
            chunk_id=source.chunk_id,
            belge_id=source.belge_id,
            madde=source.madde,
            dogrudan_alinti=source.metin if quote is None else quote,
            kaynak_url=source.kaynak_url,
            kaynak_turu=source.kaynak_turu,
            belge_basligi=source.belge_basligi,
            baglam=source.baglam,
            kaynak_sayfalari=source.kaynak_sayfalari,
        )
        if not self.verify_citation(citation):
            raise ValueError("Alıntı kaynak pasajında bulunmuyor")
        return citation

    def verify_citation(self, citation: KaynakAtfi, *, allowed_ids: set[str] | None = None) -> bool:
        source = self.by_id.get(citation.chunk_id)
        return bool(
            source
            and (allowed_ids is None or source.chunk_id in allowed_ids)
            and citation.belge_id == source.belge_id
            and citation.madde == source.madde
            and citation.kaynak_url == source.kaynak_url
            and citation.kaynak_turu == source.kaynak_turu
            and citation.belge_basligi == source.belge_basligi
            and citation.baglam == source.baglam
            and citation.kaynak_sayfalari == source.kaynak_sayfalari
            and citation.dogrudan_alinti in source.metin
        )

    def close(self):
        if self._qdrant is not None:
            self._qdrant.close()
            self._qdrant = None


def mevzuat_ara(sorgu: str, top_k: int = 3) -> tuple[AramaSonucu, ...]:
    return MevzuatRetriever().search(sorgu, top_k)
