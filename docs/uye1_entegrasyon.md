# Üye 1 entegrasyon sözleşmesi

Üye 1 RAG artışı: `0.3`; ortak ürün: `0.3.2`. İadePusula adı kullanılır;
PDF'teki İadeHakem AI aynı proje fikrinin adıdır. Bu katman **kanıt paketi** üretir.
Ortak sürümde ajan taslağı ve insan inceleme arayüzü vardır; kesin hukuki karar,
ödeme ve tebligat uygulanmaz. Güncel ortak akış [mimaridedir](mimari.md).

## Python giriş noktaları

```python
from datetime import date
from src.evidence import hazirla_inceleme
from src.rag import MevzuatRetriever
from src.tools import (
    siparis_detay_getir,
    cayma_suresi_hesapla,
    parasal_sinir_kontrol,
)

paket = hazirla_inceleme(
    "SIP-2026-1002",
    "Kulaklık bozuk, ayıplı mal nedeniyle iade istiyorum.",
    date(2026, 10, 31),
)
# Pydantic nesnesi: paket.model_dump(mode="json")
```

`src/contracts.py`, Üye 1'in tipli veri sözleşmeleridir. Üye 2'nin
`src/schemas.py` taslak karar şeması ortak sürümde bu pakete bağlıdır.
`IncelemePaketi.basvuru_tarihi` yeni üretimde doldurulur; eski pakette tarih
yoksa ajan model yoluna geçmez.

| İşlev | Dönen tip | Önemli sözleşme |
| --- | --- | --- |
| `siparis_detay_getir(siparis_no)` | `Siparis \| None` | Yalnız tekil sentetik sipariş; bilinmeyen kayıt için `None` |
| `cayma_suresi_hesapla(teslim, basvuru, ...)` | `CaymaSonucu` | Tarihler `date` veya ISO `YYYY-MM-DD`; takvim günü |
| `parasal_sinir_kontrol(tutar, yil)` | `ParasalSinirSonucu` | Para metin/Decimal/tamsayı; float kabul edilmez |
| `MevzuatRetriever.search(sorgu, top_k=3, ...)` | `tuple[AramaSonucu, ...]` | En fazla 10 parça; boş sonuç mümkündür |
| `hazirla_inceleme(...)` | `IncelemePaketi` | En fazla dört bileşen çağrısı; insan onayı daima `True` |

Başvuru tarihi burada da `date` veya ISO tarih olabilir; `datetime` kabul edilmez.
Normalleştirme sonrasında da 4000 karakter sınırı uygulanır.

Sipariş numarası `SIP-2026-1001` biçimindedir. `ValueError` geçersiz girdiyi,
`ProviderError` sağlayıcı erişim/yanıt hatasını belirtir. Araç sonucu bulunamadığında
modelin tarih veya tutar tahmin etmesine izin verilmemelidir.

## Süre ve tutar ayrımları

- Teslim günü gün 0'dır; 14. gün olağan süreye dahildir. Ara günlerdeki tatiller çıkarılmaz.
- Tek siparişin ayrı teslimlerinde `diger_teslim_tarihleri` son teslimi esas alır.
  Düzenli abonelik teslimleri bu parametreyle modellenmez.
- Teslim öncesi başvuru `TESLIM_ONCESI` döner; negatif gün sayısı üretilmez.
- Bilgilendirme eksik, belirsiz veya sonradan yapılmışsa `EK_BILGI_GEREKLI` döner;
  `son_gun` ve `kalan_gun` boştur. Bir yıllık üst süre konusunda kesin karar verilmez.
- `gecen_gun`, her zaman teslimden başvuruya takvim günü farkıdır.
- Olağan son gün hafta sonu/resmî tatil ise olası ilk iş günü ayrıca gösterilir.
  Bu aralıktaki başvuruda otomatik süre aşımı verilmez; hukuki uzama uzman değerlendirmesidir.
- Mağaza satışına mesafeli satışın cayma hesabı uygulanmaz.
- Cayma süresinin geçmesi, ayıplı mal haklarını sona erdiren bir karar değildir.
- Açılmış ambalaj tek başına sağlık/hijyen istisnası sayılmaz. Madde 15'in
  “taraflarca aksi kararlaştırılmadıkça” bağlamı parçada `baglam` alanındadır.
- Parasal sınır başvuru yılına aittir; 2026 için resmî tebliğin “altında” koşulu
  uygulanır. Bilinmeyen yıl `YIL_DESTEKLENMIYOR` döner; eski yıl taşınmaz.

## RAG ve atıf doğrulama

```python
rag = MevzuatRetriever()
bulunan = rag.search("6502 Madde 8 ayıplı mal")
p = bulunan[0].parca
atif = rag.citation_for(p.chunk_id)
assert rag.verify_citation(atif, allowed_ids={r.parca.chunk_id for r in bulunan})
```

