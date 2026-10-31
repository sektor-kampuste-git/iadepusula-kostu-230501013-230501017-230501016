# Üye 3 arayüz ve entegrasyon

## Kurulum
Proje kökünde PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Örnek sipariş SIP-2026-1002, tarih 2026-10-31. API anahtarı gerekmez.
Test: `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`, ardından
`.venv\Scripts\python.exe -m pytest -q`.

## Sahiplik
`app.py`: giriş, sonuç sekmeleri, kaynak görüntüleme, insan formu ve indirme.
`src/human_review.py`: paket özeti, doğrulama ve veri azaltılmış rapor.
`tests/test_ui.py`, `tests/test_human_review.py`: gerçek kanıt paketiyle UI ve durum geçişleri.
Üye 1 çekirdeği değiştirilmedi. Yerelde bulunan ilk ekran korunan bir kopyadan genişletildi.

## Üye 2 bağlanırken
Üye 2 kodu ortak daldan alındı. docs/uye2_entegrasyon.md içindeki ButceliAjan.run ve
RunReport sözleşmesine göre adapter eklenmeli. Mevcut ekran ajanı henüz çağırmaz. Ajan sonucu doğrulanmadan kabul/ret butonu açılmamalı. Karar, kaynaklar,
bütçe durumu ve uyarılar birlikte aynı paket özetine bağlanmalı. Yeni başvuruda önceki
karar/onay/rapor silinmeli. API çağrıları yalnız sunucuda, ortam değişkenleriyle yapılmalı.
Üye 2 güvenlik kontrolü UI atlanarak da test edilmeli.

## Oturum ve kayıt
Değerlendirme yalnız mevcut tarayıcı oturumunda, yeni kayıtta değiştirilerek tutulur.
JSON özeti onay sonrası indirilebilir; ham şikâyet/gerekçe içermez. Girdi formundaki ham
metin tarayıcıda kalabilir. Kalıcı, çok kullanıcılı DB, kimlik/rol/sipariş sahipliği kontrolü,
değiştirilemez denetim kaydı ve model kararı entegrasyonu tamamlanmamıştır.
