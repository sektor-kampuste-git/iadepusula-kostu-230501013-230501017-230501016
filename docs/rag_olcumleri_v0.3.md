# RAG v0.3 — ölçüm ve insan inceleme hazırlığı

Tarih: **1 Kasım 2026**. Bu adlandırma Üye 1 RAG artışını belirtir; ortak ürünün
0.3.2 sürümünü geri almaz. Kaynak sürümü değiştirilmedi; 40 pasajlık derlem kullanıldı.
Bu tur, aramayı aynı sorgulara göre yeniden ayarlamak yerine kaliteyi görünür
kılan ölçüm araçlarını ve gerçek insan değerlendirmesi hazırlığını ekler.

## Gerçek karşılaştırma

`eval/retrieval_cases.json`, eski 30 vakalık bileşen setinden ayrı 44 sorgu içerir:
35 kaynak beklenen sorgu, 4 açık madde/belirsizlik koruması ve 5 doğal konu dışı
sorgu. Etiketlerin tamamı **AI taslağıdır**. Set, bilinen derlemden geliştirme
amacıyla hazırlanmıştır; bağımsız test veya uzman etiketli değerlendirme değildir.

| Ölçüm | Yerel BM25 | EVREN + Qdrant hibrit |
| --- | --- | --- |
| Tamamlanan sorgu | 44/44 | 44/44 |
| İlk üçte beklenen kaynak (hit@3) | 34/35 (%97,14) | 34/35 (%97,14) |
| Sorgu başına ortalama recall@3 | %95,71 | %97,14 |
| Precision@3 | %34,29 | %35,24 |
| MRR@3 | 0,9143 | 0,9429 |
| nDCG@3 | 0,9230 | 0,9480 |
| Açık madde koruması, doğru boş sonuç | 4/4 | 4/4 |
| Doğal konu dışı soruda doğru boş sonuç | 3/5 | 3/5 |
| Tamamlanan sorgularda p95 | 0,42 ms | 245,95 ms |
| Ayrı ölçülen hazırlık | 3,73 ms | 2738,21 ms |
| API çağrısı | 0 | 41 gömme çağrısı |
| Sağlayıcının bildirdiği toplam token | 0 | 5208 |

Tek bir tam koşumdur; süreler tekrarlanmış deney veya SLA değildir. EVREN'in
hazırlığında 1 derlem gömme isteği (4029 token), sorgularda 40 istek (1179 token)
gözlendi. Dört açık madde koruması sorgusu API'ye gitmedi. Derlem önbelleği bu
koşumda yeniden oluşturuldu (`stored`). Tamamlama/karar modeli çağrılmadı.
Tarife bilinmediğinden USD maliyeti üretilmedi. Hesap bakiyesi, kota, anahtar ve
ham sağlayıcı hata metinleri rapora alınmadı.

Precision paydası `k=3`'tür; bir sorunun yalnız bir taslak ilgili kaynağı varsa
tek doğru sonuç precision@3 değerini en fazla 1/3 yapar. Bu yüzden precision,
hit ve recall ile birlikte okunmalıdır. İlgili ID listesi uzman tarafından
doğrulanmadığından alternatif doğru alıntılar düşük puan alabilir.

[Makinece okunabilir tam koşum](../eval/sonuclar/2026-11-01_rag_karsilastirma.json) ·
[Otomatik okunabilir rapor](../eval/sonuclar/2026-11-01_rag_karsilastirma.md)

## Gözlenen başarısızlıklar

- **RQ28:** satın alırken bilinen ayıp ile bilinmeyen ayıpları ayıran
  `6502-M10-F2`, iki yöntemde de ilk üçe girmedi.
- **RQ01:** yerel yöntemde teslimden itibaren süreyi açıklayan ikinci kaynak
  ilk üçe girmedi; en az bir kaynak bulunduğu için hit geçti, recall 0,5 kaldı.
- **RQ36 ve RQ42:** kuantum/alan denklemi ve yemek tarifi sorularında genel
  sözcük çakışmaları ilgisiz hukuki kaynak getirdi. Hibrit yöntem aynı iki
  hatayı korudu. Bu, konu dışı korumanın tamamlandığı anlamına gelmez.

Açık madde korumalarının başarısı doğal konu dışı sorularla birleştirilip tek
bir yüksek oran olarak sunulmaz. RAG'ın boş dönmesi de hükmün mevzuatta hiç
olmadığına ilişkin genel kanıt değildir.

## Yeni altyapı

- Açık `prepare()` ile indeks hazırlığı zamanlı sorgulardan ayrılır.
- Pozitif sorgularda hit/recall/precision/MRR/nDCG; negatiflerde ayrı boş sonuç ölçümü.
- API/hazırlık hataları paydada kalır; çalışmamış sorgu doğru boş sonuç sayılmaz.
- Yetki/kota hatasında veya üç ardışık hatada kalan istekler durdurulur ve
  `not_run` olarak raporlanır. Otomatik ücretli model veya sınırsız yeniden deneme yoktur.
- API gözlemleri yalnız izin verilen token sayısı, HTTP durum ve süre alanlarını taşır.
  Bilinmeyen kullanım sıfır sayılmaz; kaç isteğin kullanım bildirdiği ayrıca yazılır.
- 10 ayrı sorgu × 2 yöntem için 20 çıktılı, puanları boş insan inceleme paketi oluşturuldu.
  Kanıtlar sürüme bağlıdır; yöntem/otomatik skor/beklenen cevap puanlayana gösterilmez.

Ücretsiz DeepSeek tasarım incelemesi tamamlandı. Hazırlık ayrımı, ham kullanım
bilgisini dışarı vermeme ve insan paketinde yöntem adını gizleme önerileri
uygulandı. Fıkra/bent düzeyindeki farklı hükümleri tek madde olarak doğru sayma
önerisi uygulanmadı; örneğin Madde 11'in onarım süresi ile tazminat fıkrası aynı
soruyu karşılamaz.

## Doğrulama ve kalan işler

Ekip arkadaşlarının güncel `develop` sürümü korunarak birleştirilen projede
375 ağsız test, Ruff ve belge bağlantıları/kriter kanıtları denetimi geçti.
44 sorguluk yerel ölçüm tamamlandı; yeni veri setini içeren wheel kaynak depo
dışında doğrulandı. CI'a bu ölçüm ve paket kontrolleri de eklendi.
Mevcut 30 vakalık bileşen eval'i
30/30 olarak korundu. Gerçek insan etiketleri ve hakem değerlendirmesi henüz yok;
boş puanlı paketten kalibrasyon sonucu alınamaz. İnceleme adımları
[insan incelemesi rehberindedir](../eval/insan_incelemesi.md).

Son kod incelemesi için başlatılan ikinci ücretsiz DeepSeek işi kullanım
sınırında durdu; tamamlanmış inceleme sayılmadı. Kod burada ayrıca kontrol edildi.
Bozuk üst düzey JSON veri seti başarısız rapora çevrilir; türetilen Markdown ve
manifest çıktılarının girdi raporunu/veri setini ezmesi reddedilir. Bu hata yolları
ağsız testlerle doğrulandı. Ekip insan kod incelemesi henüz yapılmadı.
