# İadePusula kullanım senaryosu

Üye 3 katkısı, 31 Ekim 2026. Hedef kullanıcı: iade başvurularını ön inceleyen müşteri temsilcisi.
Problem: sipariş, süre ve kaynakları ayrı yerlerde incelemek zaman alır.

## Kullanıcı akışı
1. Sentetik sipariş numarası, başvuru tarihi ve kişisel bilgi içermeyen açıklama girilir.
2. Üye 1 bileşeni siparişi, takvim hesabını, parasal sınırı ve kaynakları getirir.
3. Ekran hesapları, uyarıları, hükmün bağlamını, PDF sayfalarını ve işlem sürelerini gösterir.
4. İnsan kaynakları okuduğunu belirtir; ek bilgi, uzmana yönlendirme veya ön inceleme tamamlama seçer ve gerekçe yazar.
5. Geçerli değerlendirmeden sonra serbest metin içermeyen JSON özeti indirilir.
6. Yeni başvuru veya başarısız yeni değerlendirme eski onayı temizler.

## Kabul koşulları
Boş metin, bilinmeyen sipariş ve engellenen girdi eski sonuç göstermemeli.
Sipariş/kaynak bulunmadan insan değerlendirmesi kaydedilememeli.
Onaysız veya başka başvuruya ait kayıtla rapor üretilememeli.
Hesaplar kabul/ret kararı olarak sunulmamalı. Kaynak skoru güven yüzdesi değildir.

## Sınırlar ve veri
Mevcut sürüm yerel BM25 kullanır; UI yolunda model API çağrısı yoktur.
Üye 2 ajanı henüz repoda bulunmadığından karar önerisi entegrasyonu bekler.
Gerçek kişi/sipariş kullanılmaz. İsim ve adres için maskeleme garantisi yoktur.
Kimlik doğrulama ve gerçek sipariş sahipliği kontrolü yoktur; internete gerçek veriyle açılmaz.
İnceleme yalnız oturum belleğindedir; kalıcı denetim sistemi değildir.
