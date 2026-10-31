# İadePusula

Türkçe e-ticaret iade ve ayıplı mal başvuruları için kaynaklı ön inceleme projesi.
Öneri üretir; nihai değerlendirme insan uzmana aittir.

## Geliştirme düzeni

- `main`: doğrulanmış, paylaşılabilir sürüm.
- `develop`: sürekli geliştirme ve ekip entegrasyonu.
- Özellikler `develop` üzerinden geliştirilir; testlerden sonra `main`e alınır.
- API anahtarı `.env` içinde tutulur; kaynak PDF ve anahtar dosyası Git'e eklenmez.

## İş bölümü

| Üye | Sorumluluk |
| --- | --- |
| 1 | Ürün kapsamı, mevzuat derlemi, RAG, deterministik araçlar, 30 vaka ve eval koşucusu |
| 2 | Ajan, sağlayıcı istemcisi, karar şemaları, güvenlik, maliyet ve CI |
| 3 | Streamlit arayüzü, insan onayı, yönetişim, red team ve sunum |

Bu ilk kurulum Üye 1 kapsamını temel alır. Proje dokümanındaki örnek skorlar,
kalibrasyon sonuçları, canlı demo adresleri ve tamamlanmış teslim iddiaları ölçüm
veya gerçek teslim kanıtı olarak kullanılmaz.
