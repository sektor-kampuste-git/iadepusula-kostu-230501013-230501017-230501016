# Üye 2 - İlk katkı: kanıta bağlı ön inceleme şeması

Hazırlama tarihi: 31 Ekim 2026. Temel sürüm: `cfc3e2c` (Üye 1 / v0.2).
Durum: yerel geliştirme ve test; uzaktaki repoya henüz gönderilmedi.
Bu belge ilk şema paketini anlatır. Genişletilmiş v0.3 kapsamı için
`docs/uye2_entegrasyon.md` ve `docs/uye2_katki_kaydi.md` esas alınmalıdır.
Planlanan birincil sorumlu: Zeynep Zehra Kocatürk, 230501017.

Bu değişiklik Codex yardımıyla hazırlanmıştır. Zeynep kodu okuyup testleri
çalıştırdıktan ve ekip incelemesinden sonra katkı kaydını kesinleştirecektir.
İnsan incelemesi veya GitHub PR onayı henüz yapılmış gibi raporlanmaz.

## Emre'nin mevcut katkısının incelemesi

- Commit geçmişinde ilk kurulumdan `cfc3e2c` sürümüne kadar yeni geliştirmeler
  `Wrindzler` hesabında görünüyor. Kullanıcının belirttiği Üye 1 katkısı bu sürüm
  üzerinden incelendi; burada kişiye ilişkin başka hesap bilgisi varsayılmadı.
- `main` ve `develop` aynı temel commit'teydi. Repo kuralına uygun hedef dal
  `develop`; yerel katkı dalı `feat/uye2-karar-semasi`.
- Yerelde değişiklik öncesi 141 test geçti. Ruff kontrolü ve biçim kontrolü geçti.
- Ağsız araç/RAG koşucusu 30/30 geliştirme vakasını geçti; kaynak beklentili 20
  vakada hit@3 20/20. Bu set geliştirmede kullanılmıştır; etiketler `ai_taslak`tır.
- GitHub'da bu commit'in iki push çalışması da başarılı olarak görüldü.
  Kanıt: https://github.com/sektor-kampuste-git/iadepusula-kostu-230501013-230501017-230501016/actions/runs/41214076777
- RAG ve araç temeli, MCP sunucusu, atıf doğrulaması, derlem/sipariş verisi,
  bağımsız ajan için eval bağlantı noktası ve CI hazırdır.
- Tam ajan, genel model istemcisi, USD bütçe, kapsamlı güvenlik, insan onayı
  iş akışı, kullanıcı arayüzü, canlı yayın ve insan kalibrasyonu bitmiş değildir.

Bu inceleme bir hukuk denetimi veya tam sistem güvenliği raporu değildir.
Kaynakların bütün hukukî kapsamı bu katkıda yeniden doğrulanmadı.

## Bu katkının kapsamı

Yalnız dört yeni dosya ve README bağlantısı eklenir:

1. `src/schemas.py`: Pydantic taslak ve kanıta bağlı doğrulama sınırı.
2. `tests/test_schemas.py`: 45 ağsız davranış testi.
3. `scripts/demo_karar_semasi.py`: API'siz, sentetik ve elle hazırlanmış taslak demosu.
4. Bu belge: kullanım, sınırlar ve öğrenci çalışma adımları.

Üye 1'in `src/contracts.py`, `src/rag.py`, araçları veya eval alan adları
değiştirilmez. Yeni karar üreticisi bu pakette yoktur. Kullanılan durumlar mevcut
`AgentPrediction` ile aynıdır: `KABUL_ONERILIR`, `RED_ONERILIR`,
`UZMAN_INCELEMESI_GEREKLI`.

## Şema ile bağlamsal kontrolün ayrımı

`KararTaslagi`, metin, para, kaynak tekrarı, eksik bilgi ve insan incelemesi
kurallarını kontrol eder. Ancak gerçek fatura tutarını veya hangi kaynakların
bu istekte getirildiğini tek başına bilemez.

Bu yüzden model çıktısı arayüze verilmeden önce uygulama daima
`dogrula_karar_taslagi(ham, paket, retriever=rag)` çağırır. `paket`, modelin
ürettiği bir nesne değil; sunucunun Üye 1 katmanından aldığı kanıttır.
İşlev aynı derlemdeki `verify_citation` kontrolünü, yalnız istekte getirilen
kimliklere izin vererek kullanır. Kimlik, alıntı, URL, madde, belge türü, bağlam
ve sayfa metadatası mevcut sözleşmeyle eşleşmelidir.

Pydantic `model_copy(update=...)` tekrar doğrulama yapmadan nesne üretebilir.
Bu sınır, gelen nesneleri iç içe sözlüklere açıp yeniden doğrular. Kontrol
edilmemiş nesne arayüze veya eval'e doğrudan verilmemelidir.

## Doğrulanan başlıca davranışlar

- Boş veya yalnız görünmez karakter/boşluktan oluşan özet ve gerekçe kabul edilmez.
- Para float/bool olarak alınmaz; kuruş hassasiyeti, negatif ve sonsuz değerler kontrol edilir.
- Kabul/ret önerisi kaynak gerektirir. Eksik bilgi varsa uzman incelemesi gerekir.
- Uzman incelemesinde tutar `null` olmalıdır; `0`, bulunamayan tutar yerine kullanılmaz.
- İlk sürümün fatura bedeliyle sınırlı iade kapsamı dışında tutar verilemez.
  Bu bir genel hukukî tazminat sınırı iddiası değildir.
