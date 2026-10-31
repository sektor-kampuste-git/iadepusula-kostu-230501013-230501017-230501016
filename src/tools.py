"""Salt okunur sipariş sorgusu, takvim günü hesabı ve yıllık parasal sınır.

Bu araçlar bir hukuki kabul/ret kararı üretmez. Para hesapları Decimal kullanır.
"""

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

import holidays
from pydantic import Field, HttpUrl

from src.contracts import CaymaSonucu, Contract, ParasalSinirSonucu, Siparis
from src.paths import DATA


def parse_date(value: date | str) -> date:
    if isinstance(value, datetime):
        raise ValueError("Saat değil YYYY-MM-DD biçiminde takvim tarihi kullanın")
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Tarih YYYY-MM-DD biçiminde olmalıdır")
    return date.fromisoformat(value)


def _money(value: Decimal | str | int) -> Decimal:
    if isinstance(value, (float, bool)):
        raise ValueError("Tutarı kuruş duyarlılığıyla metin veya Decimal olarak verin")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Geçersiz TL tutarı") from exc
    if (
        not result.is_finite()
        or result <= 0
        or result.as_tuple().exponent < -2
        or result > Decimal("9999999999.99")
    ):
        raise ValueError("Tutar pozitif, sonlu ve en fazla iki ondalıklı olmalıdır")
    return result.quantize(Decimal("0.01"))


class SiparisDeposu:
    """Only synthetic public fixtures. Production authorization belongs in the service layer."""

    def __init__(self, path: Path | str = DATA / "siparisler_sentetik.json"):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = [Siparis.model_validate(row) for row in raw]
        self._rows = {row.siparis_no: row for row in rows}
        if len(self._rows) != len(rows):
            raise ValueError("Tekrarlanan sipariş numarası")

    def getir(self, siparis_no: str) -> Siparis | None:
        if not isinstance(siparis_no, str) or not re.fullmatch(r"SIP-2026-\d{4}", siparis_no):
            raise ValueError("Sipariş numarası SIP-2026-0001 biçiminde olmalıdır")
        return self._rows.get(siparis_no)


def siparis_detay_getir(siparis_no: str, *, depo: SiparisDeposu | None = None) -> Siparis | None:
    return (depo or SiparisDeposu()).getir(siparis_no)


@lru_cache(maxsize=16)
def _holiday_calendar(year: int):
    return holidays.country_holidays("TR", years=[year, min(year + 1, 9999)])


def _calendar_warning(deadline: date) -> tuple[date | None, str | None]:
    calendar = _holiday_calendar(deadline.year)
    if deadline.weekday() < 5 and deadline not in calendar:
        return None, None
    next_day = deadline
    while next_day.weekday() >= 5 or next_day in calendar:
        try:
            next_day += timedelta(days=1)
        except OverflowError:
            raise ValueError("Tatil sonrası tarih desteklenen takvim aralığını aşıyor") from None
    return next_day, (
        "Takvim son günü hafta sonu veya resmî tatile rastlıyor. Tatil uzaması hukuki "
        "uygulanabilirliği uzman tarafından incelenmelidir; süre iş günü olarak sayılmadı."
    )


