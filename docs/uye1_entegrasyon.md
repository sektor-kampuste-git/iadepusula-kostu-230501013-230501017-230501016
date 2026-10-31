# Üye 1 entegrasyon sözleşmesi

Sürüm: `0.1.0`. İadePusula adı kullanılır; PDF'teki İadeHakem AI aynı proje fikrinin adıdır.
Bu sürüm **kanıt paketi** üretir. Nihai karar, ödeme, tebligat veya onay işlemi uygulamaz.

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
`src/schemas.py` karar şeması için ayrılan dosya henüz oluşturulmadı.

| İşlev | Dönen tip | Önemli sözleşme |
| --- | --- | --- |
| `siparis_detay_getir(siparis_no)` | `Siparis \| None` | Yalnız tekil sentetik sipariş; bilinmeyen kayıt için `None` |
| `cayma_suresi_hesapla(teslim, basvuru, ...)` | `CaymaSonucu` | Tarihler `date` veya ISO `YYYY-MM-DD`; takvim günü |
| `parasal_sinir_kontrol(tutar, yil)` | `ParasalSinirSonucu` | Para metin/Decimal/tamsayı; float kabul edilmez |
| `MevzuatRetriever.search(sorgu, top_k=3, ...)` | `tuple[AramaSonucu, ...]` | En fazla 10 parça; boş sonuç mümkündür |
| `hazirla_inceleme(...)` | `IncelemePaketi` | En fazla dört bileşen çağrısı; insan onayı daima `True` |

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
from src.contracts import KaynakAtfi

rag = MevzuatRetriever()
bulunan = rag.search("6502 Madde 8 ayıplı mal")
p = bulunan[0].parca
atif = KaynakAtfi(
    chunk_id=p.chunk_id, belge_id=p.belge_id, madde=p.madde,
    dogrudan_alinti=p.metin, kaynak_url=p.kaynak_url,
)
assert rag.verify_citation(atif, allowed_ids={r.parca.chunk_id for r in bulunan})
```

Modelin kaynağı yalnız derlemde bulunması yeterli değildir; **o istekte getirilen**
`allowed_ids` içinde olmalıdır. URL, madde, belge kimliği ve alıntı da eşleşmelidir.
Bu kontrol, gerekçenin tamamının doğru olduğunu ispatlamaz. Anlam sadakati ayrıca
insan/hakem değerlendirmesi gerektirir.

Yerel yol BM25 ve Türkçe sorgu genişletmesi kullanır. Anlamsal yol,
EVREN `qwen3-embedding-8b`, bellek içi Qdrant, kosinüs araması ve reciprocal rank
fusion kullanır. Sıralama skorları güven yüzdesi değildir. Vektörler süreç içinde
bir kez oluşturulur; yeniden başlatmada tekrar gömme isteği yapılır. Kalıcı indeks,
yeniden kullanım ve maliyet denetimi Üye 2 ile sonraki entegrasyon konusudur.

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

## Üye 2 ve Üye 3 için devam noktaları

Üye 2; sağlayıcıdan bağımsız tam LLM istemcisini, bütçeli araç çağıran ajanı,
nihai karar şemasını, en az üç karar doğrulayıcısını, güvenlik ve maliyet katmanını
ekleyecek. `src/evren.py`, Üye 1 için dar kapsamlı gömme/bağlantı adaptörüdür;
tam ajan veya bütçe altyapısı olarak sunulmamalıdır. Mevcut CI, ağsız temel
doğrulamayı sağlar; Üye 2 bunu genişletebilir.

Üye 3; Streamlit'te paketin kaynaklarını, araç izlerini ve uyarılarını gösterecek;
insan onayı/değişiklik gerekçesi ve denetim kaydını kendi katmanında uygulayacak.
Paket içindeki `True` bayrağı, tamamlanmış bir onay iş akışı değildir.

`src/privacy.py` yalnız başlangıç sınırıdır. İsim/adres tespiti, kapsamlı KVKK,
bağlamsal dolaylı enjeksiyon savunması ve gerçek RBAC tamamlanmış değildir.
Bu entegrasyonlar bitene kadar sağlayıcı denemeleri sentetik başvurularla yapılmalıdır.
