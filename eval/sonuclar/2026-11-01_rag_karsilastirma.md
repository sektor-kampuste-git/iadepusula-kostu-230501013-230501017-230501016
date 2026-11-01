# RAG karşılaştırma raporu

RAG geliştirme ve karşılaştırma seti; nihai karar doğruluğu veya bağımsız insan testi değildir.

Sorgu sayısı: **44 / 44**. Etiket durumu: `{'ai_taslak': 44}`. Koşum: `complete`.

Hazırlık süresi sorgu gecikmesine katılmaz. Tokenlar sağlayıcının bildirdiği değerlerdir; eksik kullanım bilgisi sıfır maliyet sayılmaz. USD maliyeti hesaplanmadı.

| Yöntem | Hit@k | Recall@k | Precision@k | MRR@k | nDCG@k | Tamamlanan | Sorgu p95 (ms) | API çağrısı | Bildirilen toplam token |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lexical (k=3) | 97.1% | 95.7% | 34.3% | 0.91 | 0.92 | 44/44 | 0.42 | 0 | 0 |
| evren (k=3) | 97.1% | 97.1% | 35.2% | 0.94 | 0.95 | 44/44 | 245.95 | 41 | 5208 |

## Boş sonuç ve hazırlık kontrolleri

Açık madde koruması ile doğal konu dışı sorular ayrıdır; boş sonuç hukuki hakkın olmadığı anlamına gelmez.

| Yöntem | Madde koruması n / doğruluk | Doğal konu dışı n / doğruluk | Hazırlık (ms) | Derlem önbelleği |
| --- | --- | --- | --- | --- |
| lexical | 4 / 100.0% | 5 / 60.0% | 3.73 | disabled |
| evren | 4 / 100.0% | 5 / 60.0% | 2738.21 | stored |

## Gözlenen eksikler

### lexical

- RQ01: `ok`; kaynaklar: `['MSY-M10-F2', 'MSY-M10-F1', 'MSY-M9-F1']`; ölçümler: `{'hit_at_k': True, 'recall_at_k': 0.5, 'precision_at_k': 0.3333333333333333, 'mrr_at_k': 0.3333333333333333, 'ndcg_at_k': 0.3065735963827292}`
- RQ28: `ok`; kaynaklar: `['6502-M11-F3', '6502-M11-F1', '6502-M11-F5']`; ölçümler: `{'hit_at_k': False, 'recall_at_k': 0.0, 'precision_at_k': 0.0, 'mrr_at_k': 0.0, 'ndcg_at_k': 0.0}`
- RQ36: `ok`; kaynaklar: `['6502-M8-F2', '6502-M11-F4']`; ölçümler: `{'empty_correct': False}`
- RQ42: `ok`; kaynaklar: `['REHBER-IADE-SURE', 'MSY-M11-F1', 'MSY-M15-h']`; ölçümler: `{'empty_correct': False}`

### evren

- RQ28: `ok`; kaynaklar: `['6502-M11-F1', '6502-M11-F3', '6502-M11-F6']`; ölçümler: `{'hit_at_k': False, 'recall_at_k': 0.0, 'precision_at_k': 0.0, 'mrr_at_k': 0.0, 'ndcg_at_k': 0.0}`
- RQ36: `ok`; kaynaklar: `['6502-M8-F2', '6502-M11-F4']`; ölçümler: `{'empty_correct': False}`
- RQ42: `ok`; kaynaklar: `['REHBER-IADE-SURE', 'MSY-M11-F1', 'MSY-M15-h']`; ölçümler: `{'empty_correct': False}`
