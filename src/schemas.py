"""Üye 2: model taslağını Üye 1'in güvenilir kanıt paketiyle doğrula.

Bu katman karar üretmez ve ödeme/onay işlemi uygulamaz. PII kontrolü yalnız
``src.privacy`` içindeki örüntüler kapsamındadır; hukukî doğruluk veya KVKK
uyumluluğunun tamamını kanıtlamaz. Uygulama giriş noktası
``dogrula_karar_taslagi`` olmalıdır; şema doğrulaması tek başına yeterli değildir.
"""

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from src.contracts import Contract, IncelemePaketi, KaynakAtfi
from src.privacy import mask_pii, normalize_input
from src.rag import MevzuatRetriever

KararOnerisi = Literal["KABUL_ONERILIR", "RED_ONERILIR", "UZMAN_INCELEMESI_GEREKLI"]


class TaslakDogrulamaHatasi(ValueError):
    """Ham model yanıtını veya kişisel veri değerini içermeyen sınır hatası."""


def _yalin_veri(value: Any) -> Any:
    """model_copy ile atlanan doğrulamaları sınırda tekrar çalıştırabilmek için aç."""
    if isinstance(value, BaseModel):
        return _yalin_veri(value.model_dump(mode="python"))
    if isinstance(value, Mapping):
        return {key: _yalin_veri(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_yalin_veri(item) for item in value]
    return value


def _metinler(value: Any):
    """İç içe kaynaklar dahil çıktıdaki bütün metin değerlerini dolaş."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _metinler(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _metinler(item)


class KararTaslagi(Contract):
    """Kaynaklı ön inceleme önerisi; nihai karar veya insan onayı kaydı değildir."""

    model_config = ConfigDict(hide_input_in_errors=True)

    sorgu_ozeti: str = Field(min_length=10, max_length=1000)
    karar_onerisi: KararOnerisi
    gerekce: str = Field(min_length=20, max_length=4000)
    kaynaklar: tuple[KaynakAtfi, ...] = Field(max_length=10)
    eksik_bilgiler: tuple[str, ...] = Field(default=(), max_length=10)
    hesaplanan_iade_tutari_tl: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    insan_onayi_gerekiyor_mu: Literal[True] = True

    @field_validator("sorgu_ozeti", "gerekce", mode="before")
    @classmethod
    def metin_bos_olamaz(cls, value: Any) -> str:
        """Boşluk ve görünmez karakterden ibaret metinleri kabul etme."""
        if not isinstance(value, str) or not (text := normalize_input(value).strip()):
            raise ValueError("Özet ve gerekçe dolu metin olmalıdır")
        return text

    @field_validator("insan_onayi_gerekiyor_mu", mode="before")
    @classmethod
    def insan_incelemesi_zorunlu(cls, value: Any) -> bool:
        """Modelin false, 1 veya metin değeriyle inceleme kuralını değiştirmesini engelle."""
        if value is not True:
            raise ValueError("İnsan incelemesi zorunludur")
        return True

    @field_validator("hesaplanan_iade_tutari_tl", mode="before")
    @classmethod
    def para_float_olamaz(cls, value: Any) -> Any:
        """Para için Decimal, metin veya tam sayı kullan; float/bool kabul etme."""
        if value is not None and (
            isinstance(value, (bool, float)) or not isinstance(value, (str, int, Decimal))
        ):
            raise ValueError("Tutar Decimal, tam sayı veya ondalık metin olmalıdır")
        return value

    @field_validator("eksik_bilgiler")
    @classmethod
    def eksikler_anlamli_olmali(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Eksik bilgi kalemlerini kısa, dolu ve tekrarsız tut."""
        clean = tuple(normalize_input(item).strip() for item in values)
        if any(not item or len(item) > 300 for item in clean) or len(set(clean)) != len(clean):
            raise ValueError("Eksik bilgi kalemleri kısa, dolu ve benzersiz olmalıdır")
        return clean

    @field_validator("kaynaklar")
    @classmethod
    def kaynak_tekrari_olamaz(cls, values: tuple[KaynakAtfi, ...]) -> tuple[KaynakAtfi, ...]:
        """Tek pasajın tekrarlarıyla kaynak sayısının şişirilmesini engelle."""
        if len({source.chunk_id for source in values}) != len(values):
            raise ValueError("Kaynak parça kimlikleri benzersiz olmalıdır")
        return values

    @model_validator(mode="after")
    def karar_alanlari_tutarli_olmali(self):
        """Kaynak, eksik bilgi, öneri ve tutar arasındaki kuralları uygula."""
        expert = self.karar_onerisi == "UZMAN_INCELEMESI_GEREKLI"
        if not expert and not self.kaynaklar:
            raise ValueError("Kabul/ret önerisi kaynak olmadan sunulamaz")
        if self.eksik_bilgiler and not expert:
            raise ValueError("Eksik bilgi varsa uzman incelemesine yönlendirilmelidir")
        if self.karar_onerisi == "RED_ONERILIR" and self.hesaplanan_iade_tutari_tl not in (
            None,
            Decimal("0"),
        ):
            raise ValueError("Ret önerisinde pozitif iade tutarı bulunamaz")
        if expert and self.hesaplanan_iade_tutari_tl is not None:
            raise ValueError("Uzman incelemesinde tutar belirlenmemiş olmalıdır")
        return self

    @model_validator(mode="after")
    def cikti_pii_icermemeli(self):
        """Özet, gerekçe, eksikler ve kaynak metinlerinde bilinen PII örüntülerini reddet."""
        if any(
            mask_pii(text) != normalize_input(text)
            for text in _metinler(self.model_dump(mode="python"))
        ):
            raise ValueError("Çıktı desteklenen kişisel veri örüntülerinden birini içeriyor")
        return self

    def eval_ciktisi(self) -> dict:
        """Doğrulanmış taslağı mevcut AgentPrediction alanlarına izdüşür.

        Yalnız dogrula_karar_taslagi dönüşünde kullanılır. Bu bir predictor veya
        model değerlendirmesi değildir; eval sözleşmesini değiştirmemeyi sağlar.
        """
        return self.model_dump(
            mode="json",
            include={"karar_onerisi", "kaynaklar", "insan_onayi_gerekiyor_mu"},
        )


def dogrula_karar_taslagi(
    ham: Mapping[str, Any] | KararTaslagi,
    paket: IncelemePaketi,
    *,
    retriever: MevzuatRetriever,
) -> KararTaslagi:
    """Taslağı sunucu tarafında tutulan paket ve aynı derlemle doğrula.

    paket ve retriever model/kullanıcı yanıtından alınmaz; Üye 1 katmanından
    gelir. Kaynaklar yalnız bu istekte getirilen pasajlara dayanabilir. Tutar
    sınırı ilk sürümün fatura bedeliyle sınırlı iade kapsamıdır; genel hukukî
    hak/tazminat üst sınırı iddiası değildir. Gerekçenin anlam doğruluğu ayrıca
    değerlendirilmelidir.
    """
    try:
        draft = KararTaslagi.model_validate(_yalin_veri(ham))
        trusted = IncelemePaketi.model_validate(_yalin_veri(paket))
    except (ValidationError, TypeError, ValueError):
        raise TaslakDogrulamaHatasi(
            "Taslak veya kanıt paketi şema kurallarını karşılamıyor"
        ) from None

    allowed = {row.parca.chunk_id for row in trusted.kaynaklar}
    if any(not retriever.verify_citation(cite, allowed_ids=allowed) for cite in draft.kaynaklar):
        raise TaslakDogrulamaHatasi("Atıf bu istekte getirilen kaynakla eşleşmiyor")

    if trusted.siparis is None or {"GIRDI_ENGELLENDI", "KAPSAM_DISI"}.intersection(
        trusted.uyarilar
    ):
        if draft.karar_onerisi != "UZMAN_INCELEMESI_GEREKLI":
            raise TaslakDogrulamaHatasi(
                "Yetersiz veya engellenmiş kanıtta uzman incelemesi gerekir"
            )

    amount = draft.hesaplanan_iade_tutari_tl
    if amount is not None and (
        trusted.siparis is None or amount > trusted.siparis.fatura_tutari_tl
    ):
        raise TaslakDogrulamaHatasi("Tutar güvenilir siparişin fatura sınırını karşılamıyor")
    return draft
