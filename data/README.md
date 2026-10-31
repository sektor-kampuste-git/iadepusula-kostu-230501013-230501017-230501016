# Veri kaynakları

`siparisler_sentetik.json`: `Faker('tr_TR')`, sabit seed `20261031` ile üretilen
100 sipariş. Faker yalnız fiyat çeşitliliği sağlar. İsim, adres, TCKN, telefon,
e-posta veya IBAN alanı yoktur. Ürün adları ve özel test senaryoları elle
belirlenmiştir; gerçek müşteri kayıtları kullanılmaz.

```powershell
.venv\Scripts\python.exe scripts\generate_orders.py
```

İlk 16 kayıtta süre, belirsiz bilgi, mağaza, kargo ve parasal sınır vakaları
bulunur. Senaryolar 31 Ekim 2026 çevresine sabitlenmiştir; testler makinenin
bugünkü tarihine bağımlı değildir. Gelecek yılın resmî sınırı tahmin edilmez.

`parasal_sinirlar.json`: yalnız doğrulanmış 2026 kaydı. Para değerleri JSON
metni olarak kuruş duyarlılığıyla saklanır. Tam sınıra eşit değer “altında”
koşulunu sağlamaz. Bu, iade talebinin esası hakkında bir ret değildir.

`mevzuat_derlemi/`: kaynak ve sürüm ayrıntıları kendi README dosyasındadır.
