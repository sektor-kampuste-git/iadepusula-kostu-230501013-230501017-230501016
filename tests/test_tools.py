import json
from datetime import date, datetime
from decimal import Decimal

import pytest

from src.paths import DATA
from src.tools import SiparisDeposu, cayma_suresi_hesapla, parasal_sinir_kontrol


@pytest.mark.parametrize(
    ("application", "days", "expected"),
    [
        ("2026-10-01", 0, "SURE_ICINDE"),
        ("2026-10-14", 13, "SURE_ICINDE"),
        ("2026-10-15", 14, "SURE_ICINDE"),
        ("2026-10-16", 15, "SURE_GECTI"),
    ],
)
def test_calendar_days_inclusive_boundary(application, days, expected):
    value = cayma_suresi_hesapla("2026-10-01", application)
    assert value.durum == expected
    assert value.gecen_gun == days
    assert value.son_gun == date(2026, 10, 15)
    assert value.insan_incelemesi_gerekli


def test_holiday_does_not_become_automatic_rejection():
    value = cayma_suresi_hesapla("2026-10-15", "2026-10-30")
    assert value.son_gun == date(2026, 10, 29)
    assert value.tatil_sonrasi_ilk_is_gunu == date(2026, 10, 30)
    assert value.durum == "EK_BILGI_GEREKLI"
    assert value.gecen_gun == 15


def test_weekend_extension_is_flagged_for_expert():
    value = cayma_suresi_hesapla("2026-10-17", "2026-11-02")
    assert value.durum == "EK_BILGI_GEREKLI"
    assert value.tatil_sonrasi_ilk_is_gunu == date(2026, 11, 2)


def test_partial_delivery_uses_last_item():
    value = cayma_suresi_hesapla("2026-10-01", "2026-10-24", diger_teslim_tarihleri=("2026-10-10",))
    assert value.gecen_gun == 14
    assert value.durum == "SURE_ICINDE"


def test_leap_year_and_year_rollover():
    assert cayma_suresi_hesapla("2024-02-29", "2024-03-14").gecen_gun == 14
    assert cayma_suresi_hesapla("2026-12-25", "2027-01-08").son_gun == date(2027, 1, 8)


@pytest.mark.parametrize("delivery", [None, "2026-11-05"])
def test_withdrawal_before_delivery(delivery):
    value = cayma_suresi_hesapla(delivery, "2026-10-31")
    assert value.durum == "TESLIM_ONCESI"
    assert value.gecen_gun is None


@pytest.mark.parametrize("notice", [False, None])
def test_missing_notice_cannot_be_rejected_on_14_days(notice):
    value = cayma_suresi_hesapla("2026-09-01", "2026-10-31", cayma_bilgilendirildi=notice)
    assert value.durum == "EK_BILGI_GEREKLI"
    assert "MSY-M10" in value.kaynak_maddeler


def test_late_notice_is_not_silently_treated_as_delivery_notice():
    value = cayma_suresi_hesapla("2026-09-01", "2026-10-31", bilgilendirme_tarihi="2026-10-25")
    assert value.durum == "EK_BILGI_GEREKLI"
    assert value.son_gun is None and value.kalan_gun is None
    with pytest.raises(ValueError):
        cayma_suresi_hesapla("2026-10-01", "2026-10-10", bilgilendirme_tarihi="2026-10-11")


@pytest.mark.parametrize("bad", ["31.10.2026", "2026-02-30", "2026-1-01", datetime(2026, 10, 1)])
def test_ambiguous_or_invalid_dates_rejected(bad):
    with pytest.raises(ValueError):
        cayma_suresi_hesapla(bad, "2026-10-31")


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("185999.99", "HEYET_SINIRI_ICINDE"),
        ("186000.00", "HEYET_SINIRI_DISINDA"),
        ("186000.01", "HEYET_SINIRI_DISINDA"),
    ],
)
def test_threshold_is_strict_and_uses_decimal(amount, expected):
    result = parasal_sinir_kontrol(amount, 2026)
    assert result.durum == expected
    assert result.tutar_tl == Decimal(amount)
    assert result.sinir_dahil is False


@pytest.mark.parametrize(
    "bad", ["0", "-1", "NaN", "Infinity", "1.001", "1,50", "1e99999", True, 1.2]
)
def test_bad_money_is_rejected(bad):
    with pytest.raises(ValueError):
        parasal_sinir_kontrol(bad, 2026)


def test_unknown_year_does_not_reuse_previous_limit():
    result = parasal_sinir_kontrol("500", 2027)
    assert result.durum == "YIL_DESTEKLENMIYOR"
    assert result.sinir_tl is None


def test_store_lookup_is_single_order_and_does_not_leak_rows():
    store = SiparisDeposu()
    assert store.getir("SIP-2026-1001").fatura_tutari_tl == Decimal("1200.00")
    assert store.getir("SIP-2026-9999") is None
    with pytest.raises(ValueError):
        store.getir("../evrenkey.txt")


def test_duplicate_or_inconsistent_fixtures_fail_early(tmp_path):
    rows = json.loads((DATA / "siparisler_sentetik.json").read_text(encoding="utf-8"))
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([rows[0], rows[0]]), encoding="utf-8")
    with pytest.raises(ValueError, match="Tekrarlanan"):
        SiparisDeposu(path)
    rows[0]["teslim_tarihi"] = "2020-01-01"
    path.write_text(json.dumps([rows[0]]), encoding="utf-8")
    with pytest.raises(ValueError, match="Teslim"):
        SiparisDeposu(path)


def test_corrupted_limit_source_is_rejected(tmp_path):
    path = tmp_path / "limits.json"
    path.write_text('{"2026":{"sinir_tl":186000.0}}', encoding="utf-8")
    with pytest.raises(ValueError):
        parasal_sinir_kontrol("500", 2026, kaynak=path)
