# Üye 2 entegrasyonu - v0.3.0

Hazırlama tarihi: 31 Ekim 2026. Temel: Üye 1 `cfc3e2c` sürümü.
Geliştirme Codex yardımıyla hazırlandı; Zeynep ve ekip kod incelemesi bekleniyor.

## Kapsam ve katmanlar

- `src/schemas.py`: taslak yapısı, doğrulayıcılar, isteğe bağlı kaynak ve tutar kontrolü.
- `src/llm_client.py`: yapılandırılabilir OpenAI uyumlu JSON istemcisi; her çağrı bir HTTP isteği.
- `src/config.py`: .env/ortam değişkenleri ve tarife/sınır ayrıştırması; sırları göstermeyen hatalar.
- `src/security.py`: normalleştirme, bilinen PII örüntüleri, girdi kısıtı ve veri minimizasyonu.
- `src/agent.py`: dört yerel araç ve en fazla iki model denemesiyle sınırlı iş akışı.
- `src/costs.py`: Decimal maliyeti, çağrı öncesi rezervasyon ve aylık senaryo.
- `src/tracing.py`: başvuru/model metni taşımayan JSONL özet kaydı.
- `maliyet_hesapla.py`: açık fiyat/token varsayımlarından ağsız maliyet simülasyonu.

Üye 1'in `contracts.py`, RAG, araçları, MCP sunucusu veya eval etiketleri değiştirilmedi.
Yalnız ortak yapılandırma, README, CI, paket tanımı ve ekip rehberi genişletildi.
Kod, arayüz kitaplığına bağımlı değildir. Fiyat hesabı, HTTP erişimi, iş akışı ve
sunum ayrı katmanlardır. İstemci ve saat bağımlılığı testlerde enjekte edilir.

## Ağsız deneme

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.venv\Scripts\python.exe -m scripts.demo_karar_semasi
.venv\Scripts\python.exe -m scripts.demo_uye2 --output artifacts/uye2-demo.json
.venv\Scripts\python.exe -m maliyet_hesapla --input-tokens 2100 --output-tokens 450 --input-price 1 --output-price 2
```

Demo, gerçek yerel sipariş/RAG bileşenlerini çalıştırır. Model HTTP yanıtı ve token
sayıları MockTransport ile taklit edilir; bunun gerçek model doğruluğu veya
gerçek sağlayıcı maliyeti olduğu iddia edilmez. .env/anahtar gerekmez.
Örnek fiyatlarla 2100 girdi + 450 çıktı için 0.003 USD/istek ve
1000 kullanıcı x 10 istek varsayımıyla 30 USD/ay hesaplanır. Bu yalnız varsayımdır.

## Gerçek istemci bağlantısı - ayrıca başlatılmalı

Bu pakette gerçek API denemesi yapılmadı. Aşağıdaki kod yalnız açıklama içindir;
çalıştırılması, tarife ve anahtar tanımlıysa gerçek sağlayıcı kotası tüketir.
Önce endpoint/model özellikleri ve fiyat kaynağı doğrulanmalıdır.

```python
from pathlib import Path
from src.agent import ButceliAjan
from src.config import load_configuration
from src.llm_client import LLMClient
from src.tracing import write_trace

settings, limits, price = load_configuration()
with LLMClient(settings) as client:
    agent = ButceliAjan(client, price, limits=limits)
    report = agent.run(
        "SIP-2026-1001", "Gömleği iade etmek istiyorum.", "2026-10-31", sentetik=True
    )
    write_trace(report, Path("traces") / f"{report.request_id}.jsonl")
