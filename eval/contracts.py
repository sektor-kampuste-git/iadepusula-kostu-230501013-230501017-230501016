from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from src.contracts import Contract, IncelemePaketi, KaynakAtfi


class Expected(Contract):
    cayma_durumu: str | None = None
    parasal_durumu: str | None = None
    kaynak_any_of: tuple[str, ...] = ()
    uyarilar: tuple[str, ...] = ()
    kaynak_bos: bool = False


class EvalCase(Contract):
    id: str = Field(pattern=r"^V\d{2}$")
    grup: Literal["standart", "sinir", "adversarial"]
    siparis_no: str
    basvuru: str = Field(min_length=3, max_length=4000)
    basvuru_tarihi: date
    beklenen: Expected
    taslak_karar: Literal["KABUL_ONERILIR", "RED_ONERILIR", "UZMAN_INCELEMESI_GEREKLI"]
    etiket_durumu: Literal["ai_taslak", "insan_dogruladi"] = "ai_taslak"
    insan_etiketleyen: str | None = None

    @model_validator(mode="after")
    def human_label_requires_reviewer(self):
        if self.etiket_durumu == "insan_dogruladi" and not self.insan_etiketleyen:
            raise ValueError("İnsan doğrulaması için etiketleyen kaydı zorunludur")
        return self


class AgentPrediction(Contract):
    """Integration contract for Member 2's predictor(case) function."""

    karar_onerisi: Literal["KABUL_ONERILIR", "RED_ONERILIR", "UZMAN_INCELEMESI_GEREKLI"]
    kaynaklar: tuple[KaynakAtfi, ...]
    insan_onayi_gerekiyor_mu: Literal[True]


class EvidenceExpectation(Contract):
    paket: IncelemePaketi