def cayma_suresi_hesapla(
    teslim_tarihi: date | str | None,
    basvuru_tarihi: date | str,
    *,
    cayma_bilgilendirildi: bool | None = True,
    bilgilendirme_tarihi: date | str | None = None,
    diger_teslim_tarihleri: tuple[date | str, ...] = (),
) -> CaymaSonucu:
    """14 calendar days, delivery day is day 0; day 14 is included.

    A single order delivered in parts uses its last delivery (MSY 9/3-a,b).
    Missing notice or a holiday extension ambiguity never produces a final rejection.
    Default notice=True is an explicit calculation assumption; pass actual evidence.
    """
    basvuru = parse_date(basvuru_tarihi)
    teslim = parse_date(teslim_tarihi) if teslim_tarihi is not None else None
    if diger_teslim_tarihleri:
        if teslim is None:
            raise ValueError("Parçalı teslim için ana teslim tarihi de gereklidir")
        teslim = max(teslim, *(parse_date(day) for day in diger_teslim_tarihleri))
    bilgi = parse_date(bilgilendirme_tarihi) if bilgilendirme_tarihi is not None else None
    if bilgi and bilgi > basvuru:
        raise ValueError("Başvuru tarihinden sonraki bilgilendirme kullanılamaz")
    if teslim is None or basvuru < teslim:
        return CaymaSonucu(
            durum="TESLIM_ONCESI",
            basvuru_tarihi=basvuru,
            teslim_tarihi=teslim,
            gecen_gun=None,
            son_gun=None,
            kalan_gun=None,
            aciklama="Teslimden önce de cayma bildirimi yapılabilir. İstisnalar ayrıca incelenir.",
        )
    try:
        ordinary = teslim + timedelta(days=14)
    except OverflowError:
        raise ValueError("14 günlük hesap desteklenen takvim aralığını aşıyor") from None
    deadline = ordinary
    refs = ("MSY-M9",)
    if bilgi and bilgi > teslim:
        # Late notice involves the one-year longstop; preserve facts for legal review.
        try:
            deadline = bilgi + timedelta(days=14)
        except OverflowError:
            raise ValueError("Bilgilendirme hesabı desteklenen takvim aralığını aşıyor") from None
        refs = ("MSY-M9", "MSY-M10")
    next_workday, warning = _calendar_warning(deadline)
    status = "SURE_ICINDE" if basvuru <= deadline else "SURE_GECTI"
    note = "14 takvim günü hesaplandı. Bu sonuç cayma istisnalarını veya ayıplı mal haklarını belirlemez."
    if cayma_bilgilendirildi is not True or (bilgi and bilgi > teslim):
        status = "EK_BILGI_GEREKLI"
        refs = ("MSY-M9", "MSY-M10")
        note = (
            "Cayma bilgilendirmesi eksik, belirsiz veya sonradan yapılmış. MSY Madde 10'daki "
            "bir yıllık üst süre ve yeni bilgilendirme kanıtı uzman tarafından incelenmelidir. "
            f"Olağan 14 günlük takvim bitişi {ordinary.isoformat()}; hukuki son gün belirlenmedi."
        )
        # Do not publish an operative deadline from incomplete notice evidence.
        deadline = None
        next_workday, warning = None, None
    elif next_workday and deadline < basvuru <= next_workday:
        status = "EK_BILGI_GEREKLI"
        note = "Başvuru tatil uzaması aralığında; otomatik süre aşımı sonucu verilmedi."
    return CaymaSonucu(
        durum=status,
        basvuru_tarihi=basvuru,
        teslim_tarihi=teslim,
        gecen_gun=(basvuru - teslim).days,
        son_gun=deadline,
        kalan_gun=max(0, (deadline - basvuru).days) if deadline else None,
        tatil_sonrasi_ilk_is_gunu=next_workday,
        tatil_uyarisi=warning,
        aciklama=note,
        kaynak_maddeler=refs,
    )


class ParasalSinirKaydi(Contract):
    sinir_tl: str = Field(pattern=r"^\d+\.\d{2}$", strict=True)
    sinir_dahil: bool
    kaynak_url: HttpUrl
    dogrulama_url: HttpUrl
    madde: str
    erisim_tarihi: date


def parasal_sinir_kontrol(
    tutar_tl: Decimal | str | int,
    yil: int,
    *,
    kaynak: Path | str = DATA / "parasal_sinirlar.json",
) -> ParasalSinirSonucu:
    """Use the application year; exact equality is outside the strict 'below' threshold."""
    amount = _money(tutar_tl)
    if isinstance(yil, bool) or not isinstance(yil, int) or not 1900 <= yil <= 2200:
        raise ValueError("Geçersiz başvuru yılı")
    values = json.loads(Path(kaynak).read_text(encoding="utf-8"))
    record = values.get(str(yil))
    if not record:
        return ParasalSinirSonucu(
            durum="YIL_DESTEKLENMIYOR",
            tutar_tl=amount,
            yil=yil,
            aciklama="Bu yılın resmî parasal sınırı derlemde yok; önceki yıl kullanılmadı.",
        )
    record = ParasalSinirKaydi.model_validate(record)
    if record.sinir_dahil:
        raise ValueError("Parasal sınır kaydı yalnız hariç üst sınır destekler")
    limit = _money(record.sinir_tl)
    return ParasalSinirSonucu(
        durum="HEYET_SINIRI_ICINDE" if amount < limit else "HEYET_SINIRI_DISINDA",
        tutar_tl=amount,
        yil=yil,
        sinir_tl=limit,
        kaynak_url=str(record.kaynak_url),
        aciklama=f"{yil} için uyuşmazlık değeri {limit} TL'nin altında olmalıdır. Bu bir iade hakkı kararı değildir.",
    )
