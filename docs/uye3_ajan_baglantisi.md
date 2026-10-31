# Üye 3 — Ajan ve insan onayı bağlantısı

## Güncel ortak düzeltme — 1 Kasım 2026 / 0.3.1

UI kanıtı artık yalnız bir kez hazırlar; ajan aynı paketi run_packet ile kullanır.
Başvuru tarihi pakete dahil edilir. Rapor/onay aynı başvuru özetine bağlanır;
metin veya tarih değişirse eski taslak onaylanamaz. Süre/skor kimlikten dışlanır.
Kaynak sahipliği doğrulaması korunur. Aşağıdaki 31 Ekim ölçümleri tarihsel kayıttır;
çift hazırlama açıklaması o eski sürümün davranışıdır. Yeni kanıt ve komutlar
[1 Kasım geliştirme kaydındadır](gelistirme_kaydi_2026-11-01.md).

31 Ekim 2026. Temel: develop / 860b55a (PR #5 sonrası).

## Çalışan üç yol
- Yerel kanıt (varsayılan): yalnız Üye 1 araçları ve BM25; ağ isteği yok.
- Ağsız ajan demosu: Üye 2 ButceliAjan ve LLMClient gerçek kodları çalışır;
  HTTP yanıtı MockTransport ile taklit edilir. Sabit uzman yönlendirmesi ve sabit
  token sayıları test verisidir. API anahtarı ve gerçek model kullanmaz.
- Gerçek model: sunucunun .env/ortam ayarları okunur. Sentetik veri ve API kullanım
  onayları, anahtar, model ve tarihli tarife gerekir. Onay/tarife yoksa istemci açılmaz.
  Bu geliştirmede gerçek sağlayıcı çağrısı yapılmadı.

## İnsan akışı
Öneri, gerekçe, eksik bilgiler ve doğrulanmış kaynaklar gösterilir. Kaynak okuma
kutusu ve 10–1500 karakter gerekçe gerekir. Öneriyi onayla veya gerekçeyle değiştir
seçilir. Değişiklik de Üye 2 karar şeması ve kanıt doğrulayıcısından geçer:
fatura sınırı, ret tutarı, uzman incelemesi/eksik bilgi ve kaynak kısıtları korunur.
Eksik bilgi beyanları insan değişikliğiyle sessizce silinmez.

Kayıt paket özeti, taslak özeti ve istek kimliğine bağlıdır. Yeni başvuru, başarısız
inceleme veya mod değişikliği eski taslak/onay/raporu temizler. Rapor yalnız kayıt
sonrası indirilir; ham başvuru, model gerekçesi ve insan serbest metni aktarılmaz.
Bu özetler kriptografik imza veya kalıcı/değiştirilemez denetim kaydı değildir.
Kimlik ve sipariş sahipliği doğrulaması yoktur; gerçek müşteri için hazır değildir.

## Dosyalar
- app.py: çalışma biçimi, onaylar ve durum temizleme.
- src/ui_service.py: yerel/demo/gerçek bağlantı; ekranda gösterilen kanıtla taslak yeniden doğrulanır.
- src/ui_agent_panel.py: durma nedeni, maliyet rezervasyonu ve insan formu.
- src/agent_review.py: gerekçeli değişiklik, bağlama ve veri azaltılmış rapor.
- tests/test_ui_agent_integration.py: 14 yeni otomatik vaka.
- .streamlit/config.toml: okunabilir açık tema; CSS tema değişkenlerini korur.

## Maliyet ve süre
Ajanın model deneme sayısı, araç sayısı, süre ve tarife hesabı gösterilir.
Demo sayıları gerçek token/fatura ölçümü değildir. Gerçek modda değerler yapılandırılan
tarifeden hesaplanır; rezervasyon varsa ekranda açıklanır. Ayrı UI kanıt hazırlama
süresi ajanın süresine dahil değildir. Bu bağlantı UI paketini ve ajanın kendi paketini
ayrı hazırlar, dolayısıyla yerel bileşenler iki kez çalışabilir. Sonuç kaynakları tekrar
kontrol edilir. Çok kullanıcılı yük, gerçek sağlayıcı ücretleri ve performans ölçülmedi.

## Doğrulama
Python 3.11.0 / Windows: 304 test geçti (5.83 saniye); 30/30 bileşen eval,
20 kaynak beklentili vakada 20/20 hit@3. Kod, biçim ve sır taraması geçti.
Tarayıcıda demo seçimi, öneri gösterimi, gerekçeli onay ve rapor butonu kontrol edildi.
Görsel kontrolde koyu temayla açık arka planın yazıyı okunmaz yaptığı görüldü;
arka plan ve yazılar tema değişkenlerine bağlandı, açık tema yapılandırması eklendi.
Demo ekranı gerçek model karar doğruluğu kanıtı değildir.

## Kalan işler
Gerçek iki sağlayıcı denemesi, insan kalibrasyonu, gerçek yetkilendirme,
kalıcı denetim kaydı/saklama politikası, ekipler arası red team, gerçek maliyet,
yayın ve 2 dakikalık video. Ekli PDF'deki başarı/maliyet örnekleri kopyalanmadı.
