"""Bounded evidence assembly: three tools and one retrieval, no final decision."""

from datetime import date
from time import perf_counter

from src.contracts import AracIzi, IncelemePaketi
from src.privacy import mask_pii, obvious_injection, retrieval_query
from src.rag import MevzuatRetriever, normalize
from src.tools import SiparisDeposu, cayma_suresi_hesapla, parasal_sinir_kontrol


def hazirla_inceleme(
    siparis_no: str,
    basvuru: str,
    basvuru_tarihi: date,
    *,
    retriever: MevzuatRetriever | None = None,
    depo: SiparisDeposu | None = None,
) -> IncelemePaketi:
    if not isinstance(basvuru, str) or not 3 <= len(basvuru) <= 4000:
        raise ValueError("Başvuru 3–4000 karakter olmalıdır")
    safe = mask_pii(basvuru)
    warnings = []
    logs = []
    norm = normalize(safe)
    blocked = obvious_injection(safe)
    outside = any(
        term in norm for term in ["ise iade", "bosanma", "ceza davasi", "kripto", "maas tablosu"]
    )
    if blocked or outside:
        return IncelemePaketi(
            siparis=None,
            cayma=None,
            parasal_sinir=None,
            kaynaklar=(),
            maskelenmis_basvuru=safe,
            arac_izleri=(AracIzi(arac="girdi_siniri", durum="engellendi", sure_ms=0),),
            uyarilar=("GIRDI_ENGELLENDI" if blocked else "KAPSAM_DISI",),
        )
    depo = depo or SiparisDeposu()
    retriever = retriever or MevzuatRetriever()

    def measured(name, call):
        start = perf_counter()
        value = call()
        logs.append(
            AracIzi(
                arac=name,
                durum="basarili" if value is not None else "bulunamadi",
                sure_ms=round((perf_counter() - start) * 1000, 3),
            )
        )
        return value

    order = measured("siparis_detay_getir", lambda: depo.getir(siparis_no))
    if order is None:
        return IncelemePaketi(
            siparis=None,
            cayma=None,
            parasal_sinir=None,
            kaynaklar=(),
            arac_izleri=tuple(logs),
            maskelenmis_basvuru=safe,
            uyarilar=("SIPARIS_BULUNAMADI",),
        )
    if basvuru_tarihi < order.siparis_tarihi:
        raise ValueError("Başvuru sipariş tarihinden önce olamaz")
    if order.satis_kanali == "magaza":
        withdrawal = None
        warnings.append("MAGAZA_SATISI_MESAFELI_CAYMA_UYGULANMAZ")
    else:
        withdrawal = measured(
            "cayma_suresi_hesapla",
            lambda: cayma_suresi_hesapla(
                order.teslim_tarihi,
                basvuru_tarihi,
                cayma_bilgilendirildi=order.cayma_bilgilendirildi,
                bilgilendirme_tarihi=order.bilgilendirme_tarihi,
            ),
        )
    threshold = measured(
        "parasal_sinir_kontrol",
        lambda: parasal_sinir_kontrol(order.fatura_tutari_tl, basvuru_tarihi.year),
    )
    sources = measured(
        "mevzuat_ara", lambda: retriever.search(retrieval_query(safe), tarih=basvuru_tarihi)
    )
    if any(term in norm for term in ["bozuk", "ariza", "kirik", "calismiyor", "ayip", "bozuldu"]):
        warnings.append("AYIP_IDDIASI_CAYMA_SURESINDEN_BAGIMSIZ_INCELENMELI")
    if order.koruyucu_muhur_acildi and order.hijyen_niteligi is not True:
        warnings.append("ACILMIS_AMBALAJ_TEK_BASINA_HIJYEN_ISTISNASI_DEGILDIR")
    if withdrawal and withdrawal.durum == "EK_BILGI_GEREKLI":
        warnings.append("SURE_ICIN_EK_KANIT_GEREKLI")
    if not sources:
        warnings.append("DERLEMDE_KANIT_BULUNAMADI")
    return IncelemePaketi(
        siparis=order,
        cayma=withdrawal,
        parasal_sinir=threshold,
        kaynaklar=sources,
        arac_izleri=tuple(logs),
        uyarilar=tuple(warnings),
        maskelenmis_basvuru=safe,
    )
