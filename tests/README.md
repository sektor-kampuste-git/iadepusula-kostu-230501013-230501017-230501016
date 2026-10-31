# Ağsız testler

Depo kökünde `python -m pytest -q`. Gerçek sağlayıcı çağrısı yapılmaz;
HTTP cevapları taklit edilir, geçici dosyalar kullanılır. UI AppTest yerel
Streamlit akışını test eder; görsel tarayıcı/çok kullanıcı testi yerine geçmez.

- test_tools, test_evidence, test_rag, test_audit_regressions: tarih, Decimal,
  kaynak, hatalı veri ve RAG regresyonları.
- test_provider, test_vector_cache, test_mcp_server: bağlantı/önbellek/araç sınırları.
- test_schemas: en az üç doğrulayıcının olumlu/olumsuz örnekleri.
- test_member2_*: ayar, istemci, bütçe, kullanım belirsizliği ve güvenli durma.
- test_human_review, test_ui, test_ui_agent_integration: insan gerekçesi,
  onay yenileme, yerel/demo/gerçek mod ayrımı.
- test_case_binding: çift hazırlama yok; tarih/metin/kanıt değişince eski taslak yok.
- test_eval_runner: beklenen etiket sızıntısı ve yanlış payda gibi ölçüm hataları.
- test_docs: bozuk yerel bağlantı ve olmayan gereksinim kanıtı yakalanır.

Test sayısı gerçek model kararı başarı oranı değildir. Tarihli sonuçlar
[geliştirme kaydında](../docs/gelistirme_kaydi_2026-11-01.md).
Yeni test gerçek bir davranış/risk sözleşmesini sınamalı; yalnız uygulamayı
taklit etmek veya sayıyı artırmak için eklenmemelidir.
