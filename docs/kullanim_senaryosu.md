# İadePusula kullanım senaryosu

Üye 3 katkısı, ortak güncelleme 1 Kasım 2026 / 0.3.1.
Hedef kullanıcı: iade başvurularını ön inceleyen müşteri temsilcisi/uzman.
Problem: sipariş, süre ve kaynakları ayrı yerlerde incelemek zaman alır.

## Kullanıcı akışı
1. Sentetik sipariş numarası, başvuru tarihi ve kişisel bilgi içermeyen açıklama girilir.
2. Üye 1 bileşeni siparişi, takvim hesabını, parasal sınırı ve kaynakları getirir.
3. Ekran hesapları, uyarıları, hükmün bağlamını, PDF sayfalarını ve işlem sürelerini gösterir.
4. İnsan kaynakları okuduğunu belirtir; ek bilgi, uzmana yönlendirme veya ön inceleme tamamlama seçer ve gerekçe yazar.
5. Geçerli değerlendirmeden sonra serbest metin içermeyen JSON özeti indirilir.
6. Yeni başvuru veya başarısız yeni değerlendirme eski onayı temizler.
7. Ajan seçilmişse aynı kanıt paketi model yoluna verilir; başvuru tarihi/metni
   değişirse eski taslak kullanılamaz. İnsan öneriyi değiştirse de şema ve kaynak
   kontrolünden geçer. Kaynaklar okundu ve gerekçe girildi beyanı gerekir.

## Kabul koşulları
Boş metin, bilinmeyen sipariş ve engellenen girdi eski sonuç göstermemeli.
Sipariş/kaynak bulunmadan insan değerlendirmesi kaydedilememeli.
Onaysız veya başka başvuruya ait kayıtla rapor üretilememeli.
Hesaplar kabul/ret kararı olarak sunulmamalı. Kaynak skoru güven yüzdesi değildir.

## Sınırlar ve veri
Varsayılan mod yerel BM25 kullanır. Ağsız demo model taklididir; gerçek model modu ayrı onay ve yapılandırma ister.
Üye 2 ajanı ekrana bağlandı; doğrulanmış öneri için insan onayı ve gerekçeli değişiklik vardır. Gerçek sağlayıcı denemesi yapılmadı.
Gerçek kişi/sipariş kullanılmaz. İsim ve adres için maskeleme garantisi yoktur.
Kimlik doğrulama ve gerçek sipariş sahipliği kontrolü yoktur; internete gerçek veriyle açılmaz.
İnceleme yalnız oturum belleğindedir; kalıcı denetim sistemi değildir.
