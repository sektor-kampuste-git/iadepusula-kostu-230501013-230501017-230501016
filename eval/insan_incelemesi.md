# RAG insan incelemesi ve gerçek hakem kalibrasyonu

Bu akış **kaynak getirme kalitesini** değerlendirmeye hazırlar. Nihai ajan kararı,
hukuki görüş, tam KVKK güvenliği veya insan onayı arayüzü değildir.

## 1. Ölçüm dosyasını üret

```powershell
# Anahtar ve ağ gerekmez:
.venv\Scripts\python.exe -m eval.retrieval_benchmark --backend lexical
# Gerçek API kotası kullanır; yalnız sentetik sorgu seti içindir:
.venv\Scripts\python.exe -m eval.retrieval_benchmark --backend compare
```

`--limit 10` açık bir **ilk 10 sorgu alt kümesi** seçer; tam set sonucu diye
sunulmaz. `--top-k` 1–10 arasında olabilir. `.json` raporunun yanında okunabilir
`.md` dosyası yazılır. Yeni koşum başarısızsa eski başarı dosyası korunarak
yanıltıcı sonuç gösterilmez; JSON ve Markdown koşum durumunu belirtir.

## 2. Puanları boş inceleme paketini oluştur

```powershell
.venv\Scripts\python.exe -m eval.review_pack export --report artifacts\retrieval_benchmark.json --output artifacts\insan_incelemesi.jsonl --limit 10
```

Burada `--limit`, her yöntem için aynı 10 **farklı sorguyu** seçer. Seçim,
başarı skoruna bakmadan kategoriler arasında sırayla yapılır. Karşılaştırma
raporunda iki yöntem varsa 20 çıktı oluşur; bu, 20 bağımsız sorgu değildir.

Üç yerel dosya yazılır:

| Dosya | İçerik |
| --- | --- |
| `insan_incelemesi.md` | Okunabilir sorular, getirilen alıntılar, bağlam, kaynak türü ve sayfalar |
| `insan_incelemesi.jsonl` | Aynı kanıtlar; boş insan/hakem puanları ve not alanları |
| `insan_incelemesi.manifest.json` | Yöntem ve özgün sorgu eşlemesi ile değişmez kanıt özeti |

Puanlayan kişi önce yalnız Markdown/JSONL dosyalarını kullanmalıdır. Yöntem,
otomatik metrik ve beklenen kaynak/karar bu dosyalarda gösterilmez. Manifest
puanlama bitene kadar açılmamalıdır. Bu pratik bir körleme düzenidir; dosyalara
erişimi engelleyen bir güvenlik sistemi değildir. İki dosya aynı sorgunun farklı
çıktılarını içerdiğinden yöntem içerikten tahmin edilebilir.

## 3. Gerçek incelemeyi kaydet

Her JSONL satırında yalnız şu alanları doldurun:

- `human_score`: yeterli ve ilgili kanıt için tamsayı `1`, eksik/ilgisiz kanıt için `0`.
- `reviewer`: gerçek etiketleyenin kodu; herkese açık isim yazmak gerekmez.
- `notes`: değerlendirme gerekçesi, kişisel veri içermeden.
- `judge_score`: yalnız gerçek bir hakem değerlendirmesi çalıştırıldıysa tamsayı `0`/`1`.
- `judge_model`: kullanılan gerçek hakem modelinin adı ve sürümü.

Hakem modeli bu komut tarafından otomatik çalıştırılmaz. Puan bilinmiyorsa `null`
kalmalıdır; `0` boş alan değildir. Başarısız/çalışmamış arama kaynak kalitesi
olarak puanlanmaz. Boş sonuç ancak derlemde uygun kaynak yoksa veya soru belirsiz
bir maddeye dayanıyorsa uygun sayılabilir; bir hukuki hakkın bulunmadığı anlamına gelmez.

Soru, kimlik, alıntı ve bağlam alanlarını değiştirmeyin. Bunlar manifestteki
SHA-256 ile karşılaştırılır. Bu kontrol kazara düzenlemeyi yakalar; manifesti ve
kanıtı birlikte değiştiren kötü niyetli bir kişiyi doğrulamaz.

## 4. Doldurulmuş paketi ölç

```powershell
.venv\Scripts\python.exe -m eval.review_pack score --pack artifacts\insan_incelemesi.jsonl --manifest artifacts\insan_incelemesi.manifest.json --output artifacts\kalibrasyon.json
```

En az **10 farklı sorguda** hem insan hem hakem puanı gereklidir. Aynı sorguyu
birkaç kez puanlamak örnek sayısını artırmaz. Farklı hakem model/sürümleri tek
kalibrasyonda karıştırılmaz. Doldurulmamış çıktılar ayrıca bekleyen sayısında
kalır; başarı sayılmaz. Sonuç yüzde uyum ve Cohen kappa içerir. Tek sınıfta kappa
tanımsızsa `null` döner. Bu ölçüm sorular arası bağımsızlık veya hukuki doğruluk
garantisi vermez.

Ham inceleme dosyaları ve etiketleyen bilgileri `artifacts/` altında Git dışında
kalır. Yayımlanacak özet yalnız örnek sayısı, kullanılan hakem, derlem sürümü ve
toplu ölçümleri içerir. Hazır gelen dosyalarda gerçek puan yoktur; bu sürümde
insan/hakem kalibrasyonu **yapılmadı**.
