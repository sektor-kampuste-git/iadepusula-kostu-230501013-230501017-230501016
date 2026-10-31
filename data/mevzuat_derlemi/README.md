# Mevzuat derlemi: seçili pasajlar

Erişim/kürasyon tarihi: **31 Ekim 2026**. Bu, bütün mevzuatın konsolide kopyası
değildir. Hukuk uzmanı onayı beklenmektedir.

| Dosya | Kapsam | Tür |
| --- | --- | --- |
| `6502.json` | 6502 Madde 8–12, fıkra düzeyinde 17 pasaj | Kanun |
| `mesafeli_sozlesmeler.json` | MSY 9, 10, seçili 11 fıkraları ve 15/1 a–h bentleri, 19 pasaj | Yönetmelik |
| `ticaret_rehberi_2026.json` | Elektronik ürünler, kargo, iade süresi ve taşımada hasar, 4 pasaj | Resmî rehber |

Kaynaklar:

- [Bakanlığın 2023 mevzuat kitabı](https://tuketici.ticaret.gov.tr/data/5e81982d13b876a1b04c7a42/2023-6502%20Say%C4%B1l%C4%B1%20T%C3%BCketicinin%20Korunmas%C4%B1%20Hakk%C4%B1nda%20Kanun.pdf).
- [Bakanlığın güncel mesafeli sözleşme rehberi](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/mesafeli-sozlesmeler-hakkinda-bilgilendirme).
- [Bakanlığın ayıplı mal/hizmet rehberi](https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/ayipli-mal-ve-hizmetler-hakkinda-bilgilendirme): çapraz kontrol kaynağı.
- [2026 parasal sınır tebliği Madde 3](https://mevzuat.adalet.gov.tr/mevzuat/350486)
  ve [Bakanlık bilgilendirmesi](https://ticaret.gov.tr/tuketici/tuketici-hakem-heyetleri/tuketici-hakem-heyetlerine-iliskin-bilgilendirme-metni).

Kitaptan yalnız seçili hükümler alınmıştır. 2023 baskısının eski MSY 12/13 ve
elektronik ürünleri cayma istisnası gösteren 15/1-i metni aktarılmamıştır.
İade ve kargo sürelerindeki güncel açıklamalar rehber olarak açıkça işaretlidir;
rehber alıntısına kanun madde numarası uydurulmaz.

`metin`: PDF sayfa üst/alt bilgileri ve editoryal değişiklik dipnotları temizlenmiş,
boşlukları normalleştirilmiş fıkra/bent. Yasal sözcükler özetlenmez.
`baglam`: MSY 15'in genel koşulu; bent tek başına değerlendirilmemelidir.
`kaynak_sha256`: indirilen asıl PDF/HTML dosyasının özeti; alıntının değil.
Derlemin tamamının parmak izi eval raporunda ayrıca bulunur.

`gecerli_baslangic` bu **2026 derlem senaryosunun** destek başlangıcıdır;
kanunun ilk yürürlük tarihi olduğu iddiası değildir. `gecerli_bitis=null`,
yürürlükten kalkmadığının geleceğe yönelik garantisi değildir. Çalışma anında
mevzuat değişiklikleri otomatik izlenmez.

## Yeniden üretim

`scripts/build_corpus.py`, yerelde indirilen kaynakları `.local/` altında bekler.
Kaynak indirme yan etkisi yoktur. `ministry-book.pdf`, bu PDF'nin pypdf ile
sayfa etiketli `ministry-book.txt` çıkarımı, rehberin `ministry-distance.html`
ve temizlenmiş `ministry-distance.txt` girdileri kullanılır. Yeni kaynak
sürümünde bu seçimi uzmanla tekrar doğrulayın; tarih/SHA ve regresyon
sonuçlarını güncelleyin. Kaynak PDF'ler ve geçici dosyalar Git'e eklenmez.
