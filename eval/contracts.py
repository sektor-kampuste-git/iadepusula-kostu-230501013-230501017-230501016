from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from src.contracts import Contract, IncelemePaketi, KaynakAtfi


class Expected(Contract):
    cayma_durumu: (
        Literal["SURE_ICINDE", "SURE_GECTI", "TESLIM_ONCESI", "EK_BILGI_GEREKLI"] | None
    ) = None
    parasal_durumu: (
        Literal["HEYET_SINIRI_ICINDE", "HEYET_SINIRI_DISINDA", "YIL_DESTEKLENMIYOR"] | None
    ) = None
    kaynak_any_of: tuple[str, ...] = ()
    uyarilar: tuple[str, ...] = ()
    kaynak_bos: bool = False

    @model_validator(mode="after")
    def meaningful_expectation(self):
        if self.kaynak_bos and self.kaynak_any_of:
            raise ValueError("Kaynak hem boş hem de belirli bir madde olamaz")
        if not (
            self.cayma_durumu
            or self.parasal_durumu
            or self.kaynak_any_of
            or self.uyarilar
            or self.kaynak_bos
        ):
            raise ValueError("En az bir alana özgü değerlendirme beklentisi gereklidir")
        return self


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
        if self.etiket_durumu == "insan_dogruladi" and not (
            self.insan_etiketleyen and self.insan_etiketleyen.strip()
        ):
            raise ValueError("İnsan doğrulaması için etiketleyen kaydı zorunludur")
        return self


class AgentPrediction(Contract):
    """Integration contract for Member 2's predictor(input) function."""

    karar_onerisi: Literal["KABUL_ONERILIR", "RED_ONERILIR", "UZMAN_INCELEMESI_GEREKLI"]
    kaynaklar: tuple[KaynakAtfi, ...]
    insan_onayi_gerekiyor_mu: Literal[True]


class PredictorInput(Contract):
    """Label-free input. Expected evidence and decisions never enter the predictor."""

    id: str
    siparis_no: str
    basvuru: str
    basvuru_tarihi: date
    kanit_paketi: IncelemePaketi
