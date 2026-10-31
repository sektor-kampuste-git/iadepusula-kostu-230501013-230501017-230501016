# Sistem kartı — Üye 3 entegrasyon durumu

Tarih: 31 Ekim 2026. Taban: cfc3e2cf041485a4cb9159168289d5344f5ec20f.

## Çalışan kapsam
Streamlit ekranı, Üye 1 kanıt paketi, yerel mevzuat araması, kaynak bağlamı ve işlem izleri,
insan değerlendirme formu, gerekçeli kayıt değiştirme, onay sonrası veri azaltılmış rapor.
UI otomatik hukuki karar, tebligat veya ödeme yapmaz. Çalışan yol LLM kullanmaz.

## Güvenlik ve insan gözetimi
Kaynak okuma beyanı ve en az 10 karakter gerekçe gerekir. Kaynak ve sipariş yoksa kayıt yoktur.
SHA-256 özeti kaydı belirli pakete bağlar; kriptografik imza veya değiştirilemez günlük değildir.
Serbest metinler JSON raporuna alınmaz. Oturumdaki gerekçeye mevcut maskeleme uygulanır;
maskelenmemiş isim/adres kalabilir. Gerçek kişi verisi girilmemelidir.
Kimliği doğrulanmış yetkili onayı henüz yoktur. Demo kutucuğu kimlik doğrulama değildir.

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
