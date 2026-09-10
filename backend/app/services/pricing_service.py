"""Dynamic pricing engine for Courrier+.

Replaces the old flat LETTER_PRICE with a tariff modeled on the Tunisian Post
weight-based registered-mail pricing: a postage fee that depends on weight
bracket, a fixed registered-mail fee, and an optional acknowledgment-of-receipt
(accusé de réception) fee.

Courrier+ is digital, so there is no physical weight. Weight is ESTIMATED from
the number of pages of the uploaded PDF (ESTIMATED_GRAMS_PER_PAGE grams per
page). This is a Courrier+ pricing convention inspired by the Tunisian Post
tariff table — it does not represent the actual physical weight of a printed
document, and does not by itself establish legal equivalence with physical
registered mail (see docs/security.md for the full legal disclaimer).

All monetary values use Decimal, never float, and are rounded to 3 decimal
places (Tunisian dinar prices are expressed in millimes: 1 TND = 1000 millimes).
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

settings = get_settings()

# Centralized, easy-to-change pricing constants. Not read from .env: this is
# structured domain tariff data, not a deployment-varying scalar.
ESTIMATED_GRAMS_PER_PAGE = 5
MAX_PAGES = 400
MAX_WEIGHT_G = MAX_PAGES * ESTIMATED_GRAMS_PER_PAGE  # 2000g

REGISTERED_MAIL_FEE = Decimal("3.000")
ACKNOWLEDGMENT_OF_RECEIPT_FEE = Decimal("2.500")

# Official Tunisian postal weight-based tariff table. A weight belongs to a
# bracket if min_weight < weight <= max_weight (so exactly 20g falls in the
# first bracket, exactly 100g in the second, etc).
WEIGHT_BRACKETS: list[dict] = [
    {"min_weight": 0, "max_weight": 20, "postage": Decimal("0.750"), "label": "0-20g"},
    {"min_weight": 20, "max_weight": 100, "postage": Decimal("1.200"), "label": "20-100g"},
    {"min_weight": 100, "max_weight": 250, "postage": Decimal("1.500"), "label": "100-250g"},
    {"min_weight": 250, "max_weight": 500, "postage": Decimal("2.000"), "label": "250-500g"},
    {"min_weight": 500, "max_weight": 1000, "postage": Decimal("2.500"), "label": "500-1000g"},
    {"min_weight": 1000, "max_weight": 2000, "postage": Decimal("3.500"), "label": "1000-2000g"},
]

MILLIME = Decimal("0.001")


def _round_millimes(value: Decimal) -> Decimal:
    return value.quantize(MILLIME, rounding=ROUND_HALF_UP)


@dataclass
class PricingBreakdown:
    page_count: int
    estimated_weight_g: int
    weight_bracket: str
    base_postage: Decimal
    registered_fee: Decimal
    acknowledgment_of_receipt: bool
    acknowledgment_fee: Decimal
    total: Decimal
    currency: str

    def to_dict(self) -> dict:
        return {
            "page_count": self.page_count,
            "estimated_weight_g": self.estimated_weight_g,
            "weight_bracket": self.weight_bracket,
            "base_postage": str(self.base_postage),
            "registered_fee": str(self.registered_fee),
            "acknowledgment_of_receipt": self.acknowledgment_of_receipt,
            "acknowledgment_fee": str(self.acknowledgment_fee),
            "total": str(self.total),
            "currency": self.currency,
        }


def _weight_bracket_for(weight_g: int) -> dict:
    for bracket in WEIGHT_BRACKETS:
        if bracket["min_weight"] < weight_g <= bracket["max_weight"]:
            return bracket
    # Unreachable when page_count has already been validated against MAX_PAGES.
    raise ValidationAppError(
        f"Le document dépasse la limite maximale de {MAX_WEIGHT_G} g équivalents ({MAX_PAGES} pages)."
    )


def calculate_price(page_count: int, acknowledgment_of_receipt: bool) -> PricingBreakdown:
    if page_count < 1:
        raise ValidationAppError("Le document doit contenir au moins une page.")
    if page_count > MAX_PAGES:
        raise ValidationAppError(
            f"Le document dépasse la limite maximale de {MAX_WEIGHT_G} g équivalents ({MAX_PAGES} pages)."
        )

    estimated_weight_g = page_count * ESTIMATED_GRAMS_PER_PAGE
    bracket = _weight_bracket_for(estimated_weight_g)

    registered_fee = REGISTERED_MAIL_FEE
    acknowledgment_fee = ACKNOWLEDGMENT_OF_RECEIPT_FEE if acknowledgment_of_receipt else Decimal("0.000")
    total = _round_millimes(bracket["postage"] + registered_fee + acknowledgment_fee)

    return PricingBreakdown(
        page_count=page_count,
        estimated_weight_g=estimated_weight_g,
        weight_bracket=bracket["label"],
        base_postage=bracket["postage"],
        registered_fee=registered_fee,
        acknowledgment_of_receipt=acknowledgment_of_receipt,
        acknowledgment_fee=acknowledgment_fee,
        total=total,
        currency=settings.currency,
    )