```

`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` mevcut sözleşmedir.
Tarife için beş alanın tamamı gerekir: `PRICE_INPUT_USD_PER_MILLION`,
`PRICE_OUTPUT_USD_PER_MILLION`, `PRICE_CHECKED_ON`, `PRICE_SOURCE`, `PRICE_KIND`.
Son alan `provider_published` veya `user_assumption` olabilir; test tarifesi
gerçek ağ istemcisinde reddedilir. Tarife boşsa model çağrısından önce durulur.
Var olan .env dosyası örnek dosyayla ezilmemelidir; anahtar Git'e girmez.

`AGENT_MAX_STEPS=6`, dört yerel bileşen ve iki model denemesini birlikte sayar.
Retry ayrı adım ve maliyettir. Model keyfî araç çağıramaz; akış deterministiktir.
Kaynak bulunamaz, sipariş yoktur veya girdi engellenirse model çağrısı yapılmaz.

## Bütçe ve zamanın sınırları

- Çağrıdan önce UTF-8 bayt uzunluğu, şablon payı ve çıktı token sınırıyla tahmini maliyet ayrılır.
- Bu tokenizer ölçümü veya matematiksel kesin üst sınır değildir. Sağlayıcının
  kendi harcama limiti varsa ayrıca kullanılmalıdır.
- Kullanım geldiğinde tarife üzerinden token bedeli hesaplanır. Sağlayıcı
  faturası, indirimler, ücretsiz kota ve başka ücretler ayrıca doğrulanmalıdır.
- Kullanım bilinmiyorsa ayrılan maliyet korunur; sıfır kabul edilmez ve kör retry yapılmaz.
- Raporlanan kullanım tahmini aşarsa gerçek hesap raporda korunur ve yeni çağrı yapılmaz.
- Zaman sınırı yerel adımlar arasında kontrol edilir; devam eden yerel Python
  işlevini zorla sonlandırmaz. HTTP timeout kalan süreyle sınırlandırılır.
- Varsayılan RAG yereldir; EVREN gömmesinin maliyeti bu ajanın USD hesabına gizlice eklenmez.
  Semantik gömme yolu bağlanmadan önce o maliyet de bütçeye dahil edilmelidir.

## Arayüz sözleşmesi - Beste için

`RunReport.reason`, kullanıcıya anlaşılır mesajla gösterilir. Başarılı sonuç
`TASLAK_DOGRULANDI` ve `draft` alanıdır. Hata/eksik kanıt durumunda `draft=None`
olması otomatik ret anlamına gelmez; uzman incelemesi veya tekrar bilgi girişi gerekir.

`insan_onayi_gerekiyor_mu=True` yalnız taslak kuralıdır. Gerçek onay, değiştirme
gerekçesi, kimlik/yetki kontrolü ve denetim kaydı Üye 3'ün iş akışında ayrıca
uygulanmalıdır. Model insan adına onay kaydı oluşturamaz. API bu sürümde gerçek
müşteri, sipariş, ödeme veya bildirim sistemine bağlı değildir.

## Eval sözleşmesi - Emre için

```python
from eval.eval_kosucu import evaluate, load_cases
from src.agent import make_eval_predictor

# agent, çağıranın açıkça oluşturduğu istemci ve tarifeyi taşır.
# Bu çağrı gerçek istemci verilmişse API isteği yapabilir.
result = evaluate(load_cases(), predictor=make_eval_predictor(agent))
```

Beklenen etiketler predictor'a verilmez. Hata durumundaki fallback uzman
incelemesidir. Bu paketle gerçek karar doğruluğu, hakem kalibrasyonu veya
30 vakalık gerçek model başarısı raporlanmadı. Mevcut 30/30 sonucu yalnız Üye 1
araç/RAG geliştirme kontrolüdür; AI taslak etiketler bağımsız altın standart değildir.

## Güvenlik ve ölçeklenebilirlik sınırları

Desteklenen örüntülerde PII girişte maskelenir, çıktıda reddedilir. İsim/adres
tespiti garanti edilmez; sentetik onay parametresi verinin gerçekten sentetik
olduğunu bağımsız doğrulayamaz. Gerçek kullanıcı verisine açılmadan önce daha
kapsamlı veri koruma ve yetki denetimi gerekir. Anahtar kelime filtresi tek başına
tam injection savunması değildir; kanıt doğrulaması, izinli araçlar ve onay sınırıyla
birlikte kullanılır.

İstek sayaçları yereldir ve bir önceki isteğin verisini devralmaz. Model/RAG/UI
katmanları ayrıdır; ancak bu ölçek/yük testi veya üretim kapasitesi kanıtı değildir.
Kimlik doğrulama, gerçek sipariş sahipliği, oran sınırı, çok kullanıcı yük testi,
iki gerçek sağlayıcı, gerçek token maliyeti ve yayınlama halen bekler.

Önbellek/model kademesi optimizasyonları ölçülmedi. Üye 1'in kamusal derlem
önbelleği korunur; kişisel nihai taslakların kullanıcılar arasında paylaşılması yoktur.
Güvenlik/yönetişim belgelerinde hukukî sınıf ve tarihler ayrıca resmî kaynaklarla
doğrulanmalıdır; bu kod paketi hukukî uyumluluk sertifikası değildir.
