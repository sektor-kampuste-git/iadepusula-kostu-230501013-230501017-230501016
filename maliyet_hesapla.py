"""Kullanıcının açık fiyat/token varsayımlarından model API maliyet simülasyonu.

Örnek (rakamlar sağlayıcı fiyatı değil, senaryo girdisidir):
python -m maliyet_hesapla --input-tokens 2100 --output-tokens 450 \
    --input-price 1 --output-price 2
Gerçek API çağrısı veya anahtar okuma yapmaz.
"""

import argparse
import json
import sys
from datetime import date

from src.costs import PriceCard, TokenUsage, monthly_estimate, request_cost


def main():
    """İstek başı ve aylık maliyeti, kullanılan varsayımlarla birlikte yaz."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-tokens", type=int, required=True)
    parser.add_argument("--output-tokens", type=int, required=True)
    parser.add_argument("--input-price", required=True, help="1M girdi token başına USD")
    parser.add_argument("--output-price", required=True, help="1M çıktı token başına USD")
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--requests-per-user", type=int, default=10)
    args = parser.parse_args()
    try:
        usage = TokenUsage(prompt_tokens=args.input_tokens, completion_tokens=args.output_tokens)
        price = PriceCard(
            base_url="https://assumption.invalid/v1",
            model="user-scenario",
            input_usd_per_million=args.input_price,
            output_usd_per_million=args.output_price,
            checked_on=date.today(),
            source="Komut satırından verilen açık kullanıcı varsayımı",
            kind="user_assumption",
        )
        cost = request_cost(usage, price)
        monthly = monthly_estimate(cost, args.users, args.requests_per_user)
    except ValueError:
        parser.error("Token, fiyat veya kullanıcı/istek girdileri geçersiz")
    print(
        json.dumps(
            {
                "tur": "SIMULASYON_GERCEK_OLCUM_DEGIL",
                "istek_usd": str(cost),
                "aylik_kullanici": args.users,
                "kullanici_basi_istek": args.requests_per_user,
                "aylik_usd": str(monthly),
                "tarife": price.model_dump(mode="json"),
                "token": usage.model_dump(),
                "kapsam": "Yalnız model API; barındırma, ağ ve işletim giderleri dahil değil",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
