# Geliştirme planı

## Tamamlanan Üye 1 temeli

- [x] Mevcut `main` geçmişi korunarak başlangıç kurulumu ve `develop` dalı.
- [x] Kaynak PDF ve API anahtarı Git dışında, `.env.example` paylaşılabilir.
- [x] 100 sentetik, gerçek kişi bilgisi taşımayan sipariş.
- [x] Kaynak URL'si, SHA-256 ve madde/fıkra kimliği olan 40 seçili pasaj.
- [x] Yerel BM25 ve EVREN gömme + Qdrant hibrit getirme.
- [x] Birebir alıntı ve istekte getirilen kaynak kontrolü.
- [x] Sipariş, cayma süresi ve yıllık parasal sınır araçları.
- [x] Komut satırı kanıt paketi ve dört araçlı MCP stdio sunucusu.
- [x] 18 standart + 6 sınır + 6 adversarial vaka; ağsız koşucu.
- [x] Ajan entegrasyon kancası ve gerçek etiketlerle kalibrasyon hesaplayıcı.
- [x] Testler, biçim/kod kontrolü ve anahtarsız CI başlangıcı.

## Üye 1 sonraki aşama

1. Hukuk uzmanıyla seçili maddelerin güncellik, kapsam ve alıntı denetimi.
2. 40 pasajı, gerçekten gerekli yeni resmî belgelerle genişletme; kurumsal
   politikayı resmî mevzuatla karıştırmadan ayrı kaynak türü olarak ekleme.
3. Ekipçe en az 10 vakada gerçek insan değerlendirmesi; hakem modelinin
   skorlarıyla uyum/kappa hesaplama. Henüz insan etiketlemesi yapılmadı.
4. Geliştirmede kullanılmamış yeni bir test seti hazırlama. Mevcut 30 vaka
   geliştirme sırasında kullanıldı; bağımsız genelleme ölçüsü değildir.
5. [İlk yerel/EVREN karşılaştırmasının](rag_olcumleri_v0.3.md) ardından yeni,
   bağımsız vakalarla konu dışı getirme ve bilinen ayıp ayrımını inceleme.
6. Bağlı Üye 2 ajanında gerçek insan etiketleriyle karar doğruluğu ve gerekçe sadakati eval'i.

## v0.3 ile eklenen hazırlık ve ölçüm

- [x] Mevcut 30 vakadan ayrı, 35 pozitif + 9 boş sonuç sorgusuyla RAG karşılaştırma seti.
- [x] Yerel/EVREN için hit, recall, precision, MRR ve nDCG; API kullanımı ve p50/p95 gecikme.
- [x] İndeks hazırlığı ve sorgu ölçümünün ayrılması; hata vakalarının paydada tutulması.
- [x] 10 farklı sorgu × 2 yöntem için beklenen cevabı/yöntemi göstermeyen inceleme dosyaları.
- [x] Gerçek puanlar girildiğinde kanıt değişikliğini ve eksik etiketleri kontrol eden kalibrasyon akışı.

Bu ek set de geliştirme amacıyla hazırlanmıştır. İnsan etiketleri ve görülmemiş,
ekipçe bağımsız hazırlanmış test seti gereksinimi devam eder. Ölçülen konu dışı
yanlış getirmeler ve bilinen ayıp/seçimlik hak ayrımındaki eksik kaynak, sonraki
iyileştirme için kayıtlıdır; bu turda aynı sorgulara özel sıralama kuralı eklenmedi.

## Takım entegrasyonu

| Sorumlu | Yapılacaklar | Kabul kanıtı |
| --- | --- | --- |
| Üye 2 | Mevcut sınırlı ajan/şema/maliyet katmanını iki gerçek sağlayıcıda ölçme | Ağsız testlere ek olarak gerçek token/tarife ölçümü |
| Üye 3 | Mevcut Streamlit/inceleme akışında insan etiketleri, yönetişim ve sunum | Gerçek etiketler, dış red team ve demo |
| Birlikte | İnsan etiketleri, mevzuat denetimi, gerçek red team eşleşmesi | Tarihli ve örnek sayılı rapor |
| Birlikte | Yayınlama ve video | Gerçek canlı adres ve erişim kontrolü |

PDF'teki örnek %86,7 başarı, %93,3 hakem uyumu, %100 red team, maliyet,
soğuk başlangıç ve demo adresleri **ölçülmüş sonuç olarak kopyalanmadı**.
Tamamlanmayan bileşenler için 8/8 teslim iddiası yoktur.
