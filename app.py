"""Üye 3: yerel kanıt paketini gösteren Streamlit başlangıç ekranı."""

from datetime import date

import streamlit as st

from src.evidence import hazirla_inceleme
from src.human_review import kaydet_inceleme, rapor_json

st.set_page_config(page_title="İadePusula | Başvuru inceleme", page_icon="🧭", layout="wide")

st.markdown(
    """<style>
.stApp {background: #f5f7fa;}
[data-testid="stSidebar"] {background: #e9eff4;}
[data-testid="stMetric"] {background:white; padding:18px; border-radius:12px;
border:1px solid #dce4eb;}
.stButton > button {border-radius:8px;}
</style>""",
    unsafe_allow_html=True,
)
st.title("İadePusula")
st.caption("İade ve ayıplı mal başvuruları için kaynaklı ön inceleme")
st.info(
    "Geliştirme demosu · Yalnızca örnek siparişler ve kişisel bilgi içermeyen metinler kullanın. "
    "Bu ekran yerel arama yapar; yapay zekâ sağlayıcısına veri göndermez."
)

with st.sidebar:
    st.header("İnceleme adımları")
    st.write("1. Örnek başvuruyu girin.")
    st.write("2. Siparişi, süre hesabını ve kaynakları inceleyin.")
    st.write("3. Eksik bilgileri belirleyin.")
    st.divider()
    st.caption(
        "Bu sürüm karar önerisi üretmez. Kaynak incelemesi ve insan değerlendirmesi "
        "sentetik demo olarak kaydedilir. Para iadesi veya tebligat yapılmaz."
    )

with st.form("basvuru"):
    st.subheader("Başvuru bilgileri")
    left, right = st.columns(2)
    order_id = left.text_input("Sipariş numarası", value="SIP-2026-1002", max_chars=30)
    application_date = right.date_input(
        "Başvuru tarihi", value=date(2026, 10, 31), format="DD/MM/YYYY"
    )
    complaint = st.text_area(
        "Şikâyet açıklaması",
        value="Kulaklık bozuk, ayıplı mal nedeniyle iade istiyorum.",
        max_chars=4000,
        height=130,
        help="Ürünü ve yaşanan sorunu açıklayın. İsim, adres, TCKN veya IBAN yazmayın.",
    )
    submitted = st.form_submit_button("Başvuruyu incele", type="primary")

if submitted:
    # Yeni istek başarısızsa önceki başvurunun sonucu ekranda kalmamalı.
    st.session_state.pop("inceleme", None)
    st.session_state.pop("insan_kaydi", None)
    st.session_state["kaynak_okundu"] = False
    st.session_state["inceleme_gerekcesi"] = ""
    if len(complaint.strip()) < 3:
        st.error("Lütfen en az 3 karakterlik bir şikâyet açıklaması yazın.")
    else:
        try:
            with st.spinner("Sipariş bilgileri ve ilgili kaynaklar hazırlanıyor…"):
                st.session_state.inceleme = hazirla_inceleme(
                    order_id.strip(), complaint.strip(), application_date
                )
        except ValueError:
            st.error(
                "Başvuru incelenemedi. Sipariş numarasını, açıklamayı ve tarihi kontrol edin. "
                "Başvuru tarihi sipariş tarihinden önce olamaz."
            )
        except Exception:
            # İç hata, yerel dosya yolu veya yapılandırma kullanıcıya sızdırılmaz.
            st.error("İnceleme şu anda tamamlanamadı. Lütfen daha sonra tekrar deneyin.")