Modelin kaynağı yalnız derlemde bulunması yeterli değildir; **o istekte getirilen**
`allowed_ids` içinde olmalıdır. URL, madde, belge kimliği ve alıntı da eşleşmelidir.
Atıf ayrıca `kaynak_turu`, `belge_basligi`, `baglam` ve `kaynak_sayfalari`
taşır; bunları değiştirmek doğrulamayı geçmez. Özellikle MSY 15 istisnalarının
“taraflarca aksi kararlaştırılmadıkça” koşulu atıfta korunur. Bu alanlar v0.2
entegrasyon sözleşmesinin parçasıdır; eski elle oluşturulmuş atıflar güncellenmelidir.
Bu kontrol, gerekçenin tamamının doğru olduğunu ispatlamaz. Anlam sadakati ayrıca
insan/hakem değerlendirmesi gerektirir.

Yerel yol BM25 ve Türkçe sorgu genişletmesi kullanır. Anlamsal yol,
EVREN `qwen3-embedding-8b`, bellek içi Qdrant, kosinüs araması ve reciprocal rank
fusion kullanır. Sıralama skorları güven yüzdesi değildir. `MSY`, `TKHK`, `6502`
ve belge adlarıyla açık madde/fıkra/bent çözülür; `c` ile `ç` farklıdır. Belgesiz
`Madde 11` sorgusu belirsizdir: belge adı veya tek `belge_ids` filtresi gerekir.
Birden fazla açık hüküm istendiğinde her birinden sonuç ayrılır; bilinmeyen
bir hüküm varsa bilinen diğer hükümle sessizce doldurulmaz. Açık madde isteği
`top_k` nedeniyle kısalıyorsa `istek_kirpildi` ve `istek_eslesme_sayisi` bunu gösterir.

CLI ve smoke testinde yalnız **kamusal derlem vektörleri**, `.cache/embeddings/`
altında 24 saat geçerli JSON önbelleğinde tutulur. Aynı model/API adresi ve aynı
başlık/bağlam/metin yeniden kullanılır; kullanıcı sorguları diske yazılmaz.
Kaynak veya model adı değişirse yeni anahtar oluşur. Bozuk/eski önbellek yeniden
üretilir; disk yazılamıyorsa arama önbelleksiz sürer. Model sağlayıcısı aynı takma
adın arkasındaki ağırlıkları değiştirirse önbellek de yenilenmelidir. Sorgu gömmesi
her aramada API'ye gider; sıfır API maliyeti veya tam yanıt önbelleği iddiası yoktur.
Kütüphane çağrısında önbellek `cache_dir=...` ile açıkça seçilir.

`MevzuatRetriever.prepare()`, gömme yolunda indeksi zamanlı sorgudan önce hazırlar;
yerel yolda API çağırmaz. [44 sorguluk karşılaştırma](rag_olcumleri_v0.3.md)
hazırlık ve sorgu sürelerini ayrı tutar. `ProviderError.status_code`, yetki/kota
hatalarında ölçümü durdurmak içindir; ham sağlayıcı yanıtı taşımaz. API gözlemleri
yalnız süre, HTTP durum ve izinli token alanlarını taşır. Bu ölçümler Üye 2'nin
taslak üretim maliyetine kendiliğinden eklenmez.

## MCP

```json
{
  "mcpServers": {
    "iadepusula": {
      "command": "C:/Users/EMRE/Desktop/iadepusula/.venv/Scripts/python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "C:/Users/EMRE/Desktop/iadepusula"
    }
  }
}
```

Diğer makinelerde yollar değiştirilmelidir. `stdio` sunucu dört araç yayınlar:
`siparis_detay_getir`, `cayma_suresi_hesapla`, `parasal_sinir_kontrol`, `mevzuat_ara`.
Dinlenen ağ portu yoktur. Sipariş aracı gerçek sistemlere bağlı değildir.
Gerçek kayıtlarda kimlik ve sipariş sahipliği kontrolü ayrıca zorunludur.

## Üye 2 ve Üye 3 bağlantıları

Üye 2'nin istemci, sınırlı ajan, taslak doğrulama, güvenlik ve maliyet katmanı
ortak sürümdedir; ayrıntı [Üye 2 sözleşmesindedir](uye2_entegrasyon.md).
UI/eval hazır kanıtı `run_packet()` ile tekrar üretmeden kullanır.
`src/evren.py`, Üye 1'in dar kapsamlı gömme/bağlantı adaptörüdür;
tam ajan veya bütçe altyapısı olarak sunulmamalıdır.

Üye 3'ün Streamlit ekranı kaynak/uyarıları ve başvuruya bağlı taslağı gösterir;
insan inceleme kaydı vardır. Bu yerel demo, gerçek kimlik/RBAC veya kalıcı kurumsal
onay değildir. Paket içindeki `True` bayrağı tek başına insanın onay verdiği
anlamına gelmez. [RAG inceleme paketi](../eval/insan_incelemesi.md) etiket toplama
hazırlığıdır; uygulamadaki başvuru onayından ayrı bir ölçüm işidir.

`src/privacy.py` yalnız başlangıç sınırıdır. İsim/adres tespiti, kapsamlı KVKK,
bağlamsal dolaylı enjeksiyon savunması ve gerçek RBAC tamamlanmış değildir.
Sağlayıcı denemeleri mevcut kapsamda sentetik başvurularla yapılmalıdır.
