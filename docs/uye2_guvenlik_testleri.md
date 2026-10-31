# Üye 2 iç güvenlik regresyonları

Tarih: 31 Ekim 2026. Bunlar sentetik/ağsız birim ve bütünleşme kontrolleridir.
Sınıflar arası gerçek red-team eşleşmesi veya kapsamlı saldırı denetimi yerine geçmez.

1. **İnsan incelemesini kaldırma:** false, sayısal 1 veya metin true reddedilir.
   Kanıt: `test_model_cannot_disable_or_coerce_human_review`.
2. **Sahte kaynak:** yanlış URL, madde, belge, bağlam, alıntı ve sayfa reddedilir.
   Kanıt: `test_citation_metadata_and_quote_must_match_member_one_verifier`.
3. **Getirilmeyen kaynak:** derlemde bulunsa bile bu istekte getirilmeyen parça reddedilir.
   Kanıt: `test_real_corpus_source_not_retrieved_for_request_is_rejected`.
4. **Tutar manipülasyonu:** adayın ek fatura alanı ve güvenilir faturayı aşan tutar reddedilir.
   Kanıt: `test_amount_compares_with_trusted_invoice_not_model_supplied_invoice`.
5. **PII sızıntısı:** bilinen örüntüler girişte maskelenir; özet, gerekçe, kaynak
   ve eksik bilgi alanında reddedilir. Trace başvuruyu veya taslağı kaydetmez.
   Kanıt: `test_all_output_texts_reject_known_pii_and_public_error_hides_value`,
   `test_pii_is_masked_in_request_and_trace_never_contains_request_or_draft`.
6. **Doğrudan talimat enjeksiyonu/kapsam dışı görev:** bilinen örüntüler model çağrısından önce durur.
   Kanıt: `test_invalid_or_unsupported_inputs_do_not_call_provider`.
7. **Maliyet/döngü sömürüsü:** adım sınırı ve her retry öncesi yeni rezervasyon uygulanır.
   Kanıt: `test_step_limit_includes_four_tools_and_first_model_attempt`,
   `test_retry_requires_new_budget_reservation`.
8. **Kayıp kullanım ve belirsiz hata:** bilinmeyen tüketim sıfır yazılmaz,
   potansiyel olarak faturalanan çağrı körlemesine tekrarlanmaz.
   Kanıt: `test_unknown_usage_keeps_reservation_and_does_not_retry`,
   `test_transport_failure_does_not_blindly_repeat_potentially_billed_request`.
9. **Doğrulamayı atlama:** model_copy ile bozulmuş taslak sınırda yeniden doğrulanır.
   Kanıt: `test_model_copy_cannot_bypass_boundary_revalidation`.
10. **Sağlayıcı/anahtar taşıma:** HTTP yönlendirmeleri izlenmez, uzak güvensiz
    URL kabul edilmez, hata gövdeleri kullanıcıya taşınmaz.
    Kanıt: `test_unsafe_api_urls_are_rejected_before_request`,
    `test_http_failures_are_safe_and_client_never_retries_implicitly`.

Bu liste yalnız belirtilen davranışları kanıtlar. Bağlamsal dolaylı injection,
isim/adres yakalama, üretim RBAC ve gerçek kişilerle veri işleme henüz çözülmüş
sayılmaz. Bulunacak yeni kırılmaların girdisi sentetikleştirilerek regresyon
testine eklenmeli; ilk sonuç, düzeltme ve tekrar test ayrı kaydedilmelidir.
