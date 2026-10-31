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
5. Yerel/EVREN RAG karşılaştırması: hit@3, yanlış kaynak, anlamsal hata,
   tüm isteklerin token kullanımı ve gecikme dağılımı.
6. Üye 2 ajanı bağlandıktan sonra tam karar doğruluğu ve gerekçe sadakati eval'i.

## Takım entegrasyonu

| Sorumlu | Yapılacaklar | Kabul kanıtı |
| --- | --- | --- |
| Üye 2 | Tam ajan, istek/adım/maliyet sınırı, karar şeması, güvenlik ve maliyet | Ağsız hata/bütçe testleri ve gerçek token ölçümü |
| Üye 3 | Streamlit, insan onayı/değiştirme kaydı, yönetişim ve sunum | Çalışan kullanıcı akışı, red team ve demo |
| Birlikte | İnsan etiketleri, mevzuat denetimi, gerçek red team eşleşmesi | Tarihli ve örnek sayılı rapor |
| Birlikte | Yayınlama ve video | Gerçek canlı adres ve erişim kontrolü |

PDF'teki örnek %86,7 başarı, %93,3 hakem uyumu, %100 red team, maliyet,
soğuk başlangıç ve demo adresleri **ölçülmüş sonuç olarak kopyalanmadı**.
Tamamlanmayan bileşenler için 8/8 teslim iddiası yoktur.
