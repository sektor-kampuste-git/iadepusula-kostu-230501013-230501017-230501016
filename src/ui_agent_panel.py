"""Üye 3: ajan taslağı, durma nedeni ve insan incelemesi ekranı."""

import streamlit as st

from src.agent_review import kaydet_taslak_incelemesi, taslak_raporu

ONERILER = {
    "KABUL_ONERILIR": "Kabul önerisi",
    "RED_ONERILIR": "Ret önerisi",
    "UZMAN_INCELEMESI_GEREKLI": "Uzman incelemesi gerekli",
}
NEDENLER = {
    "GIRDI_HATASI": "Başvuru bilgilerini kontrol edin.",
    "GIRDI_ENGELLENDI": "Girdi güvenlik kontrolünde engellendi.",
    "SIPARIS_BULUNAMADI": "Örnek sipariş bulunamadı.",
    "KAYNAK_YOK": "Yeterli kaynak bulunamadı; uzman incelemesi gerekir.",
    "SENTETIK_ONAY_GEREKLI": "Sentetik veri onayı gerekiyor.",
    "ADIM_SINIRI": "İşlem adım sınırında durdu; otomatik karar verilmedi.",
    "BUTCE_SINIRI": "İstek bütçesi nedeniyle duruldu; otomatik karar verilmedi.",
    "SURE_SINIRI": "Yanıt süresi sınırına ulaşıldı.",
    "TARIFE_YOK": "Model tarifesi tanımlı değil.",
    "SAGLAYICI_HATASI": "Model servisi yanıtı tamamlanamadı.",
    "KULLANIM_BILINMIYOR": "Kullanım bilgisi doğrulanamadı; ayrılan bütçe korunuyor.",
    "GECERSIZ_TASLAK": "Model taslağı doğrulamayı geçmedi; uzman incelemesi gerekir.",
}


def goster_ajan_paneli(paket, rapor, *, mod):
    st.subheader("Ön inceleme önerisi")
    if mod == "demo":
        st.warning(
            "Ağsız demo: model yanıtı ve token sayıları taklittir. "
            "Her zaman uzman incelemesi önerir; hukuki doğruluk testi değildir."
        )
    st.caption(
        f"Model denemesi: {rapor.model_calls} · Ajan araç çağrısı: {rapor.tool_calls} · "
        f"Ajan süresi: {rapor.elapsed_ms:.1f} ms"
    )
    st.caption(
        f"{'Demo tarife hesabı' if mod == 'demo' else 'Yapılandırılan tarife hesabı'}: "
        f"{rapor.accounted_usd} USD · "
        f"{'Rezervasyon içerir' if rapor.cost_contains_reservation else 'Raporlanan kullanım üzerinden'}"
    )
    st.caption(
        "Bu tutar sağlayıcı faturası değildir. Ekrandaki ayrı kanıt hazırlama süresini içermez."
    )
    if rapor.reason != "TASLAK_DOGRULANDI" or rapor.draft is None:
        st.warning(NEDENLER.get(rapor.reason, "Öneri hazırlanamadı; uzman incelemesi gerekir."))
        st.session_state.pop("taslak_insan_kaydi", None)
        return
    draft = rapor.draft
    st.write("**" + ONERILER[draft.karar_onerisi] + "**")
    st.text(draft.sorgu_ozeti)
    st.text(draft.gerekce)
    if draft.hesaplanan_iade_tutari_tl is not None:
        st.write(f"Önerilen tutar: {draft.hesaplanan_iade_tutari_tl:.2f} TL")
    for missing in draft.eksik_bilgiler:
        st.warning("Eksik bilgi: " + missing)
    with st.expander("Önerinin doğrulanmış kaynakları"):
        for source in draft.kaynaklar:
            st.write(source.belge_basligi + " · " + source.madde)
            st.text(source.dogrudan_alinti)
            if source.baglam:
                st.text(source.baglam)
    st.caption(
        "İnsan değerlendirmesi yalnız sentetik demo kaydıdır. Yetkili kimliği doğrulanmaz; "
        "ödeme veya tebligat yapılmaz. Eksik bilgi varsa kabul/ret değişikliği engellenir."
    )
    with st.form("taslak_onay"):
        action = st.selectbox(
            "İnsan işlemi", ["Öneriyi onayla", "Gerekçeyle değiştir"], key="taslak_eylem"
        )
        final = st.selectbox(
            "Değişiklik için yeni öneri",
            list(ONERILER),
            index=list(ONERILER).index(draft.karar_onerisi),
            format_func=ONERILER.get,
            key="taslak_yeni_oneri",
        )
        amount = st.text_input(
            "Değişiklik için tutar (TL)",
            key="taslak_yeni_tutar",
            help="Kabul/ret için 125.50 gibi yazın. Uzman incelemesinde boş bırakın.",
        )
        reason = st.text_area("İnsan değerlendirme gerekçesi", max_chars=1500, key="taslak_gerekce")
        read = st.checkbox("Öneriyi, kaynakları ve uyarıları inceledim", key="taslak_okundu")
        save = st.form_submit_button("İnsan değerlendirmesini kaydet")
    if save:
        st.session_state.pop("taslak_insan_kaydi", None)
        try:
            st.session_state.taslak_insan_kaydi = kaydet_taslak_incelemesi(
                paket,
                rapor,
                eylem="ONAYLA" if action == "Öneriyi onayla" else "DEGISTIR",
                gerekce=reason,
                kaynaklar_okundu=read,
                yeni_oneri=final,
                yeni_tutar=amount.strip() or None,
            )
        except ValueError:
            st.error(
                "Kaydedilemedi. Kaynakları okuduğunuzu belirtin; 10–1500 karakter gerekçe yazın. "
                "Tutar fatura bedelini aşamaz, ret için pozitif olamaz; uzman incelemesinde boş olmalı. "
                "Eksik bilgili taslak kabul/ret olarak değiştirilemez."
            )
    record = st.session_state.get("taslak_insan_kaydi")
    if record:
        st.success("İnsan değerlendirmesi bu başvuru ve taslağa bağlı olarak kaydedildi.")
        st.write("Kaydedilen öneri: " + ONERILER[record.son_oneri])
        st.text(record.gerekce)
        st.download_button(
            "Onay sonrası demo özetini indir",
            taslak_raporu(paket, rapor, record, mod=mod),
            file_name="iadepusula-taslak-inceleme.json",
            mime="application/json",
        )
        st.caption(
            "Serbest metin rapora alınmaz. Kayıt yalnız bu oturumdadır; kalıcı denetim kaydı değildir."
        )
