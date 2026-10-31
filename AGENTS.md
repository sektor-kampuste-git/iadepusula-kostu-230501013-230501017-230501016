# İadePusula geliştirme kuralları

- Kullanıcının rolü Üye 1: RAG, derlem, deterministik araçlar ve eval birincil kapsamdır.
- Geliştirme `develop` üzerinden yürür; `main` doğrulanmış sürümü barındırır.
  Mevcut commit geçmişini koru; force push yapma.
- `evrenkey.txt`, `.env`, kaynak PDF ve `.local/` gizli/yerel girdilerdir.
  Anahtarı hiçbir çıktıya, test fixture'ına, prompt'a veya commit'e koyma.
- PDF'teki ölçüm/teslim örneklerini gerçek sonuç olarak kopyalama.
- Para için Decimal, tarihler için açık ISO takvim tarihi kullan. Ayıplı mal ile
  cayma süresini ayrı tut. Kesin hukuki karar ve ödeme işlemi uygulama.
- Kaynak metni, URL, madde ve istekte getirilen chunk kimliğini birlikte doğrula.
- Değişiklikten sonra `python -m pytest -q`, `python -m ruff check src eval scripts tests`,
  `python -m ruff format --check src eval scripts tests` ve
  `python -m eval.eval_kosucu --min-pass-rate 0.85` çalıştır.
- Ağsız testler gerçek API çağrısı yapmamalı. EVREN smoke testi yalnız açıkça
  çalıştırıldığında sentetik senaryo kullanır; tam ajan eval'i değildir.
- Delegasyon faydalıysa ücretsiz OpenCode MCP çalışanlarını kullan;
  varsayılan `opencode/deepseek-v4.1-flash-free`, ikinci görüş
  `opencode/glm-5.3-flash-free`. Mutlak çalışma dizini belirt; incelemeyi
  `read-only` kipinde yap. Her işi `get_subagent` ile topla, çıktısını doğrula;
  timeout/sağlayıcı hatasını başarı sayma, ücretli modele geçme.
- Başka üyelerin sahiplik alanlarını `docs/uye1_entegrasyon.md` ile bağla;
  tamamlanmamış ajan, UI, gerçek RBAC ve insan onayı akışını tamamlandı gösterme.
