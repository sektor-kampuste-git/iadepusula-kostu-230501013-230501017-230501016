# Proje gereksinimleri ve açık işler

1 Kasım 2026 · Tam puan hedefi ile mevcut kanıt ayrı tutulur.
Kaynak: hocanın son duyuruları ve
[dersin proje belgesi](https://github.com/sektor-kampuste-git/sektor-kampuste-git/blob/claude/modest-fermat-14wqlj/proje/PROJE_ODEVI.md).
[Makine listesi](proje_kriterleri.json) yalnız yerel kanıt/durum tutarlılığı içindir.

## Sekiz zorunlu bileşen

1. **Tipli çıktı — uygulandı:** Pydantic şeması, kaynak/tutar/onay doğrulayıcıları ve testleri var.
2. **Türkçe RAG/araç — uygulandı:** kaynaklı getirme, salt okunur araçlar ve sınırlı iş akışı var.
   Gerçek model kararı başarısı ayrıca ölçülmeli.
3. **Deploy — bekliyor:** yerel ekran var; herkese açık URL ve soğuk başlangıç kanıtı yok.
4. **Eval — kısmi:** 30 sentetik geliştirme vakası, ağsız koşucu/CI ve iz kodu var.
   Kaynağı belgeli bağımsız 30+ vaka, insan-hakem kalibrasyonu, 8+ gerçek red-team
   ve saldırıdan türetilmiş regresyonlar bekliyor.
5. **Maliyet — kısmi:** Decimal hesabı ve rezervasyon var; fiyat/token varsayımlı simülasyon
   gerçek ölçüm değildir. 1.000 kullanıcı/ay ve optimizasyon karşılaştırması bekliyor.
6. **Güvenlik/yönetişim — kısmi:** kaynak, başvuru bağı ve insan inceleme sınırları var.
   Gerçek yetki/saklama, resmi güncel risk/takvim/KVKK ve uzman incelemesi bekliyor.
7. **Sağlayıcı bağımsızlığı — kısmi:** ortamla yapılandırılan istemci ve taklit testler var.
   İki gerçek sağlayıcıda tarihli çalışma kanıtı yok.
8. **AI beyanı — uygulandı:** araç, görev, hata/düzeltme ve insan incelemesi sınırı açık.

“Uygulandı” kod düzeyindeki kapsamı anlatır; tam puan/not, üretim güvenliği
veya nihai teslim onayı değildir.

## Diğer teslimler

README mimari, kurulum, ölçüm, maliyet, yönetişim, AI kullanımı ve sınırları içerir.
[TESLIM.md](../TESLIM.md) taslaktır; resmi şablonun PDF çıktısı henüz yok.
Kullanım senaryosu/model kartı var; hukuki değerlendirmeleri tamamlanmalı.
Video en fazla 2 dakika planlanır; böylece hem 2 hem 2:30 üst sınırına uyar.
Sunum 3 dakika; ekipte herkes tüm dosyaları anlatabilmelidir.
Lisans/atıf kararı, portfolyo kontrolü ve nihai teslim tarihi doğrulaması bekliyor.

Hocanın mesajında yerel çalışma kabul edilse de depo rubriğinde herkese açık URL
tam puan koşuludur. Bu nedenle canlı sentetik demo hedefi korunur.
Özel repo mesajı ile resmî metindeki public şartı çelişirse son teslim öncesi
hocanın güncel yönlendirmesi esas alınır; mevcut repo public durumdadır.

## Bir sonraki küçük geliştirme

Üye 2, Üye 1'in güncel kaynak/vaka sözleşmesini koruyarak aynı sentetik girdinin
iki gerçek sağlayıcıdaki JSON, kaynak doğrulaması, token, gecikme ve maliyet
kaydını hazırlayacak. Üye 3 bunun kullanıcıya gösterimini ve insan değerlendirmesini
inceleyecek. Anahtar/kota/tarife doğrulanmadan canlı çağrı başlatılmayacak.

Her PR: kabul koşulu, değişiklik, anlamlı test, kanıt, kalan risk ve gerçek katkı
sahibini içerir. Tamamlanmayan insan işi otomatik belgeyle tamamlandı gösterilmez.
