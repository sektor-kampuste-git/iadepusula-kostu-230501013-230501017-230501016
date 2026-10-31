# Dosyaları anlatma rehberi

Amaç kodu ezberlemek değil, bir başvurunun nasıl ilerlediğini açıklamaktır.
Önce [mimari](mimari.md), ardından aşağıdaki dosyalar okunur.
Tüm modüller için [src rehberi](../src/README.md) kullanılır.

## Ortak prova: hangi dosya, neden?

- app.py: girdiler, mod seçimi, oturum ve eski sonucun temizlenmesi.
- ui_service.py: kanıt/UI ile ajan arasında tek entegrasyon noktası; açık onay.
- contracts.py: sipariş, kaynak, hesap ve kanıt paketinin ortak veri dili.
- evidence.py: salt okunur dört bileşenden paket; model kararı vermez.
- rag.py ve references.py: kaynağı getirmek ile alıntıyı doğrulamak farklı işlerdir.
- tools.py: para ve tarihte deterministik hesap; hukuki nihai karar değildir.
- schemas.py: modelin geçerli JSON üretmesi içeriğin doğru olduğu anlamına gelmez;
  kaynak, tutar ve insan onayı ayrıca doğrulanır.
- agent.py: bütçe/adım/zaman ve başarısızlıkta güvenli durma; keyfî araç ajanı değildir.
- llm_client.py ve config.py: sağlayıcı ile bağlantı, sırları saklama, yapılandırma.
- costs.py: kullanım gelmediyse sıfır maliyet yazmama; rezervasyon faturadan farklıdır.
- case_binding.py: aynı siparişte farklı şikâyeti ayırt etme; süre/skoru kimliğe almama.
- human_review.py ve agent_review.py: kaynak okuma/gerekçe ve aynı başvuru bağı.
- tracing.py: içerik taşımayan iz; kurumsal değiştirilemez günlük değildir.
- eval/eval_kosucu.py: beklenen cevap ajana verilmez; araç başarısı karar başarısı değildir.
- tests/test_case_binding.py: aynı kaynaklarla farklı başvuruyu onaylama ve çift
  hazırlama hatalarının tekrarını önler.
- scripts/check_docs.py: yerel bağlantı ve kanıt yollarını kontrol eder; not veya uyum vermez.
- maliyet_hesapla.py: kullanıcı varsayımıyla hesap; gerçek fiyat ölçümü değildir.

## Herkesin cevaplayacağı sorular

1. Hangi veri gerçek, hangisi sentetik veya model taklidi?
2. Model geçerli şemada yanlış cevap verirse hangi kontrol yakalar, hangisi yakalayamaz?
3. Tarife/kullanım bilinmiyorsa neden yeni çağrı yapmıyoruz?
4. Aynı sipariş için ikinci başvuru geldiğinde eski onay neden geçersiz?
5. Kaynak doğru olsa bile mevzuat güncel veya tüm koşulları kapsıyor mu?
6. Demo onayı neden kimlik/rol doğrulaması yerine geçmez?
7. 30/30 hangi ölçüm; gerçek tüketici başarısı neden değil?
8. Bugün hangi teslim kanıtları eksik?

Cevap kanıtı [gereksinim listesinde](proje_isterleri.md) ve tarihli kayıtlardadır.
Anlaşılamayan kod inceleme sorusu olarak PR'da kaydedilir; okunmadan sahiplenilmez.
