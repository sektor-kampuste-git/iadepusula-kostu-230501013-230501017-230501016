# Depo otomasyonu

Bu dosya README olarak adlandırılmaz: GitHub .github/README dosyasını kökteki
ürün README'sinden önce gösterir. Ana vitrin kökteki README.md'dir.

workflows/ci.yml; PR'larda ve main/develop push'larında Python 3.11/3.12/3.14
için biçim/kod, sır, belge, test, bileşen eval, ağsız demo ve wheel kontrolü yapar.
Gerçek model anahtarı kullanılmaz. artifacts raporları çalıştırma kanıtıdır.

Başarısız kontrol atlanarak yeşil gösterilmez. Yeşil CI, gerçek model kalibrasyonu,
hukuki uyum veya insan ekip incelemesi anlamına gelmez.
[Geliştirme düzeni](../docs/ekip_calisma_rehberi.md).
