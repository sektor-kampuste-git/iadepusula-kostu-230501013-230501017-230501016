# Üye 3 doğrulama kaydı

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
