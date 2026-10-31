# Üye 3 doğrulama kaydı

Bu dosya 31 Ekim sürümlerinin tarihsel sonuçlarıdır. Sonraki ajan bağlantısı
[entegrasyon notunda](uye3_ajan_baglantisi.md), güncel ortak sürüm ise
[1 Kasım kaydında](gelistirme_kaydi_2026-11-01.md) açıklanır.
Alttaki "henüz bağlı değil" ifadesi eski sürüme aittir.

31 Ekim 2026, Windows / Python 3.11.0, taban cfc3e2cf041485a4cb9159168289d5344f5ec20f.

- Tam test paketi: **153 geçti, 6.83 saniye**. Bunun 12 testi UI/insan inceleme katkısına aittir.
- Araç ve RAG bileşen eval: **30/30**; kaynak beklenen **20/20 hit@3**.
- Ortalama bileşen süresi: 11.84 ms; LLM gecikmesi veya üretim performansı değildir.
- İnsan hakem kalibrasyonu ve nihai ajan karar doğruluğu: ölçülmedi.
- Kod ve biçim kontrolü: geçti (app.py, src, eval, scripts, tests).

Windows kısıtlı çalıştırmada Streamlit testinin yerel socket oluşturması bekledi;
aynı testler izinli ortamda 153/153 geçti. Gerçek model çağrısı yapılmadı.
Görsel tarayıcı incelemesi ve çok kullanıcılı manuel test yapılmadı; AppTest kullanıcı
akışı, hata, eski onayın silinmesi ve rapor önkoşullarını doğruladı.
GitHub CI bu paket için henüz koşmadı. Canlı yayın ve video yoktur.

Mevcut geliştirme eval seti bağımsız test değildir; etiketler AI taslağıdır.
Bu sayılar bireysel not veya gerçek tüketici uyuşmazlığı çözme başarısı iddiası içermez.


## Üye 2 ile birleştirme kontrolü — 31 Ekim 2026

Üye 3 dalına develop tabanı 62e722b alındı. README ve CI çakışmaları iki üyenin
katkıları korunarak çözüldü. CI hem app.py hem maliyet_hesapla.py kontrolünü,
üye 2 demosunu ve paket doğrulamasını içerir.

- Birleşik test paketi: **290 geçti, 7.24 saniye** (Python 3.11.0, Windows).
- Ruff kod/biçim kontrolü ve gizli bilgi taraması geçti.
- Bileşen eval: **30/30**, kaynak beklentili 20 vakada **20/20 hit@3**.
- Üye 2 ağsız demo: normal, bütçe, adım ve kullanım bilgisi yok senaryoları beklenen şekilde tamamlandı.
- Maliyet komutu çalıştı; fiyat/token girdileri kullanıcı varsayımı, gerçek sağlayıcı ölçümü değildir.
- UI hâlâ kanıt paketini kullanır; mevcut karar ajanı henüz ekrana bağlı değildir.
- GitHub kontrol sonuçları ayrıca takip edilmelidir; yerel test CI sonucu değildir.
