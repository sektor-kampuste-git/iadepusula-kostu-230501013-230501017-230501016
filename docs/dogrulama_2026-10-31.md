# Doğrulama kaydı — 31 Ekim 2026

## Yerel sonuçlar

Windows, Python 3.14.0 üzerinde:

| Kontrol | Gerçek sonuç |
| --- | --- |
| Pytest | 80 test geçti; gerçek MCP stdio istemci/sunucu testi dahil |
| Ruff kod kontrolü | Geçti |
| Ruff biçim kontrolü | Geçti |
| Bağımlılık tutarlılığı (`pip check`) | Hata yok |
| Düzenlenebilir paket kurulumu ve CLI | Kuruldu; parasal sınır komutu doğrulandı |
| Gizli bilgi taraması | Yayınlanacak dosyalarda anahtar bulunmadı |
| 30 vaka, araç/RAG bileşen eval'i | 30/30; 18 standart, 6 sınır, 6 adversarial |
| Kaynak hit@3 | Kaynak beklentisi olan 20 vakada 20/20 |
| İnsan/hakem kalibrasyonu | Yapılmadı |
| Nihai ajan karar doğruluğu | Ölçülmedi; ajan entegrasyonu henüz yok |

[Ham bileşen raporu](../eval/sonuclar/2026-10-31_bilesenler.json).
İlk geliştirme koşumu 27/30, hit@3 17/20 idi. Maskeleme alan adlarının aramayı
saptırması ve teslim öncesi/cayma ifadelerinin sıralanması düzeltildi. Aynı set
üzerinde iyileştirme yapıldı; sonuç bağımsız veya insan onaylı doğruluk değildir.

## Gerçek EVREN denemesi

API anahtarı ile `/v1/models` erişimi HTTP 200 olarak doğrulandı.
EVREN `qwen3-embedding-8b` ile derlem ve sentetik sorgu gömüldü, bellek içi
Qdrant'ta arandı; ardından `qwen3-vl-30b` ile birebir kaynak alıntısı seçen
JSON üretildi. Sağlayıcı gerçek model adını `qwen/qwen3-vl-30b-a3b` döndürdü.

Son başarılı denemede iki alıntı, getirilen parça kimlikleri ve asıl pasaj
metinleriyle birebir eşleşti. Tamamlama yanıtı 442 giriş + 209 çıkış = 651
token bildirdi; bu sayı **gömme isteklerini içermez**. Tamamlama gecikmesi
yaklaşık 2,04 saniyeydi; tüm işlem süresi veya ortalama performans iddiası değildir.
USD maliyeti hesaplanmadı ve tek isteğin gecikmesi genellenmedi.

[Anahtarsız bağlantı kanıtı](kanitlar/evren_2026-10-31.json).
Hesap bakiyesi/kota bilgisi yayımlanan rapora alınmadı.

Gerçek başarısızlıklar da kaydedildi:

1. `auto` ile bir tekrar tamamlanmış/doğrulanabilir JSON üretmedi. Bu deneme
   başarı sayılmadı. Varsayılan örnek ayar sabit modele ve JSON yanıt biçimine
   geçirildi; yarım cevaplar reddedilir ve önceki başarı kaydı geçersizleştirilir.
2. Serbest özet denemesinde model, eksik bilgilendirmeyle ilgili şartlı hükmü
   genelleştiren cümle üretti; alıntılar eşleşmesine rağmen anlam sadakati
   garanti değildi. Üye 1 smoke çıktısı birebir alıntı seçimine daraltıldı.
   Nihai yorum/karar ve insan denetimi Üye 2/3 entegrasyonuna bırakıldı.

## Ücretsiz dış inceleme

- İlk DeepSeek doküman incelemesi 180 saniyede zaman aşımına uğradı; tamamlandı
  veya onay verdi diye kaydedilmedi.
- İkinci DeepSeek incelemesi yalnız `src/tools.py` ve `src/contracts.py`
  üzerinde tamamlandı. Para büyüklüğü/duyarlılığı, tarih aralığı ve eksik
  bilgilendirmede son gün gösterimi bulguları ana ajan tarafından kontrol edilip
  düzeltildi. Çalışanın bir yıllık süreyi teslim tarihinden başlatan önerisi
  doğrudan uygulanmadı; MSY 10 hükmü ve hukuki belirsizlik korundu.

## Yeniden çalıştırma

```powershell
.venv\Scripts\python.exe -m ruff check src eval scripts tests
.venv\Scripts\python.exe -m ruff format --check src eval scripts tests
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m eval.eval_kosucu
.venv\Scripts\python.exe scripts\check_secrets.py
# Gerçek API kotası kullanır, yalnız sentetik senaryo:
.venv\Scripts\python.exe -m scripts.smoke_evren
```

GitHub CI aynı ağsız kontrolleri Python 3.12 ve 3.14 üzerinde yürütür; gerçek
sağlayıcı isteği veya API anahtarı kullanmaz. Güncel durumu repodaki Actions
sekmesi ve dal rozeti gösterir.
