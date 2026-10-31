# İadePusula — TESLIM

**Ara geliştirme kaydı; nihai teslim değildir.** 1 Kasım 2026 · sürüm 0.3.1.
Kocaeli Sağlık ve Teknoloji Üniversitesi · Takım Şarjör.

## 1. Takım ve sorumluluk

- Emre Berk Güç / 230501013 / Üye 1: derlem, RAG, araçlar, eval.
  Kanıt: src/evidence.py, src/rag.py, src/tools.py, eval/evaller.json ve commit geçmişi.
- Zeynep Zehra Kocatürk / 230501017 / Üye 2: istemci, şema, ajan,
  güvenlik/maliyet, CI ve ortak başvuru bağı.
  Kanıt: src/agent.py, src/schemas.py, src/case_binding.py,
  tests/test_case_binding.py, docs/gelistirme_kaydi_2026-11-01.md.
- Beste Tuana Çuhadar / 230501016 / Üye 3: arayüz, insan incelemesi,
  UI bağlantısı ve yönetişim/sunum hazırlığı.
  Kanıt: app.py, src/ui_service.py, src/agent_review.py ve docs/uye3_ajan_baglantisi.md.

Sorumluluk alanı tamamlanma beyanı değildir. Herkes tüm dosyaları anlatabilmelidir.
Commit/PR ve insan incelemesi üzerinden bireysel katkı doğrulanır.

## 2. Problem ve çözüm

Türkçe e-ticaret başvurusu için sipariş, süre ve kaynakları uzman önüne toplar.
Model varsa kanıtla doğrulanan taslak önerir. İnsan kaynakları okuyup gerekçe verir.
Kesin hukuki karar, ödeme ve bildirim uygulamaz. Yalnız sentetik veri prototipidir.
[Kullanım senaryosu](docs/kullanim_senaryosu.md).

## 3. Bağlantılar ve kurulum

[Repo](https://github.com/sektor-kampuste-git/iadepusula-kostu-230501013-230501017-230501016).
Canlı URL: henüz yok. Video: henüz yok.
Kurulum/yerel demo: [README](README.md). Mimari: [docs/mimari.md](docs/mimari.md).
5 dakikalık temiz kurulum ölçümü yapılmadı.

## 4. Zorunlu bileşenler ve kanıt

- Tipli çıktı/3+ doğrulayıcı: src/schemas.py ve tests/test_schemas.py.
- Türkçe RAG/izinli araçlar: src/rag.py, src/evidence.py, src/mcp_server.py.
- Sınırlı ajan: src/agent.py; dört araç, en fazla iki model denemesi; USD/süre/adım.
- Deploy: yerel app.py var; sıfır maliyetli public URL kanıtı bekliyor.
- Eval/iz/CI: eval/eval_kosucu.py, src/tracing.py, .github/workflows/ci.yml.
  30 sentetik geliştirme vakası var; gerçek insan kalibrasyonu/dış red team yok.
- Maliyet: maliyet_hesapla.py varsayım hesabı; gerçek kullanım/optimizasyon bekliyor.
- Güvenlik/yönetişim: src/security.py, docs/model_karti.md; resmi sınıf/takvim
  ve KVKK doğrulaması bekliyor.
- İki sağlayıcı: .env.example ve genel istemci var; iki gerçek çalışma kanıtı yok.
- AI beyanı: README AI kullanımı bölümü ve tarihli geliştirme kaydı.

Durumlar [gereksinim kanıt listesinde](docs/proje_kriterleri.json) izlenir.

## 5. Eval ve maliyet sonuçları

31 Ekim bileşen geliştirme eval'i 30/30; kaynak beklenen 20 vakada hit@3 20/20.
Etiket AI taslağıdır; insan onaylı altın standart veya nihai ajan doğruluğu değildir.
1 Kasım test/komut kayıtları [geliştirme kaydında](docs/gelistirme_kaydi_2026-11-01.md).

Simülasyon: 2100 girdi/450 çıktı, 1M için 1/2 USD varsayımıyla 0.003 USD/istek;
1000 kullanıcı × 10 istek = 30 USD/ay. Gerçek sağlayıcı fiyatı/faturası değildir.

## 6. Güvenlik, yönetişim ve AI kullanımı

Anahtarlar ortamda, kaynak/tutar/başvuru doğrulaması ve gerekçeli insan incelemesi var.
Gerçek RBAC, sipariş sahipliği ve kalıcı audit yoktur. İsim/adres maskeleme garantisi yok.
EU AI Act/KVKK uygunluğu veya üretim güvenliği iddiası kurulmaz.
[Model kartı](docs/model_karti.md) sınırları açıklar.

Codex araştırma, kod, test ve belge taslaklarında kullanıldı. Ekip insan incelemesi
ayrıca gereklidir. Gerçek hata/düzeltmeler README ve tarihli kayıtlarda açıklanır.

## 7. Sınırlar, kalanlar ve son kontrol

- [ ] İki gerçek sağlayıcı, kullanım ve fiyat kaynağı.
- [ ] 30+ bağımsız/kökeni belgeli vaka; 5+ zorlayıcı; insan-hakem kalibrasyonu.
- [ ] 8+ gerçek red-team saldırısı, başarısız saldırının eval regresyonu.
- [ ] Ölçülmüş maliyet/optimizasyon; gerçek yük ve soğuk başlangıç.
- [ ] Yetki/saklama/audit ve resmi yönetişim incelemesi.
- [ ] Public sentetik URL, <=2 dakika video, 3 dakika sunum.
- [ ] Lisans/atıf kararı ve portfolyo kontrolü >=8/10.
- [ ] Son teslim tarihi/LMS kontrolü; bu dosyanın <=6 sayfalık PDF çıktısı.
- [ ] Her üyenin tüm dosyaları açıklaması ve ekip insan incelemesi.

Nihai PDF/sunum henüz üretilmedi. Dersin resmi şablonu ve güncel duyurularla
son karşılaştırma yapılacak; olmayan kanıt tamamlandı işaretlenmeyecek.
