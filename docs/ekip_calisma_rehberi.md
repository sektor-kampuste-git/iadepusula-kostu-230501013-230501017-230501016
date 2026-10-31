# Ekip çalışma rehberi

Takım Şarjör: Üye 1 Emre Berk Güç, Üye 2 Zeynep Zehra Kocatürk,
Üye 3 Beste Tuana Çuhadar. Sorumluluk ayrımı koordinasyon içindir; her üye tüm
akışı ve rastgele seçilen dosyayı açıklayabilmelidir.

## Tek ortak çalışma

Tek proje deposu, özellik başına dal ve PR kullanılır.
develop entegrasyon, main doğrulanmış sürümdür. Eski yükleme paketini tüm dosyaların
üstüne kopyalamayın. Arkadaşınızın yeni değişikliğini almadan aynı dosyayı ezmeyin.
Force push ve sahte/sonradan üretilmiş katkı geçmişi kullanılmaz.

1. develop güncellenir; açık PR ve sorumluluklar kontrol edilir.
2. SPEC'te küçük kabul koşulu yazılır; ilgili üyeyle sözleşme netleştirilir.
3. Özellik dalında kod, anlamlı test ve belge aynı değişiklikte hazırlanır.
4. README, gereksinim kanıtları ve TESLIM durumu gerçek sonuçla güncellenir.
5. CI, test/eval ve ekip incelemesi sonrası develop'a alınır.
6. main'e aktarım, çalışan ortak sürüm doğrulandıktan sonra yapılır.

## Sıradaki koordinasyon

- Üye 1: gerçek/anonim kökeni belgeli bağımsız vakalar ve hukuk kaynağı kontrolü.
- Üye 2: iki sağlayıcının sentetik gerçek denemesi; tarihli kullanım/maliyet ve
  hata/timeout karşılaştırması. Anahtar/tarife doğrulanmadan otomatik canlı çağrı yapılmaz.
- Üye 3: insan etiketi toplama, dış ekip red-team, güvenli sentetik deploy,
  yönetişim kaynakları, video ve sunum.
- Ortak: lisans/atıf kararı, insan kod incelemesi, dosya anlatma provası.

Bu görevler atama önerisidir; tamamlandı beyanı değildir.
Birbirine bağlı alanlarda PR açıklamasında sözleşme değişikliği belirtilir.

## Bireysel kanıt

Commit yazarı gerçek katkı sahibidir. AI aracı katkısı README'de açıklanır.
Ölçüm tarihi, komut, kapsam, önce/sonra hatası ve PR bağlantısı tutulur.
Üye numarasıyla test sayısı yarıştırılmaz; yeni katkının çözdüğü problem gösterilir.
Zeynep bu sürümün başvuru bağı ve tek paket düzeltmesini, testlerin neden önce
başarısız olduğunu ve SHA-256'ın sınırlarını anlatmalıdır.

## İnsan incelemesi

İnceleyen; kaynakların aynı başvuruyu temsil ettiğini, hatada eski verinin
temizlendiğini, ağsız/gerçek model ayrımını ve sırların dışarı çıkmadığını kontrol eder.
Otomatik CI insan incelemesi değildir. Ekip onayı olmadan belgede onay verildi yazılmaz.
