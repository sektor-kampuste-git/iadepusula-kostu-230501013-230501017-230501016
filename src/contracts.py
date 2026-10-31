"""Üye 1 veri sözleşmeleri; Üye 2'nin nihai karar şemalarından bağımsızdır."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

KaynakTuru = Literal["kanun", "yonetmelik", "resmi_rehber", "teblig", "demo_politika"]
KaynakSayfalari = tuple[Annotated[int, Field(strict=True, ge=1)], ...]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Siparis(Contract):
    siparis_no: str = Field(pattern=r"^SIP-2026-\d{4}$")
    urun_adi: str = Field(min_length=2)
    kategori: str
    siparis_tarihi: date
    teslim_tarihi: date | None
    fatura_tutari_tl: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    satis_kanali: Literal["mesafeli", "magaza"] = "mesafeli"
    cayma_bilgilendirildi: bool | None = True
    bilgilendirme_tarihi: date | None = None
    koruyucu_muhur_acildi: bool | None = None
    hijyen_niteligi: bool | None = None
    kisisellestirilmis: bool = False
    cabuk_bozulabilir: bool = False
    dijital_ifa_onayi: bool | None = None
    kargo_hasar_tutanagi: bool = False
    sentetik: Literal[True] = True

    @model_validator(mode="after")
    def tarih_sirasi(self):
        if self.teslim_tarihi and self.teslim_tarihi < self.siparis_tarihi:
            raise ValueError("Teslim tarihi siparişten önce olamaz")
        if self.bilgilendirme_tarihi and self.bilgilendirme_tarihi < self.siparis_tarihi:
            raise ValueError("Bilgilendirme tarihi siparişten önce olamaz")
        return self


class CaymaSonucu(Contract):
    durum: Literal["SURE_ICINDE", "SURE_GECTI", "TESLIM_ONCESI", "EK_BILGI_GEREKLI"]
    basvuru_tarihi: date
    teslim_tarihi: date | None
    gecen_gun: int | None
    son_gun: date | None
    kalan_gun: int | None
    tatil_sonrasi_ilk_is_gunu: date | None = None
    tatil_uyarisi: str | None = None
    aciklama: str
    kaynak_maddeler: tuple[str, ...] = ("MSY-M9",)
    insan_incelemesi_gerekli: Literal[True] = True


class ParasalSinirSonucu(Contract):
    durum: Literal["HEYET_SINIRI_ICINDE", "HEYET_SINIRI_DISINDA", "YIL_DESTEKLENMIYOR"]
    tutar_tl: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    yil: int
    sinir_tl: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    sinir_dahil: Literal[False] = False
    kaynak_url: str | None = None
    aciklama: str


class KaynakParcasi(Contract):
    chunk_id: str
    belge_id: str
    kaynak_turu: KaynakTuru
    belge_basligi: str
    madde: str
    baslik: str
    metin: str = Field(min_length=15)
    kaynak_url: str
    erisim_tarihi: date
    gecerli_baslangic: date
    gecerli_bitis: date | None = None
    anahtar_kelimeler: tuple[str, ...] = ()
    kaynak_sha256: str
    baglam: str | None = None
    kaynak_sayfalari: KaynakSayfalari = ()

    @model_validator(mode="after")
    def gecerlilik_sirasi(self):
        if self.gecerli_bitis and self.gecerli_bitis < self.gecerli_baslangic:
            raise ValueError("Derlem geçerlilik bitişi başlangıçtan önce olamaz")
        return self


class AramaSonucu(Contract):
    parca: KaynakParcasi
    skor: float
    yontem: Literal["bm25", "hybrid_rrf"]
    istek_eslesme_sayisi: int | None = Field(default=None, ge=0)
    istek_kirpildi: bool = False


class KaynakAtfi(Contract):
    chunk_id: str
    belge_id: str
    madde: str
    dogrudan_alinti: str = Field(min_length=15, max_length=2500)
    kaynak_url: str
    kaynak_turu: KaynakTuru
    belge_basligi: str
    baglam: str | None = None
    kaynak_sayfalari: KaynakSayfalari = ()


class AracIzi(Contract):
    arac: str
    durum: Literal["basarili", "bulunamadi", "engellendi"]
    sure_ms: float = Field(ge=0)


class IncelemePaketi(Contract):
    basvuru_tarihi: date | None = None
    siparis: Siparis | None
    cayma: CaymaSonucu | None
    parasal_sinir: ParasalSinirSonucu | None
    kaynaklar: tuple[AramaSonucu, ...]
    arac_izleri: tuple[AracIzi, ...]
    uyarilar: tuple[str, ...]
    maskelenmis_basvuru: str
    insan_onayi_gerekiyor_mu: Literal[True] = True
    # Deliberately no final decision or refund execution field.
