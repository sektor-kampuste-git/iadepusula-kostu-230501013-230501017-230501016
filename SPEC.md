# İadePusula ürün şartnamesi

Sürüm 0.3.2 · 1 Kasım 2026 · Takım Şarjör.
Kapsam burada, kanıt/durum [gereksinim listesinde](docs/proje_isterleri.md),
uygulama akışı [mimaride](docs/mimari.md) tutulur.

## Problem ve kapsam

Türkçe e-ticaret başvurularını ön inceleyen uzman; sipariş, süre, parasal sınır
ve kaynak koşullarını tek akışta görmek ister. Süre hesabı uyuşmazlığın esası
hakkında karar değildir. Mevcut prototip sentetik siparişler üzerinde çalışır.
Gerçek sipariş sistemi, otomatik para iadesi, tebligat ve kesin hukuki karar kapsam dışıdır.

## Ortak sözleşmeler

- IncelemePaketi: sipariş, başvuru metni/tarihi, hesaplar, kaynaklar ve araç izleri.
- Yeni paket başvuru tarihini taşır. Eski veriyi okuyabilmek için alan boş olabilir;
  tarih yoksa model yoluna alınmaz.
- RunReport: durma nedeni, sayaçlar, maliyet, doğrulanmış taslak ve kanıt özeti.
  Başarılı rapor taslak/özet taşır; başarısız rapor taslak taşımaz.
- Başvuru özeti tarih, metin ve iş kanıtına bağlıdır; süre/arama skoru dışlanır.
  İnsan incelemesi aynı paket, taslak ve istekle eşleşir.
- Özet imza, kimlik doğrulama veya anonimleştirme değildir.

## Beş kabul senaryosu

1. SIP-2026-1002 / 2026-10-31 / “Kulaklık bozuk, ayıplı mal nedeniyle iade
   istiyorum.” Kaynak ve hesaplar görünür; demo taslağı insan incelemesine gider.
2. SIP-2026-1001 / aynı tarih / “Gömleği iade etmek istiyorum.”
   Süre/uyarılar gösterilir; süre tek başına otomatik hukuki ret üretmez.
3. SIP-2026-9999 / aynı tarih / aynı metin. Bilinmeyen siparişte model/onay
   açılmaz; önceki rapor temizlenir ve anlaşılır mesaj gösterilir.
4. Boş veya bilinen talimat saptırma girdisi. Güvenli hata/durma; model çağrısı yok.
5. Taslaktan sonra metin/tarih değişir. Eski taslak/onay kullanılamaz.
   Kaynak okuma beyanı ve yeterli gerekçe olmadan rapor verilmez.

Bunlar kabul sözleşmesidir; gerçek iki sağlayıcıda manuel kabul testi
tamamlandı iddiası değildir. Ağsız karşılıklar tests/ altındadır.

## Mühendislik kabulü

UI, model istemcisi ve iş kuralları ayrılır. Sağlayıcı bilgileri ortamdan okunur.
Varsayılan üst sınır dört araç ve iki model denemesidir; adım/süre/USD denetlenir.
Para Decimal ile işlenir; bilinmeyen maliyet sıfır sayılmaz. Kaynak kontrolü ve
insan incelemesi başarısızsa güvenli durulur. Ham kişisel veri/sır yayımlanmaz.

## Teslim sırası

Tek kanıt paketi ve doğru başvuru bağı → iki gerçek sağlayıcının sentetik denemesi →
bağımsız/insan etiketli eval ve kalibrasyon → gerçek red team → ölçülmüş maliyet
ve optimizasyon → güvenli sentetik deploy → video, sunum ve teslim PDF'i.

Tam puan hedefi 30+ vaka ve 8+ red-team saldırısıdır. Test sayısı, veri kökeni ve
insan doğrulaması koşulunu karşılamaz. Not öğretim elemanına aittir.