package = st.session_state.get("inceleme")
if package is not None:
    st.divider()
    st.subheader("İnceleme dosyası")
    st.caption(
        "Aşağıdaki sonuç son gönderilen başvuruya aittir. Değişiklikten sonra yeniden inceleyin."
    )

    warnings = {
        "GIRDI_ENGELLENDI": "Girdi güvenlik kontrolünde engellendi. Başvuruyu sade biçimde yazın.",
        "KAPSAM_DISI": "Bu başvuru iade ve ayıplı mal kapsamı dışında görünüyor.",
        "SIPARIS_BULUNAMADI": "Bu numarayla örnek sipariş bulunamadı. Numarayı kontrol edin.",
        "MAGAZA_SATISI_MESAFELI_CAYMA_UYGULANMAZ": "Mağaza satışı: mesafeli satış cayma hesabı uygulanmadı.",
        "AYIP_IDDIASI_CAYMA_SURESINDEN_BAGIMSIZ_INCELENMELI": "Ayıplı mal iddiası, cayma süresinden ayrı değerlendirilmelidir.",
        "ACILMIS_AMBALAJ_TEK_BASINA_HIJYEN_ISTISNASI_DEGILDIR": "Ambalajın açılmış olması tek başına hijyen istisnası anlamına gelmez.",
        "SURE_ICIN_EK_KANIT_GEREKLI": "Süre değerlendirmesi için ek bilgi veya kanıt gerekiyor.",
        "DERLEMDE_KANIT_BULUNAMADI": "Derlemde uygun kaynak bulunamadı. Uzman incelemesi gerekiyor.",
    }
    for warning in package.uyarilar:
        st.warning(warnings.get(warning, "Ek uzman incelemesi gerektiren bir durum bulundu."))

    if package.siparis:
        order = package.siparis
        a, b, c = st.columns(3)
        a.metric("Ürün", order.urun_adi)
        b.metric("Fatura tutarı", f"{order.fatura_tutari_tl:.2f} TL")
        c.metric("Teslim tarihi", str(order.teslim_tarihi or "Henüz teslim edilmedi"))
        st.caption(f"İncelenen sipariş: {order.siparis_no} · Sentetik kayıt")

        facts, sources, traces = st.tabs(["Hesaplamalar", "Dayanak kaynaklar", "İşlem adımları"])
        with facts:
            st.write("**Cayma süresi**")
            if package.cayma:
                st.write(package.cayma.aciklama)
                if package.cayma.gecen_gun is not None:
                    st.write(f"Teslimden itibaren geçen takvim günü: {package.cayma.gecen_gun}")
                if package.cayma.tatil_uyarisi:
                    st.warning(package.cayma.tatil_uyarisi)
            else:
                st.write("Bu sipariş için cayma süresi hesaplanmadı.")
            if package.parasal_sinir:
                st.write("**Başvuru tutarı kontrolü**")
                st.write(package.parasal_sinir.aciklama)
            st.info("Süre ve tutar hesapları tek başına kabul veya ret kararı değildir.")

        with sources:
            if not package.kaynaklar:
                st.write("Gösterilecek kaynak bulunamadı.")
            for result in package.kaynaklar:
                source = result.parca
                with st.expander(f"{source.belge_basligi} · {source.madde}"):
                    st.text(source.metin)
                    if source.baglam:
                        st.write("**Hükmün bağlamı**")
                        st.text(source.baglam)
                    st.caption(f"Kaynak türü: {source.kaynak_turu} · Parça: {source.chunk_id}")
                    if source.kaynak_sayfalari:
                        st.caption("PDF sayfaları: " + ", ".join(map(str, source.kaynak_sayfalari)))
                    if source.kaynak_url.startswith("https://"):
                        st.link_button("Kaynak belgeyi aç", source.kaynak_url)
                    st.caption(f"Derleme erişim tarihi: {source.erisim_tarihi}")
            st.caption(
                "Arama sıralaması güven yüzdesi değildir; kaynakların uzman denetimi gerekir."
            )

        with traces:
            for trace in package.arac_izleri:
                st.text(f"{trace.arac} · {trace.durum} · {trace.sure_ms:.1f} ms")

    st.caption("İnsan incelemesi gereklidir. Bu demo kesin hukuki karar vermez.")

    if package.siparis and package.kaynaklar:
        st.divider()
        st.subheader("İnsan değerlendirmesi")
        st.caption(
            "Demo kaydıdır; yetkili kimliği doğrulanmaz. Kaynakları inceleyerek iş akışını deneyin. "
            "Ajan kararı henüz bağlı olmadığı için kabul/ret onayı verilmez."
        )
        labels = {
            "Ek bilgi istensin": "EK_BILGI_ISTENDI",
            "Uzman incelemesine yönlendirilsin": "UZMANA_YONLENDIRILDI",
            "Ön inceleme tamamlandı": "ON_INCELEME_TAMAMLANDI",
        }
        with st.form("insan_inceleme"):
            selected = st.selectbox("İnceleme sonucu", list(labels))
            reason = st.text_area(
                "Değerlendirme gerekçesi",
                key="inceleme_gerekcesi",
                max_chars=1500,
                help="En az 10 karakter. Kişisel bilgi yazmayın.",
            )
            read = st.checkbox("Kaynakları ve uyarıları inceledim", key="kaynak_okundu")
            save = st.form_submit_button("Değerlendirmeyi kaydet")
        if save:
            # Geçersiz değişiklik eski onayla rapor indirmeye izin vermemeli.
            st.session_state.pop("insan_kaydi", None)
            try:
                st.session_state.insan_kaydi = kaydet_inceleme(
                    package, labels[selected], reason, read
                )
            except ValueError as exc:
                st.error(str(exc))
        record = st.session_state.get("insan_kaydi")
        if record:
            st.success(
                "Demo incelemesi kaydedildi. Yeni kayıtta önceki değerlendirme değiştirilir."
            )
            st.write("Kaydedilen sonuç: " + record.sonuc)
            st.text(record.gerekce)
            st.caption("Kayıt zamanı (UTC): " + record.zaman_utc)
            st.download_button(
                "Kişisel veri içermeyen demo özetini indir",
                data=rapor_json(package, record),
                file_name="iadepusula-inceleme.json",
                mime="application/json",
            )
            st.caption(
                "Rapora şikâyet ve serbest metin gerekçesi eklenmez. Kayıt yalnız bu oturumda tutulur; "
                "sayfa oturumu kapanınca kaybolabilir. Kalıcı ve değiştirilemez denetim kaydı değildir."
            )
