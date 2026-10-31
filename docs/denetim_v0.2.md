# v0.2 denetimi ve iyileştirmeleri

Tarih: 31 Ekim 2026. İncelenen başlangıç: `4cd78a7`, sürüm `0.1.0`.
Bu belge, ilk 80 testin geçmesinin kapsamadığı somut hataları ve yeni kanıtları kaydeder.

## Yeniden üretilen sorunlar ve sonuç

| Sorun | Önce | v0.2 davranışı |
| --- | --- | --- |
| Değerlendirmede cevap sızıntısı | `predictor(case)` beklenen kaynakları ve taslak kararı görebiliyordu | Etiketsiz `PredictorInput`, maskelenmiş metin ve kanıt paketi gönderilir |
| Başarısız ajan vakasının ölçümleri | Şema/API hatası bütün kontrolleri siliyor, kaynak paydasını ve süre ortalamasını saptırıyordu | Bileşen/ajan sonuçları ayrılır; hata vakası paydada, süre ve hata aşaması raporda kalır |
| Geçersiz eval beklentisi | Boş beklenti yalnız genel bayraklarla geçebiliyordu | Boş/çelişkili beklenti ve durum yazım hatası yüklemede reddedilir |
| İnsan kalibrasyonu girdisi | Boolean ve `1.0` skorlar tamsayı gibi kabul ediliyordu | Gerçek tamsayı 0/1 ve boş olmayan etiketleyen gerekir |
| Belge/fıkra/bent seçimi | MSY Madde 9 başka kanundan, 15/1-ç başka bentten sonuç getirebiliyordu | Belge takma adı/adı, madde, fıkra ve Türkçe bent harfi birlikte eşleşir |
| Çoklu madde isteği | Yalnız ilk madde süzülüyordu | Her açık hüküm için sonuç ayrılır; bilinmeyen hüküm sessizce atılmaz |
| Eksik madde sunumu | `top_k` nedeniyle maddenin bir kısmı döndüğü anlaşılmıyordu | Kısaltılma ve eşleşen parça sayısı açık alanlarda gösterilir |
| Yasal koşul ve kaynak türü | Atıf MSY 15 koşulunu veya rehberin statüsünü taşımıyordu | Kaynak türü, başlık, bağlam ve PDF sayfaları atfa bağlanır ve doğrulanır |
| Türkçe çekimli ifade | `bozuktu` kök anahtar sözcükle ortak özellik üretmiyordu | Beş harfli kök özelliği ve normalleştirilmiş durak sözcükler düzeltilir |
| Kapsamda yanlış ret | `elbise iade` içindeki `ise iade` parçası kapsam dışı sayılıyordu | Sözcük sınırı uygulanır; kriptografi kitabı ve kriptoyla ürün ödemesi de sebepsiz engellenmez |
| Yaygın kişisel veri biçimleri | Gruplu TCKN ve sabit telefonlar maskelenmiyordu | Boşluk/nokta/tireli TCKN, mobil ve sabit telefonların test edilen biçimleri maskelenir |
| Tarih ve metin sınırı | ISO metin tarih geç aşamada `TypeError`, Unicode genişlemesi uzun girdi üretebiliyordu | Girişte tarih ve normalleştirilmiş uzunluk doğrulanır; takvim taşması açıklanır |
| Sağlayıcı yanıtı | `null` içerik ve hatalı model listesi `AttributeError` çıkarabiliyordu | Şekil hataları güvenli `ProviderError`; boş/boolean/metin vektörleri reddedilir |
| Kurulum paketi | Wheel hiçbir JSON veri kaynağını taşımıyordu | Sipariş, mevzuat, sınır ve eval verileri pakete dahil edilir; kaynak klasörü dışındaki CLI çalıştırılır |

## Yeni iyileştirmeler

Kamusal derlem gömmeleri 24 saatlik, model ve metin kimliğine bağlı JSON önbelleğine
alındı. Kullanıcı sorguları yazılmaz. Bozuk/eski önbellek yeniden üretilir, atomik
yazılır; yazılamıyorsa arama sürer. 64'ten büyük derlemler API'ye en fazla 64 metinlik
partilerle gönderilir. Aynı takma ad arkasındaki model güncellemesinde önbelleği
yenilemek hâlâ gereklidir; bu bir tam yanıt veya USD bütçe altyapısı değildir.

CI, Python **3.11, 3.12, 3.14** üzerinde test, kaynak taraması, eval, wheel üretimi
ve kaynak depo dışında paket kontrolünü çalıştıracak şekilde genişletildi. Resmî
Actions paketleri denetim tarihinde mevcut sürümlere güncellendi. Bir matrisin
hatası diğerinin tanı sonucunu iptal etmez.

## Doğrulama

- **141 ağsız test geçti.** Yeni vakalar, yukarıdaki somut hataların regresyonları
  ve önbellek/model/değişmiş derlem/bozuk dosya durumlarını kapsar.
- Kod ve biçim denetimleri geçti. Düzenlenebilir kurulum yenilendi; bağımlılıklar tutarlı.
- Yeni wheel, kaynak klasörü dışında gerçek uygulama modülleri ve verileriyle
  doğrulandı; klasördeki kaynak dosyalara geri düşmediği ayrıca kontrol edildi.
- 30 vakalık mevcut geliştirme seti **30/30**, kaynak beklentili 20 vaka **20/20**.
  Bu sonuç bağımsız test, insan kalibrasyonu veya nihai karar doğruluğu değildir.
- Son gerçek EVREN testinde gömme, Qdrant araması ve birebir alıntı seçimi geçti.
  Soğuk çalışmada 2 gömme + 1 tamamlama isteği; yeni bir retriever ile sıcak
  çalışmada yalnız 1 sorgu gömme isteği gözlendi. Sorgunun hâlâ API'ye gittiği açıktır.

[Bileşen raporu](../eval/sonuclar/2026-10-31_v0.2_bilesenler.json) ·
[Anahtarsız EVREN/önbellek kanıtı](kanitlar/evren_v0.2.json).
Önceki sürümün tarihli raporları geçmiş ölçüm olarak korundu.

## Dış inceleme ve reddedilen öneriler

Ücretsiz DeepSeek ile RAG ve giriş/sağlayıcı incelemeleri tamamlandı; eval
incelemesi 180 saniyede sonuç üretmeden zaman aşımına uğradı. Eval hataları ana
ajan tarafından bağımsız olarak yeniden üretildi; başarısız iş onay sayılmadı.

“Kanun ve yönetmelik aynı URL/SHA taşıyor, kaynak yanlış” bulgusu uygulanmadı:
indirilen Bakanlık kitabı her iki hukuki metni de içeriyor. Kanun pasajları 8–10,
MSY pasajları 147–150. PDF sayfaları şimdi ayrıca taşınıyor. “Ceza davasında
ifadesi eski alt dizeyi hiçbir zaman eşleştirmez” iddiası da doğru değildi;
gerçek kapsam hatası geçerli başvurulardaki alt dize çakışmasıydı.

## Kalan sınırlar

Gerçek insan etiketleri, görülmemiş test seti ve mevzuatın hukuk uzmanı incelemesi
bekleniyor. İsim/adres maskeleme ve genel prompt injection savunması garanti
edilmiyor. Nihai bütçeli ajan ile kullanıcı arayüzündeki insan onayı, Üye 2/3
entegrasyonudur. Sürüm 0.2'de atıf alanları ve predictor girdisi değiştiği için
entegrasyon kodu güncel sözleşmeye geçirilmelidir.
