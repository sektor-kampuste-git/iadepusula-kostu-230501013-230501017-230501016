# Üye 3 — Paketi kullanma ve GitHub'a yükleme

Bu klasör tam proje kopyasıdır; .git, .env, API anahtarı ve sanal ortam içermez.
Taban commit cfc3e2cf041485a4cb9159168289d5344f5ec20f. Önce docs/uye3_arayuz.md ile çalıştır.
Kaynakları ve testleri incele; AI yardımıyla hazırlanan kodu açıklayabilmeden teslim etme.

## Önemli dosyalar
app.py ekran; src/human_review.py insan değerlendirmesi; requirements-ui.txt ekran kurulumu;
tests/test_ui.py ve tests/test_human_review.py kontroller; docs/ altında açıklamalar.

## GitHub'da birlikte yapacağımız adımlar
1. Reponun develop dalını aç. develop güncellendiyse önce yeni dosyalarla karşılaştır.
2. Dal menüsünden uye3-arayuz-insan-incelemesi adlı yeni dal oluştur.
3. Bu dalda Add file > Upload files seç.
4. Yalnız UYE3_DOSYA_LISTESI.txt içindeki değişen dosyaları, klasör yollarını koruyarak yükle.
   Tüm projeyi, ZIP dosyasını, .env dosyasını, .venv veya .git klasörünü yükleme.
5. Açıklama: Kaynak inceleme ekranını ve gerekçeli insan değerlendirmesini ekle.
6. Commit changes ile kendi hesabından kaydet.
7. Compare & pull request: hedef develop, kaynak uye3-arayuz-insan-incelemesi.
8. Testler ve ekip incelemesi geçince birleştirme yapılır; otomatik main üzerine yükleme yok.

Dosyaları web sayfasına tek tek taşımak zor gelirse GitHub Desktop ile yerel klasör eşleştirmesini
birlikte yapacağız. Bu paket otomatik GitHub değişikliği yapmaz.

## Kodu anlatma provası
hazirla_inceleme hangi bilgileri getiriyor? Yeni başvuru eski onayı neden siliyor?
Kaynak okuma ve gerekçe neden zorunlu? JSON'dan serbest metin neden çıkarıldı?
Demo onayı gerçek yetkilendirmeden nasıl farklı? Üye 2 ajanı nerede bağlanacak?
