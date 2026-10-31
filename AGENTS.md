# İadePusula geliştirme kuralları

- Her geliştirmeden önce SPEC.md, README.md ve docs/proje_kriterleri.json oku.
  Güncel develop/açık PR durumunu kontrol et; eski yükleme paketiyle kodu ezme.
- Kod/kabul koşulu, test ve ortak belgeleri birlikte güncelle. Klasör rehberleri
  sade olmalı; tüm ekip tüm dosyaları açıklayabilmeli.
- Mock test, gerçek sağlayıcı, insan etiketi ve deploy ayrı kanıttır. Hiçbirini
  diğerinin yerine sayma; tamamlanmayan teslimi veya not garantisini yazma.
- Belge yolları ve kriter kanıtlarını `python -m scripts.check_docs` ile doğrula.

- Kullanıcının oturumda belirttiği üye rolünü esas al. Üye 1: RAG, derlem,
  deterministik araçlar ve eval. Üye 2: istemci, şema, güvenlik, sınırlı ajan,
  maliyet ve CI. Üye 3: arayüz, insan onayı, yönetişim ve sunum.
- Geliştirme `develop` üzerinden yürür; `main` doğrulanmış sürümü barındırır.
  Mevcut commit geçmişini koru; force push yapma.
- Commit mesajlarını normal ve açıklayıcı dille yaz. Caveman, caveman-commit
  veya sıkıştırılmış commit üslubu kullanma; yapılan değişikliği ve nedenini belirt.
- `evrenkey.txt`, `.env`, kaynak PDF ve `.local/` gizli/yerel girdilerdir.
  Anahtarı hiçbir çıktıya, test fixture'ına, prompt'a veya commit'e koyma.
- PDF'teki ölçüm/teslim örneklerini gerçek sonuç olarak kopyalama.
- Para için Decimal, tarihler için açık ISO takvim tarihi kullan. Ayıplı mal ile
  cayma süresini ayrı tut. Kesin hukuki karar ve ödeme işlemi uygulama.
- Kaynak metni, URL, madde ve istekte getirilen chunk kimliğini birlikte doğrula.
- Değişiklikten sonra `python -m pytest -q`, `python -m ruff check src eval scripts tests`,
  `python -m ruff format --check src eval scripts tests` ve
  `python -m eval.eval_kosucu --min-pass-rate 0.85` çalıştır.
- Kök `maliyet_hesapla.py` dosyasını da Ruff kontrolüne dahil et.
- Üye 2 demosu `python -m scripts.demo_uye2` ile tamamen ağsız çalışır.
  Test tarifesini gerçek istemciye bağlama; bilinmeyen maliyeti sıfır yazma.
- Ağsız testler gerçek API çağrısı yapmamalı. EVREN smoke testi yalnız açıkça
  çalıştırıldığında sentetik senaryo kullanır; tam ajan eval'i değildir.
- Delegasyon faydalıysa ücretsiz OpenCode MCP çalışanlarını kullan;
  varsayılan `opencode/deepseek-v4.1-flash-free`, ikinci görüş
  `opencode/glm-5.3-flash-free`. Mutlak çalışma dizini belirt; incelemeyi
  `read-only` kipinde yap. Her işi `get_subagent` ile topla, çıktısını doğrula;
  timeout/sağlayıcı hatasını başarı sayma, ücretli modele geçme.
- Başka üyelerin sahiplik alanlarını `docs/uye1_entegrasyon.md` ile bağla;
  tamamlanmamış ajan, UI, gerçek RBAC ve insan onayı akışını tamamlandı gösterme.
