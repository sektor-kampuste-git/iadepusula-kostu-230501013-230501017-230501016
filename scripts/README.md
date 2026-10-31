# Yardımcı komutlar

Komutlar depo kökünden çalışır; gerçek API kullanılan yol açıkça ayrılır.

- demo_karar_semasi.py: elle hazırlanmış sentetik taslağın doğrulayıcıları.
- demo_uye2.py: gerçek yerel araç/RAG + taklit model; anahtar gerekmez.
- check_secrets.py: izlenen dosyalarda yanlışlıkla yayımlanan sır örüntüleri.
- check_docs.py: yerel Markdown bağlantıları ve kriter/kanıt tutarlılığı; ağsız.
- verify_package.py: wheel dosyasını depo dışında doğrulama.
- generate_orders.py: sabit seed ile sentetik sipariş verisi oluşturma.
- build_corpus.py: kaynaklardan pasaj hazırlama; veri değişikliği ayrıca incelenir.
- smoke_evren.py: **gerçek API çağrısı**, açıkça çalıştırılmalıdır; sentetik veri
  ve yapılandırma gerekir. Tam ajan/iki sağlayıcı eval'i değildir.

Günlük doğrulamada veri üretim dosyalarını veya gerçek API smoke testini
kendiliğinden çalıştırmayın. Çalışan örnekler [ana README'de](../README.md).
