# Üye 2 katkı ve doğrulama kaydı

Hazırlama: 31 Ekim 2026. Üye 2: Zeynep Zehra Kocatürk, 230501017.
Temel: Üye 1 `cfc3e2cf041485a4cb9159168289d5344f5ec20f`.
Durum: yerel paket hazır; GitHub'a yükleme/CI ve ekip kod incelemesi bekliyor.

## Gerçekte yapılanlar

- Codex ile üye 1 kodu, entegrasyon sözleşmesi ve görev dağılımı incelendi.
- İlk paket: şema ve kanıta bağlı doğrulama; 45 yeni test ve API'siz şema demosu.
- Kullanıcı ilk 45 testi ve demoyu kendi PowerShell'inde başarıyla çalıştırdı.
- Sonraki paket: genel HTTP/JSON istemcisi, .env yapılandırması, bütçeli iş akışı,
  girdi minimizasyonu, maskelenmiş izler, maliyet ve aylık senaryo hesapları.
- Testler mevcut CI'a bağlandı; wheel paketine maliyet modülü eklendi.
- 137 üye 2 testi dahil toplam 278 test yerelde Codex tarafından çalıştırıldı ve geçti.
- Kod ve biçim kontrolleri geçti; dört senaryolu ağsız iş akışı demosu çalıştı.
- Bu sayılar gerçek LLM başarısı, gerçek sağlayıcı token ölçümü veya not garantisi değildir.

## Gerçek sorunlar ve düzeltmeler

1. Kullanıcının PowerShell'inde `git` komutu bulunamadı. Python kodu/testleri
   çalışıyordu. Sistem PATH'ini değiştirmek yerine yalnız güncellenmiş kaynak
   dosyalarını içeren GitHub web yükleme paketi hazırlanıyor.
2. Önceki pytest önbelleğinde kullanıcı yazma yetkisi hatası görüldü. Kullanıcı
   `-p no:cacheprovider` ile 45 testi uyarısız çalıştırdı; sistem izinleri gevşetilmedi.
3. İlk zaman sınırı testi gerçek saatin çok küçük bir aralığına bağımlıydı.
   Saat bağımlılığı ajana enjekte edilerek test deterministik hâle getirildi.
4. Retry maliyetinin ve bilinmeyen kullanımın sıfır görünmemesi için önce
   rezervasyon, sonra gerçek kullanım hesabı uygulandı; bunun sağlayıcı tarafı
   katı fatura limiti olmadığı belgelerde açıklandı.

## İnsan incelemesinde açıklanacaklar

- Şema doğrulaması ile isteğe bağlı atıf/fatura kontrolü arasındaki fark.
- İki gerçek sağlayıcı denemesi ile MockTransport testinin neden farklı kanıtlar olduğu.
- Yeniden denemenin hangi adım ve maliyeti tükettiği; kayıp usage'ın neden sıfır olmadığı.
- Bir true bayrağının neden gerçek insan onayı olmadığı.
- Maskelemenin isim/adres sınırı; trace'in neden ham metin saklamadığı.
- Üye 1 kaynaklarının nasıl bağlandığı ve Üye 3'e hangi alanların verileceği.

GitHub commit/PR bağlantıları ve insan incelemesi, gerçekten oluştuğunda
bu kayda ve final `TESLIM.md` sorumluluk tablosuna eklenecek. Bu belgede
henüz gerçekleşmemiş bir insan kod incelemesi veya PR onayı iddia edilmez.

## Bekleyen işler

- En az iki gerçek sağlayıcıda sentetik senaryoyla çalışma kanıtı.
- Tarihli/doğrulanmış gerçek fiyat veya açık varsayım; gerçek token ve gecikme ölçümü.
- Üye 1 ile gerçek ajan eval'i, yeni bağımsız vakalar ve insan/hakem kalibrasyonu.
- Üye 3 ile onay/değiştirme kaydı, arayüz, canlı yayın ve demo videosu.
- Gerçek veri öncesi kapsamlı kişisel veri, yetki, oran sınırı ve güvenlik incelemesi.
- Önbellek/kademe/çıktı limiti maliyet ve kalite karşılaştırmaları.

Nihai değerlendirme öğretmene aittir. Katkı dosya/commit sayısıyla eşitlenmez;
çalışan kod, gerçek test, ekip incelemesi ve sözlü açıklama ile kanıtlanır.