- İnsan incelemesi yalnız gerçek JSON/Python `true` değerini kabul eder.
  Bu bayrak onayın verilmiş olduğu anlamına gelmez.
- Mevcut PII örüntüleri özet, gerekçe, eksik bilgiler ve kaynaklar dahil taranır.
- Şema alanına fazladan fatura tutarı ekleyerek güvenilir fatura değiştirilemez.
- Derlemde bulunan ama bu istekte getirilmeyen kaynak kabul edilmez.
- Bilinmeyen sipariş veya engellenmiş girdi kabul/ret taslağına dönüşemez.
- Sınır hatası ham model yanıtını/PII değerini mesajına eklemez. Uygulama bu
  hata türünü yakalamalı; ham yanıt veya doğrulama ayrıntılarını kullanıcıya/loga basmamalıdır.

## Ağsız kullanım

```python
from src.evidence import hazirla_inceleme
from src.rag import MevzuatRetriever
from src.schemas import dogrula_karar_taslagi

rag = MevzuatRetriever()
paket = hazirla_inceleme(
    "SIP-2026-1001", "Gömleği iade etmek istiyorum.", "2026-10-31", retriever=rag
)
# Gerçek model istemcisi eklenene kadar elle oluşturulmuş örnek taslak.
ham = {
    "sorgu_ozeti": "Sentetik sipariş için ön inceleme istendi.",
    "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
    "gerekce": "Bu şema örneğidir; kaynakların anlamı uzman tarafından incelenmelidir.",
    "kaynaklar": [],
    "hesaplanan_iade_tutari_tl": None,
    "insan_onayi_gerekiyor_mu": True,
}
taslak = dogrula_karar_taslagi(ham, paket, retriever=rag)
eval_yaniti = taslak.eval_ciktisi()  # Mevcut AgentPrediction ile uyumlu üç alan.
rag.close()
```

## Doğrulama komutları

PowerShell'de repo kökünden:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_schemas.py -q
.\.venv\Scripts\python.exe -m scripts.demo_karar_semasi
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src eval scripts tests
.\.venv\Scripts\python.exe -m ruff format --check src eval scripts tests
.\.venv\Scripts\python.exe -m eval.eval_kosucu --min-pass-rate 0.85 --output artifacts/uye2-sema-bilesen.json
.\.venv\Scripts\python.exe scripts/check_secrets.py
```

İlk komutta bu katkının 45 testi çalışır. Bileşen eval'i karar şemasının veya
gelecekteki LLM ajanının karar doğruluğu diye sunulmaz. Yeni dosyalar mevcut
CI test komutuna otomatik dahildir; workflow'u kopyalamaya gerek yoktur.

31 Ekim 2026 tarihli bu yerel çalışma kopyasında doğrulanan sonuçlar:

- Başlangıç: 141 test başarılı.
- Üye 2 şeması: 45 yeni test başarılı; toplam 186 test başarılı.
- Tüm proje Ruff ve biçim kontrolü başarılı; 34 Python dosyası biçime uygun.
- Mevcut araç/RAG geliştirme eval'i: 30/30; insan kalibrasyonu halen yapılmadı.
- Demo: geçerli uzman inceleme taslağı ve beklenen üç engelleme görüldü.
- Yayınlanabilir dosya taraması başarılı; anahtar veya model API'si kullanılmadı.
- Bu yeni dal için GitHub CI/PR sonucu henüz yok; push sonrası ayrıca kontrol edilecek.

## Zeynep'in uygulama ve inceleme sırası

1. `src/schemas.py` içinde şema ile `dogrula_karar_taslagi` işlevinin farklı
   sorumluluklarını oku. Her doğrulayıcıya karşılık gelen testi bul.
2. Yukarıdaki ilk iki komutu kendi terminalinde çalıştır. Geçerli taslağı ve
   engellenen üç hatalı örneği incele; demo API anahtarı gerektirmez.
3. Deneme olarak kaynak kimliğini veya tutarı değiştirdiğinde hangi testin
   neden başarısız olacağını açıkla. Ardından bütün testleri çalıştır.
4. PR başlığı: `Üye 2: kanıt paketine bağlı ön inceleme şemasını ekle`.
5. PR açıklamasında kapsamı, test sonuçlarını ve kalan sınırları yaz; Codex
   yardımıyla hazırlanan kodu kendin incelediğini ancak gerçekten inceledikten sonra belirt.
6. Emre'den kaynak/atıf sözleşmesini, Beste'den arayüzün kullanacağı alanları incelemesini iste.
7. İnceleme sonrası `develop` ile birleştirin; mevcut ekip düzeni `main`e doğrudan yazmak değildir.

Yerelde hazırlanan dal otomatik commit edilmedi veya push edilmedi. Kullanıcı
kendi GitHub hesabı/kimliğiyle, anlayıp doğruladığı değişikliği kaydetmelidir.

## Bu paketten sonra

İlk şema paketinden sonra genel istemci, güvenlik sınırı, bütçeli iş akışı ve
maliyet hesabı v0.3 paketine eklendi. Gerçek sağlayıcı ve gerçek token maliyeti
denemeleri halen bekler; genişletilmiş katkı kaydı ayrı belgelerde tutulur.

Bilinen sınırlar: regex isim/adres tespitini garanti etmez; geçerli atıf gerekçenin
doğru yorumlandığını ispatlamaz; bir boolean gerçek insan onayı iş akışı değildir;
mevcut sınıflandırma/karar etiketlerinin hukuk uzmanı ve gerçek insan incelemesi
devam eder. Bu katkı bireysel veya takım için not garantisi değildir.
