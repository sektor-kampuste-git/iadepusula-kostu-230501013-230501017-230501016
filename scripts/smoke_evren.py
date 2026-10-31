"""One real embedding batch, one query and one synthetic grounded completion.

Explicitly invoked only. This is a connectivity/evidence smoke test, not a calibrated eval.
No user complaint or credential is saved in the output.
"""

import json
import sys
from typing import Literal

from pydantic import Field

from src.contracts import Contract
from src.evren import EvrenAdapter, ProviderSettings
from src.paths import ROOT
from src.rag import MevzuatRetriever


class Quote(Contract):
    chunk_id: str
    alinti: str = Field(min_length=15)


class EvidenceResponse(Contract):
    kontrol: Literal["KAYNAK_KANITI_URETILDI"]
    kaynaklar: tuple[Quote, ...] = Field(min_length=1, max_length=3)
    insan_onayi_gerekiyor_mu: Literal[True]


def smoke():
    path = ROOT / "artifacts" / "evren_smoke.json"
    path.parent.mkdir(exist_ok=True)
    # Invalidate the previous run before touching the provider.
    path.write_text('{"basarili": false, "durum": "basladi"}\n', encoding="utf-8")
    with EvrenAdapter(ProviderSettings.from_env()) as adapter:
        retriever = MevzuatRetriever(embedder=adapter, cache_dir=ROOT / ".cache" / "embeddings")
        try:
            found = retriever.search(
                "İnternetten alınan gömlekte teslimden 10 gün sonra 14 günlük cayma hakkı"
            )
            response = adapter.synthetic_completion(
                [{"chunk_id": item.parca.chunk_id, "metin": item.parca.metin} for item in found]
            )
            summary = EvidenceResponse.model_validate(response.pop("output"))
            allowed = {item.parca.chunk_id for item in found}
            for quote in summary.kaynaklar:
                source = retriever.by_id.get(quote.chunk_id)
                if not source or not retriever.verify_citation(
                    retriever.citation_for(source.chunk_id, quote.alinti),
                    allowed_ids=allowed,
                ):
                    raise ValueError("Model alıntısı getirilen kaynakla eşleşmiyor")
            # Public report contains token counts only, never account/quota metadata.
            response["usage"] = {
                key: value
                for key, value in response["usage"].items()
                if key in {"prompt_tokens", "completion_tokens", "total_tokens"}
            }
            report = {
                "tur": "sentetik_baglanti_ve_atif_smoke",
                "basarili": True,
                "sinir": "Birebir alıntı seçimi doğrulandı. Hukuki yorum veya karar üretilmedi.",
                "derlem_sha256": retriever.fingerprint,
                "getirilen_kaynaklar": sorted(allowed),
                "kanit": summary.model_dump(mode="json"),
                "derlem_onbellek_durumu": retriever.cache_status,
                "api_istek_sayilari": dict(adapter.request_counts),
                **response,
            }
            path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
        except Exception as exc:
            path.write_text(
                json.dumps({"basarili": False, "hata_turu": type(exc).__name__}) + "\n",
                encoding="utf-8",
            )
            raise
        finally:
            retriever.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    smoke()
