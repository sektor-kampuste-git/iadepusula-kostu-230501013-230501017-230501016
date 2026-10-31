# Kurulum ve doğrulama rehberi

Bu belge geliştirme komutlarını ve çalışma biçimlerini açıklar.
Ürün tanıtımı [ana README](../README.md), kapsam [SPEC](../SPEC.md) içindedir.

## Yerel ekran

Python 3.11+ gerekir. Git ile klonlayın veya GitHub'da Code → Download ZIP seçin;
komutları proje kökünde çalıştırın. macOS/Linux'ta Python yolu .venv/bin/python olur.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

İlk kurulum bağlantıya bağlıdır; beş dakikalık temiz kurulum hedefi henüz ölçülmedi.
SIP-2026-1002, 2026-10-31 ve “Kulaklık bozuk, ayıplı mal nedeniyle iade istiyorum.”
sabit senaryosuyla Yerel kanıt veya Ağsız ajan demosu denenebilir.
Başka tarih seçilirse hesapların değişmesi beklenir.

## Gerçek model ve ortam

Ağsız kullanımda .env gerekmez. Gerçek model için [.env.example](../.env.example)
alanlarını sunucu ortamına veya yerel .env dosyasına aktarın.
Var olan .env dosyasını örnek dosyayla ezmeyin; anahtarı Git'e eklemeyin.

- LLM_BASE_URL, LLM_API_KEY, LLM_MODEL: sağlayıcı bağlantısı.
- LLM_TIMEOUT_SECONDS, LLM_MAX_TOKENS: istemci sınırları.
- AGENT_MAX_STEPS, AGENT_MAX_MODEL_CALLS, AGENT_MAX_TOOL_CALLS,
  AGENT_MAX_USD, AGENT_MAX_SECONDS: iş akışı bütçeleri.
- PRICE_INPUT_USD_PER_MILLION, PRICE_OUTPUT_USD_PER_MILLION,
  PRICE_CHECKED_ON, PRICE_SOURCE, PRICE_KIND: açık ve tarihli tarife.
- RAG_BACKEND ve EMBEDDING_MODEL: isteğe bağlı semantik arama ayarları.

EVREN örnek ayarı doğrulanmış iki sağlayıcı başarısı değildir.
Gerçek model modu açık sentetik veri/API onayı ister. Tarife yoksa çağrı yapılmaz.
Test tarifesi gerçek ağ istemcisinde reddedilir. Gerçek çağrı kota tüketebilir.
[Sağlayıcı ve bütçe sözleşmesi](uye2_entegrasyon.md).

## Geliştirme ve ağsız kontroller

Geliştirme dalı develop, doğrulanmış sürüm main'dir. Özellik başına PR kullanılır.
Kod incelemesi ve ortak sözleşmeler [ekip rehberinde](ekip_calisma_rehberi.md).

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check app.py src eval scripts tests maliyet_hesapla.py
.venv\Scripts\python.exe -m ruff format --check app.py src eval scripts tests maliyet_hesapla.py
.venv\Scripts\python.exe scripts/check_secrets.py
.venv\Scripts\python.exe -m scripts.check_docs --output artifacts/docs.json
.venv\Scripts\python.exe -m eval.eval_kosucu --min-pass-rate 0.85 --output artifacts/eval.json
.venv\Scripts\python.exe -m scripts.demo_uye2 --output artifacts/uye2-demo.json
```

Testler gerçek sağlayıcı çağırmaz. Model HTTP yanıtları taklittir; yerel araçlar/RAG
gerçek kodu çalıştırır. CI aynı kontrolleri üç Python sürümünde çalıştırır.
Belge kontrolü dosya ve bağlantıları doğrular; hukuki uyum veya not vermez.

### Kurulu paket kontrolü

```powershell
.venv\Scripts\python.exe -m pip wheel . --no-deps --wheel-dir artifacts/wheels
.venv\Scripts\python.exe scripts/verify_package.py artifacts/wheels
```

Kaynak depo dışındaki wheel doğrulaması; CLI, veriler, eval ve temel ajan/istemci
modüllerini sınar. Paket dizininde tek İadePusula wheel dosyası bulunmalıdır.

## Maliyet

```powershell
.venv\Scripts\python.exe -m maliyet_hesapla --input-tokens 2100 --output-tokens 450 --input-price 1 --output-price 2 --users 1000 --requests-per-user 10
```

Bu komut yalnız kullanıcı varsayımını hesaplar: 0.003 USD/istek, 30 USD/ay.
Gerçek sağlayıcı fiyatı/faturası değildir; barındırma, gömme ve işletim dahil değildir.
Kamusal derlem gömmelerinde önbellek vardır; nihai taslak önbelleği/model kademesi
tasarrufu henüz ölçülmedi. Rezervasyon kesin sağlayıcı harcama tavanı değildir.

## Sorun giderme

- Modül bulunamıyorsa komutu doğru .venv Python'u ile ve proje kökünde çalıştırın.
- Tarife eksikse beş PRICE alanını inceleyin; bilinmeyen maliyeti sıfır yazmayın.
- Kaynak/sipariş bulunmuyorsa sabit demo girdileriyle deneyin; hatalı girdide model çağrılmaz.
- Ağsız demo token/maliyetleri gerçek kullanım değildir.
- Onay sonrası girdi/mod değişirse yeni inceleme gerekir; eski raporun silinmesi beklenen davranıştır.
- Windows'ta pytest önbelleği yazılamıyorsa -p no:cacheprovider ile çalıştırılabilir.

Kaynak metni, tarih ve maskeleme sınırları [model kartında](model_karti.md) açıklanır.
