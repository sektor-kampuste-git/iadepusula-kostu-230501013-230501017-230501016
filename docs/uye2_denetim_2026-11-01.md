# Üye 2 kapsam ve depo denetimi

1 Kasım 2026 · sürüm 0.3.2 · Zeynep Zehra Kocatürk.
Taban develop: db139c97239392029fa1a334229974a575204838.
Kod, klasör, test/CI, README ve ortak arayüzler okundu. Codex yardımı ve iki
salt okunur inceleme kullanıldı; bunlar insan ekip incelemesi yerine geçmez.

## Genel değerlendirme

Proje; UI, RAG/araçlar, şema/istemci/ajan ve eval katmanları ayrılmış bir
geliştirme prototipidir. Ağsız testler, içeriksiz izler, Decimal maliyet ve CI vardır.
Tek dosyalı/dağınık bir uygulama değildir. Son ürün/üretim hazır olduğu veya
bütün rubrik koşullarının tamamlandığı iddia edilmez.

Ana README ürün, kullanım, kurulum, mimari, ölçüm, maliyet, ekip, AI beyanı ve
sınırları içerir. Klasör rehberleri teknik ayrıntıları taşır. Vitrin sorunu metin
güncellenmemesi değil, GitHub'ın .github/README.md dosyasını önce seçmesiydi.
[GitHub'ın resmi README seçme sırası](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
ile bu davranış doğrulandı; canlı API ve HTML de otomasyon belgesini seçiyordu.
Depo About alanına ürün açıklaması ve mevcut kapsamı anlatan konu etiketleri eklendi;
canlı demo veya lisans alanına olmayan bir değer yazılmadı.

## Üye 2 kapsamında düzeltmeler

1. .github/README.md, OTOMASYON.md olarak yeniden adlandırıldı. İşlev/içerik
   korundu; referanslar ve belge denetimi düzeltildi. Ana vitrin gölgelenmesini
   yakalayan regresyon kontrolü eklendi. Önceki kontrol yalnız kök dosyanın
   değiştiğini doğruladığından ana sayfa seçimini kaçırmıştı.
2. run_packet dış boşlukları güvenli biçimde kabul eder. Başvuru özeti değiştirilmez;
   ham kişisel veri ve görünmez Unicode dönüşümü hâlâ reddedilir. İki boşluk/satır
   testi önce GIRDI_HATASI ile başarısız oldu, sonra geçti. Mevcut app.py zaten strip
   uyguluyordu; bu sorun entegrasyon çağıranları içindi.
3. Tarife/sağlayıcı/bütçe/kullanım belirsizliği eval'de artık geçerli uzman önerisi
   sayılamaz. Dört regresyon önce başarısızdı. Eksik tarihli iç kanıt paketinin
   uzman önerisine dönüşmesi de ayrı başarısız testle gösterilip engellendi.
   Üye 1'in koşucusu değiştirilmeden
   güvenli AgentEvaluationError üzerinden ajan aşaması hatası kaydedilir.
4. Eksik src.agent:predict_for_eval girişi eklendi. Ayrı işletim ortamı onayı
   olmadan yapılandırma/anahtar okunmaz; ağsız testte istemci enjekte edilir.
5. Eski Üye 2 katkı kaydı tarihsel olarak işaretlendi. Ana vitrin/depo denetiminin
   Üye 2 sahipliği ve diğer üyelerin koduna müdahale etmeme kuralı kalıcılaştırıldı.

## Korunan ekip sınırı

app.py, Üye 3'ün UI/human-review modülleri; Üye 1'in RAG, araç, derlem ve
eval koşucusu/veri etiketleri değiştirilmedi. Üye 2 yalnız kendi ajan adaptörünü,
testlerini, CI/belge denetimini ve kendi dokümantasyonunu geliştirdi.

## Ekip arkadaşlarına bırakılan notlar

Bu notlar atama veya yapılmış katkı değildir; içerik sahipleriyle görüşülmelidir.

- Beste: kökteki BASLA_UYE3.md ve UYE3_*DOSYA*.txt eski yükleme paketinden kalıyor.
  İçerik silinmeden tarihsel arşive taşınması kökü sadeleştirebilir.
- Beste: app.py yerel mod açıklamasındaki “ajan henüz bağlı değil” ifadesi diğer
  modlarla çelişiyor; “yerel kanıt modunda öneri üretilmiyor” biçimi daha doğru olur.
- Emre: docs/gelistirme_plani.md tarihsel entegrasyon beklentilerini taşıyor.
  Güncel ortak planla bağlantısı netleştirilebilir.
- Ortak: lisans ve üçüncü taraf atıfları ekipçe kararlaştırılmalı.
- Paket geliştirme için desteklenen yol requirements-dev.txt'dir; .[dev]
  ekinin daha dar olması şu an belgelenmiş kurulum akışını bozmuyor.
- Üye 2 sonraki güvenlik işi: sır taraması bilinen örüntüler ve yerel anahtar
  eşleşmesine dayanır; tüm sağlayıcı anahtarları/.env varyantları için kapsamlı
  sızıntı garantisi değildir. Yeni sağlayıcı bağlantısıyla kapsamı genişletilmeli.

## Yerel doğrulama

Python 3.12.14 / Windows: **333 test geçti, 7.31 saniye**. Belge kontrolü, Ruff
kod/biçim ve sır taraması geçti. Aynı geliştirme setiyle bileşen eval ve ağsız
demo ayrıca koşulur; bunlar gerçek model doğruluğu veya insan onayı değildir.
Eksik tarihli paket regresyonu düzeltmeden önce "beklenen istisna oluşmadı"
sonucuyla başarısızdı; hata sınıfı artık koşucuya iletilir.

## Doğrulama ve kalanlar

[Ham kontrol özeti](kanitlar/2026-11-01_uye2_denetim.json) gerçek yerel koşuma aittir.
GitHub'ın seçtiği README yolu API ile ayrıca doğrulanır; dosya içeriği tek başına
vitrin doğrulaması sayılmaz. Model yanıtları testte taklittir, gerçek API çağrısı yoktur.

Üye 2 için sonraki küçük iş: iki sağlayıcıda aynı sentetik girdi, kaynak doğrulaması,
token/gecikme ve tarihli maliyet. Sonra önbellek/kademe/çıktı sınırı karşılaştırması.
İnsan kalibrasyonu, dış red-team, güvenli deploy, yönetişim ve video ekipçe sürer.
Not öğretim elemanına aittir; eksik kanıtlar [kriter listesinde](proje_kriterleri.json)
açık tutulur.
