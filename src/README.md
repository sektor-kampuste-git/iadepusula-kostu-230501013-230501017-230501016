# Uygulama katmanları

Modül yüklemek ağ isteği başlatmaz. UI, iş kuralları ve sağlayıcı ayrı tutulur.
Başlangıç [mimari](../docs/mimari.md) ve [SPEC](../SPEC.md).

## Veri ve yerel kanıt — Üye 1

- contracts.py: ortak Pydantic veri sözleşmeleri.
- paths.py: kaynak depo/kurulu paket veri yolları.
- tools.py: sipariş, süre ve parasal sınır araçları.
- rag.py: BM25 ve isteğe bağlı hibrit arama.
- references.py: kaynak kimliği, madde, URL ve alıntı denetimi.
- evidence.py: başvuru tarihi dahil tek IncelemePaketi üretimi.
- privacy.py: yerel veri maskeleme örüntüleri; tam anonimleştirme garantisi yok.
- evren.py: EVREN bağlantı/gömme ve ortak sağlayıcı ayarı.
- vector_cache.py: kamusal derlem gömme önbelleği.
- cli.py, mcp_server.py: aynı bileşenlerin CLI ve izinli MCP araçları.

## Model ve sınırlar — Üye 2

- schemas.py: tipli taslak ve kaynak/tutar/insan onayı doğrulayıcıları.
- config.py: ortam, limit ve tarife yükleme; sır içermeyen hata.
- llm_client.py: OpenAI uyumlu JSON istemcisi, kullanım ve hata ayrımı.
- agent.py: sınırlı model iş akışı; run() veya hazır kanıt için run_packet().
- costs.py: Decimal maliyet, rezervasyon ve aylık tahmin.
- security.py: model sınırında normalleştirme/maskeleme/engelleme.
- tracing.py: içeriksiz JSONL işlem izi.
- case_binding.py: tüm üyelerin kullandığı kararlı başvuru/kanıt özeti.

## Arayüz ve inceleme — Üye 3, ortak entegrasyon

- ui_service.py: yerel, ağsız taklit ve açık onaylı gerçek model yolları.
- human_review.py: gerekçeli kanıt incelemesi ve veri azaltılmış rapor.
- agent_review.py: model taslağını onaylama/değiştirme ve aynı başvuruya bağlama.
- ui_agent_panel.py: bütçe/durma nedeni ve insan formunu gösterme.
- __init__.py: ortak paket kimliği; yan etkisiz yükleme.

Bu başlıklar bakım sorumlusudur; her üye tümünü açıklayabilmelidir.
Yeni modül eklenince bu rehber, test ve [kriter kanıtı](../docs/proje_kriterleri.json)
aynı PR'da güncellenir.
