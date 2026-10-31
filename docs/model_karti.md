# İadePusula sistem/model kartı

Güncelleme: 1 Kasım 2026, sürüm 0.3.1. Taban: develop bedc0179.
Üye 3'ün kartı ortak başvuru bağıyla güncellendi. Bu belge model sağlayıcısının
eğitim model kartının yerine geçmez; uygulama sistem kartıdır.

## Model ve veri

Model seçimi LLM_BASE_URL / LLM_API_KEY / LLM_MODEL ortam alanlarından yapılır.
Varsayılan yerel kanıt modunda model yoktur; ağsız demoda yanıt/token taklittir.
Gerçek sağlayıcı/model sürümü ve kullanım ölçümleri henüz bu sürüm için raporlanmadı.
100 sipariş sentetik, 40 pasaj resmi kaynaklardan seçilmiştir; tam konsolide
mevzuat değildir. Eğitim/fine-tuning yapılmadı. 30 eval etiketi AI taslağıdır.

## Çalışan kapsam
Streamlit ekranı, Üye 1 kanıt paketi, yerel mevzuat araması, kaynak bağlamı ve işlem izleri,
insan değerlendirme formu, gerekçeli kayıt değiştirme, onay sonrası veri azaltılmış rapor.
UI otomatik hukuki karar, tebligat veya ödeme yapmaz. Varsayılan yol LLM kullanmaz. Gerçek model modu ancak açık onay ve sunucu yapılandırmasıyla çağrı yapar; geliştirmede gerçek API denenmedi.

## Güvenlik ve insan gözetimi
Kaynak okuma beyanı ve en az 10 karakter gerekçe gerekir. Kaynak ve sipariş yoksa kayıt yoktur.
SHA-256 özeti kaydı belirli pakete bağlar; kriptografik imza veya değiştirilemez günlük değildir.
Özet başvuru metni, başvuru tarihi ve kaynakları kapsar. Süre/skor kapsanmaz.
Taslaktan onaya geçerken aynı başvuru kontrol edilir; başka başvurunun taslağı reddedilir.
Serbest metinler JSON raporuna alınmaz. Oturumdaki gerekçeye mevcut maskeleme uygulanır;
maskelenmemiş isim/adres kalabilir. Gerçek kişi verisi girilmemelidir.
Üye 2 ajanı ekrana bağlıdır; ağsız demo ve gerçek model yolları ayrıdır. Kimliği doğrulanmış yetkili onayı henüz yoktur. Demo kutucuğu kimlik doğrulama değildir.

## Hukuk ve yönetişim
Hukuki ön inceleme kullanımından dolayı uzman gözetimi gerekir. EU AI Act risk sınıfı,
uygulama takvimi ve KVKK hukuki uygunluğu bu geliştirmede doğrulanmadı; hukuk uzmanı
ve güncel resmi kaynak kontrolü olmadan uyum iddiası kurulmaz.

## Ölçüm
UI/human review testleri otomatik ve ağsızdır. Gerçek insan kalibrasyonu, nihai karar
doğruluğu, canlı kullanım gecikmesi ve model USD maliyeti bu katkıda ölçülmedi.
Model bağlanmadan sıfır toplam maliyet veya yüzde başarı iddiası yoktur.

## AI kullanımı
Kod, test ve belge taslakları Codex yardımıyla oluşturuldu. Üye 3 kendi bilgisayarında
çalıştırmalı, kodu incelemeli ve anlamadığı bölümleri açıklatmalıdır. Bu dosyalar tek başına
kullanıcının bağımsız geliştirdiğine veya not başarısına kanıt değildir.
