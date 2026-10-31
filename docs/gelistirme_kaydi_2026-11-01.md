# Üye 2 — Ortak başvuru bağı ve belge tutarlılığı

Tarih: 1 Kasım 2026. Geliştirici hesabı: Zeynep Zehra Kocatürk (Üye 2).
Codex yardımıyla kod/test/belge hazırlandı; ekip insan incelemesi ayrıca gereklidir.
Taban develop: bedc0179e41f6603530cdd052a69f4c2f5a8fd78.
Emre'nin RAG/araçları ve Beste'nin UI/insan incelemesi korunarak ilerlenir.

## Sorun ve tekrar üretim

İlk iki yeni regresyon testi düzeltmeden önce başarısız oldu:

- UI ve ajan aynı kanıtı iki kez hazırlıyordu; sayaç 1 yerine 2 gördü.
- Aynı sipariş/kaynakta metni değiştirilen paketle eski taslak onaylanabildi;
  beklenen ValueError oluşmadı.

Bu testler tests/test_case_binding.py içinde korunur.
Başvuru tarihi artık kanıt paketine eklenir; tarih yoksa model yolu durur.
UI, hazır paketi run_packet ile ajana verir. Rapor aynı paket özetini taşır;
onay ve indirme öncesi bağ yeniden denetlenir.
Süre/skor kimlikten ayrılır; başvuru/tarih/kaynak değişikliği özeti bozar.

## Doğrulama

Windows / Python 3.12.14 üzerinde entegrasyon düzeltmesi sonrası **316 test geçti**
(13.91 saniye). Bu, belge kontrol testleri eklenmeden önceki gerçek koşumdur.
Son tüm-sürüm doğrulaması tamamlandığında aşağıya ayrı kayıt eklenir;
eski sayı yeni test sonucu olarak yeniden kullanılmaz.

Ruff src/tests kod ve biçim kontrolü geçti. Gerçek API çağrısı yapılmadı.
Model HTTP yanıtları taklit edildi; test tarife/token verileri gerçek maliyet değildir.
Yeni 12 vaka; başvuru/tarih/uyarı değişimi, eksik/geçersiz özet, tek paket,
skor/süre kararlılığı, retriever yaşam süresi ve eksik tarih sınırlarını kapsar.

## Ortak belge geliştirmesi

README tek ürün akışına dönüştürüldü. SPEC, klasör rehberleri, ekip/kod anlatma
rehberi, gereksinim-kanıt listesi ve ağsız belge denetimi eklendi.
Eski tarihli üye kanıtları tarihsel kayıttır; özgün katkı silinmedi.
Bu çalışma gerçek sağlayıcı, insan kalibrasyonu, deploy veya video yerine geçmez.

## Öğrenme ve sınır

Zeynep; neden aynı siparişin yeterli kimlik olmadığını, SHA-256'ın neden imza
olmadığını ve bilinen fiyatla hesaplanan kullanımın faturadan farkını açıklamalıdır.
Otomatik başarı insan kod incelemesi veya bireysel not garantisi değildir.

## Son ortak doğrulama — 1 Kasım 2026

- Tam paket: **321 test geçti / 6.79 saniye**, Windows / Python 3.12.14.
- Ruff kod ve biçim: geçti, 61 Python dosyası.
- Sır taraması: geçti; değerler yazdırılmadı.
- Belge denetimi: yerel bağlantılar ve C1–C8 kanıt yolları geçti.
- Bileşen eval: **30/30**, kaynak beklenen **20/20 hit@3**, 6 adversarial vaka;
  insan kalibrasyonu yok, gerçek ajan kararı ölçülmedi.
- Ağsız ajan demosu: normal, bütçe, adım ve eksik kullanım senaryoları beklenen
  durma nedenini verdi. Model yanıtı/token kullanımı taklittir.
- Maliyet simülasyonu: 0.003 USD/istek ve 1000 × 10 için 30 USD/ay;
  bunlar varsayım, güncel sağlayıcı fiyatı değildir.
- 0.3.1 wheel oluşturuldu ve depo dışından CLI/veri/eval/Üye 2 modülleri doğrulandı.

Komutlar README ağsız doğrulama bölümündedir. Wheel kontrolü:
`python -m pip wheel . --no-deps --wheel-dir artifacts/wheels` ve
`python scripts/verify_package.py artifacts/wheels`.
Yerel ortamda paketleme altyapısı yüklü olmadığından ilk yalıtımsız deneme başarısızdı;
standart izole derleme ile geçti. Bu uygulama testi hatası değildi.

Koşum UTC tarihi 31 Ekim 22:41, İstanbul tarihi 1 Kasım'dır; tarih alanları bu nedenle
bir gün farklı görünebilir. Ham değerlendirmede UTC bilgisi korunur.
GitHub CI sonucu bu yerel sonuçlardan ayrıdır; PR kontrollerinde görülebilir.
