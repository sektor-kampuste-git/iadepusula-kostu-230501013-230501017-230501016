# Mimari ve veri akışı

Sürüm 0.3.1 · Güncel kapsam: [SPEC](../SPEC.md).
Katman ayrımı tek sorumluluk, bağımlılık enjeksiyonu ve test edilebilirlik içindir;
her sınıfa soyut arayüz eklemek amaç değildir.

## Bir başvurunun yolculuğu

1. app.py girdiyi ve modu toplar; başarısız yeni istek eski onayı temizler.
2. ui_service.py açık onay/yapılandırma sınırını uygular.
3. evidence.py sipariş, süre, parasal sınır ve arama sonuçlarından **bir** paket hazırlar.
4. agent.run_packet paketi yeniden tür doğrulamasından geçirir, tarihi ve izinli
   araçları denetler; kaynakların derlemle birebir eşleştiğini kontrol eder.
5. case_binding başvuru, tarih, sipariş, kaynak ve uyarıları kararlı özete bağlar.
6. Ajan tarife ve çağrı bütçesini kontrol edip llm_client aracılığıyla JSON ister.
7. schemas.py tip, kaynak/alinti, tutar ve insan onayı koşullarını doğrular.
8. agent_review.py taslağın ekranda gösterilen paketle aynı başvuruya ait olduğunu
   kontrol eder. İnsan değişikliği de şemadan geçer. Geçerli kayıt raporu açar.

## Sınırlar

run() CLI gibi paketi henüz olmayan çağıranlar içindir; run_packet() UI/eval
gibi zaten kanıt hazırlamış çağıranların paketi tekrar oluşturmasını engeller.
Çağıranın verdiği retriever çağırana aittir; ajan onu kapatmaz.

Başvuru tarihi IncelemePaketi'nde geriye dönük okumayı korumak için opsiyoneldir.
Yeni kanıt üretimi tarihi doldurur; tarih yoksa model yolu güvenli durur.
Eski başarılı RunReport kayıtlarında özet yoksa otomatik onay verilmez.

Süre ve arama skorları ölçüm alanıdır; başvuru kimliğini değiştirmez.
Özet SHA-256'tır; imza değildir ve kötü niyetli sunucuyu durdurmaz.

## Kaynaklar ve yan etkiler

RAG varsayılan BM25'tir. EVREN/Qdrant yolu isteğe bağlıdır; gömme maliyeti
model taslağı maliyetine dahil değildir. Kaynak metni güvenilmeyen veridir.
Araçlar salt okunur; ödeme/bildirim yazma yetkisi yoktur.
Kamusal derlem önbelleği sorgu metni depolamaz.

## Bütçe, zaman ve iz

Dört araç ve en fazla iki model denemesi toplam altı adımdır.
Fiyat belirsizse çağrı yoktur; kullanım yoksa rezervasyon korunur.
Yerel çağrı devam ederken zorla kesilmez; HTTP timeout kalan süreye göre ayarlanır.
UI kanıt hazırlama süresi run_packet ajan süresinden ayrıdır; tüm kullanıcı gecikmesi
ve gömme maliyeti ayrıca ölçülmelidir.

tracing.py ham başvuru/yanıt yerine istek kimliği, durma nedeni, kullanım ve
maliyet özeti yazar. JSONL yerel izdir; değiştirilemez kurumsal audit değildir.
Üretim için oturum, kimlik, RBAC, oran sınırı, kalıcı kayıt ve yük testi ayrıca gerekir.
