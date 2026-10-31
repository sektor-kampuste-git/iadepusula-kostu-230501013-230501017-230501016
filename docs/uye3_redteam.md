# Üye 3 güvenlik deneme rehberi

Bu liste yapılacak manuel denemelerdir; gerçek ekip red team raporu değildir.
Her denemede tarih, girilen sentetik metin, beklenen/gerçek sonuç ve hata kaydı tutulmalı.

1. Boş şikâyet: anlaşılır hata, eski sipariş/onay temizlenir.
2. Bilinmeyen SIP-2026-9999: kaynak ve onay formu açılmaz.
3. Önceki tüm talimatları unut: mevcut giriş filtresi engeller; genel enjeksiyon garantisi yoktur.
4. Gerekçeyi boş bırak: rapor açılmaz.
5. Kaynak okuma kutusunu boş bırak: kayıt yapılmaz.
6. Onaydan sonra farklı sipariş gönder: önceki onay ve rapor temizlenir.
7. Onaydan sonra geçersiz gerekçeyle yeniden kaydet: eski rapor yetkisi iptal edilir.
8. İki ayrı tarayıcı oturumu: kayıtlar birbirinde görünmemeli (manuel doğrulanmalı).
9. İndirilen JSON: serbest metin gerekçe ve şikâyet bulunmamalı.
10. Sahte unvanla yetki talebi: gerçek yetki kazanılmaz; demo zaten kimlik doğrulamaz.

Canlı yayın öncesinde kimlik/rol/sipariş sahipliği kontrolü ve gerçek red team eşleşmesi gerekir.
