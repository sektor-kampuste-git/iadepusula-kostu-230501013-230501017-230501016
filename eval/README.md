# Değerlendirme

`evaller.json`: 18 standart, 6 sınır, 6 adversarial = 30 sentetik geliştirme vakası.
Her etiketi AI taslağıdır; insan incelemesi henüz yapılmadı. Boş insan etiketi
veya örnek PDF sonucu, gerçek insan değerlendirmesi gibi sunulmaz.

```powershell
.venv\Scripts\python.exe -m eval.eval_kosucu
```

Varsayılan koşum ağsızdır. Araç sonuçlarını, beklenen kaynağın ilk üçte
bulunmasını, uyarıları, dört çağrı sınırını ve zorunlu insan onayı bayrağını
ölçer. `kaynak_hit_at_3`, kaynak beklentisi olan 20 vakada en az bir beklenen
parçanın bulunma oranıdır; tüm ilgili kaynakların getirildiği anlamına gelmez.
Nihai karar doğruluğu, gerekçe sadakati, model güvenliği veya insan kalibrasyonu
ölçtüğü iddia edilmez. Başarısız vakalar rapordan çıkarılmaz.

Varsayılan çıkış kodu, bütün vakaların geçmesini gerektirir. CI, dokümanın
hedefiyle uyumlu `--min-pass-rate 0.85` eşiğini açıkça belirtir. Eşik, rapordaki
başarısız vakaları gizlemez. Rapor `artifacts/eval.json` dosyasındadır.

## Tam ajan entegrasyonu

```powershell
.venv\Scripts\python.exe -m eval.eval_kosucu --predictor src.agent:predict_for_eval
```

`src.agent:predict_for_eval` ortak entegrasyona bağlıdır; gerçek model çağrısı
açıkça seçilmelidir. Hazır kanıt run_packet ile bir kez kullanılır. Aday fonksiyon bir
**etiketsiz `PredictorInput`** almalı, `eval/contracts.py` içindeki `AgentPrediction` şemasını
karşılayan dict/model döndürmelidir. Anahtar gerekebilen bu yol yalnız açıkça
seçildiğinde çalışır. Taslak karar uyumu, kaynak doğrulama ve şema kontrolleri
raporlanır; insan kararı doğruluğu olarak etiketlenmez.

`PredictorInput` alanları: `id`, `siparis_no`, maskelenmiş `basvuru`,
`basvuru_tarihi`, `kanit_paketi`. `beklenen` ve `taslak_karar` ajana verilmez.
Bu düzeltme, ilk sürümdeki cevap sızıntısını giderir. Bu bir süreç izolasyonu
değildir; aynı dosyalara erişen kötü niyetli bir değerlendirilenin veri setini
okumasını engellemez. Bağımsız test seti hâlâ gereklidir.

Rapor sürümü 2, `bilesen_gecen` ile `ajan_gecen` sayılarını ayrı tutar. Ajan
şema/API hatası verse bile bileşen kontrolleri kaybolmaz. Kaynak hit@3 paydası,
kaynak beklenen **tüm** vakalardır; hatalı vakalar paydadan düşmez. Hata aşaması,
hata sınıfı ve hata süresi raporlanır; sağlayıcının ham hata metni yayımlanmaz.
Boş, çelişkili veya yazım hatalı beklentiler veri yüklenirken reddedilir.

## Gerçek hakem kalibrasyonu

En az 10 ayrı vaka için ekip, gerçek model cevabını görüp bağımsız insan skoru
vermelidir. Ardından hakem modeli aynı cevapları puanlamalıdır. JSONL kayıtları:

```json
{"id":"V01","human_score":1,"judge_score":1,"reviewer":"gerçek-etiketleyen-kodu"}
```

Bu satır **biçim örneğidir**, ölçülmüş insan kaydı değildir.

```powershell
.venv\Scripts\python.exe -m eval.calibration artifacts\gercek_incelemeler.jsonl
```

Hesaplayıcı yüzde uyum ve Cohen kappa döndürür; tek sınıfta kappa tanımsızsa
`null` verir. Eksik insan skoru, eksik etiketleyen ve 10'dan az kayıt reddedilir.
Kullanılmış geliştirme setinin yanında ayrıca görülmemiş test seti hazırlanmalıdır.
