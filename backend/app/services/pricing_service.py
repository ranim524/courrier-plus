"""Physical-mail pricing engine for Courrier+.

Courrier+ actually prints the uploaded PDF, puts it in an envelope, and sends
it as physical registered mail. The price therefore reflects a real physical
mail service rather than a purely digital delivery:

    PDF pages -> physical sheets (simplex/duplex) -> paper weight + envelope
    weight -> estimated postal weight -> weight-bracket postage
    + printing cost + paper cost + envelope cost + registered-mail fee
    + optional acknowledgment-of-receipt fee + delivery/logistics fee
    + Courrier+ service fee
    = final total

"Poids estimé" (estimated weight), not "poids réel": it is derived from the
configured paper/envelope weight model below, not weighed on an actual scale.
The postal tariff values are prototype defaults inspired by the Tunisian
Post's internal-letter tariff and should be verified before real production
use (see docs/security.md for the full legal/certification disclaimer).

All monetary and weight values use Decimal, never float, rounded to 3 decimal
places (Tunisian dinar prices are expressed in millimes: 1 TND = 1000 millimes).
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from math import ceil

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

settings = get_settings()

# ---------------------------------------------------------------------------
# Centralized pricing configuration. Not read from .env: this is structured
# domain/tariff data, not a deployment-varying scalar. These are INITIAL
# PROTOTYPE DEFAULTS, not official market prices -- an admin settings screen
# to edit them is the natural next step (see docs/deployment.md); until then,
# change them here only.
# ---------------------------------------------------------------------------

PRINTING_MODES = ("black_and_white", "color")
DEFAULT_PRINTING_MODE = "black_and_white"
PRINTING_COST_BW_PER_PAGE = Decimal("0.150")
PRINTING_COST_COLOR_PER_PAGE = Decimal("0.300")  # placeholder default, no color UI yet
PRINTING_COST_PER_PAGE: dict[str, Decimal] = {
    "black_and_white": PRINTING_COST_BW_PER_PAGE,
    "color": PRINTING_COST_COLOR_PER_PAGE,
}

PRINTING_SIDES = ("single", "double")
DEFAULT_PRINTING_SIDES = "single"

PAPER_TYPE = "A4"
PAPER_WEIGHT_GSM = 80
# An A4 sheet is ~0.06237 m²; 80 gsm x 0.06237 m² ~= 4.99g, rounded to 5g.
PAPER_WEIGHT_PER_SHEET_G = Decimal("5.000")
PAPER_COST_PER_SHEET = Decimal("0.050")

ENVELOPE_WEIGHT_G = Decimal("10.000")
ENVELOPE_COST = Decimal("0.500")

REGISTERED_MAIL_FEE = Decimal("3.000")
ACKNOWLEDGMENT_FEE = Decimal("2.500")

# Not a specific courier's real price -- a configurable placeholder. Currently
# 0 because delivery is treated as included in the postal tariff for the
# prototype. The architecture (a single configurable value here) is ready for
# an admin to later split this by zone/speed/partner without touching callers.
DELIVERY_FEE = Decimal("0.000")

COURRIER_PLUS_SERVICE_FEE = Decimal("1.000")

MAX_WEIGHT_G = Decimal("2000.000")

# Official Tunisian internal-letter postal tariff (prototype default values --
# verify against the current official tariff before real production use).
# Brackets are contiguous inclusive integer-gram ranges: a weight belongs to
# the bracket where min_weight_g <= weight <= max_weight_g.
POSTAL_TARIFFS: list[dict] = [
    {"min_weight_g": 0, "max_weight_g": 20, "postage": Decimal("0.750")},
    {"min_weight_g": 21, "max_weight_g": 100, "postage": Decimal("1.200")},
    {"min_weight_g": 101, "max_weight_g": 250, "postage": Decimal("1.500")},
    {"min_weight_g": 251, "max_weight_g": 500, "postage": Decimal("2.000")},
    {"min_weight_g": 501, "max_weight_g": 1000, "postage": Decimal("2.500")},
    {"min_weight_g": 1001, "max_weight_g": 2000, "postage": Decimal("3.500")},
]

MILLIME = Decimal("0.001")


def _round_millimes(value: Decimal) -> Decimal:
    return value.quantize(MILLIME, rounding=ROUND_HALF_UP)


def _bracket_label(bracket: dict) -> str:
    return f"{bracket['min_weight_g']}-{bracket['max_weight_g']}g"


@dataclass
class PricingBreakdown:
    page_count: int
    sheet_count: int
    printing_mode: str
    printing_sides: str
    paper_weight_g: Decimal
    envelope_weight_g: Decimal
    estimated_weight_g: Decimal
    weight_bracket: str
    printing_cost: Decimal
    paper_cost: Decimal
    envelope_cost: Decimal
    postal_postage: Decimal
    registered_mail_fee: Decimal
    acknowledgment_of_receipt: bool
    acknowledgment_fee: Decimal
    delivery_fee: Decimal
    service_fee: Decimal
    total: Decimal
    currency: str

    def to_dict(self) -> dict:
        return {
            "page_count": self.page_count,
            "sheet_count": self.sheet_count,
            "printing_mode": self.printing_mode,
            "printing_sides": self.printing_sides,
            "paper_weight_g": str(self.paper_weight_g),
            "envelope_weight_g": str(self.envelope_weight_g),
            "estimated_weight_g": str(self.estimated_weight_g),
            "weight_bracket": self.weight_bracket,
            "printing_cost": str(self.printing_cost),
            "paper_cost": str(self.paper_cost),
            "envelope_cost": str(self.envelope_cost),
            "postal_postage": str(self.postal_postage),
            "registered_mail_fee": str(self.registered_mail_fee),
            "acknowledgment_of_receipt": self.acknowledgment_of_receipt,
            "acknowledgment_fee": str(self.acknowledgment_fee),
            "delivery_fee": str(self.delivery_fee),
            "service_fee": str(self.service_fee),
            "total": str(self.total),
            "currency": self.currency,
        }


def _weight_bracket_for(weight_g: Decimal) -> dict:
    for bracket in POSTAL_TARIFFS:
        if bracket["min_weight_g"] <= weight_g <= bracket["max_weight_g"]:
            return bracket
    # Unreachable: callers already reject weight_g > MAX_WEIGHT_G before this
    # is called, and POSTAL_TARIFFS covers [0, MAX_WEIGHT_G] with no gaps.
    raise ValidationAppError(
        f"Le poids estimé dépasse la limite maximale de {MAX_WEIGHT_G} g."
    )


def calculate_letter_price(
    page_count: int,
    printing_mode: str = DEFAULT_PRINTING_MODE,
    printing_sides: str = DEFAULT_PRINTING_SIDES,
    acknowledgment_of_receipt: bool = False,
) -> PricingBreakdown:
    if page_count < 1:
        raise ValidationAppError("Le document doit contenir au moins une page.")
    if printing_mode not in PRINTING_COST_PER_PAGE:
        raise ValidationAppError(f"Mode d'impression invalide : {printing_mode}")
    if printing_sides not in PRINTING_SIDES:
        raise ValidationAppError(f"Mode recto/verso invalide : {printing_sides}")

    sheet_count = page_count if printing_sides == "single" else ceil(page_count / 2)

    paper_weight_g = sheet_count * PAPER_WEIGHT_PER_SHEET_G
    envelope_weight_g = ENVELOPE_WEIGHT_G
    estimated_weight_g = paper_weight_g + envelope_weight_g

    if estimated_weight_g > MAX_WEIGHT_G:
        raise ValidationAppError(
            f"Le document est trop volumineux une fois imprimé (poids estimé "
            f"{estimated_weight_g}g pour un maximum de {MAX_WEIGHT_G}g). "
            f"Réduisez le nombre de pages ou activez l'impression recto-verso."
        )

    bracket = _weight_bracket_for(estimated_weight_g)

    printing_cost = _round_millimes(page_count * PRINTING_COST_PER_PAGE[printing_mode])
    paper_cost = _round_millimes(sheet_count * PAPER_COST_PER_SHEET)
    envelope_cost = ENVELOPE_COST
    postal_postage = bracket["postage"]
    registered_mail_fee = REGISTERED_MAIL_FEE
    acknowledgment_fee = ACKNOWLEDGMENT_FEE if acknowledgment_of_receipt else Decimal("0.000")
    delivery_fee = DELIVERY_FEE
    service_fee = COURRIER_PLUS_SERVICE_FEE

    total = _round_millimes(
        printing_cost
        + paper_cost
        + envelope_cost
        + postal_postage
        + registered_mail_fee
        + acknowledgment_fee
        + delivery_fee
        + service_fee
    )

    return PricingBreakdown(
        page_count=page_count,
        sheet_count=sheet_count,
        printing_mode=printing_mode,
        printing_sides=printing_sides,
        paper_weight_g=paper_weight_g,
        envelope_weight_g=envelope_weight_g,
        estimated_weight_g=estimated_weight_g,
        weight_bracket=_bracket_label(bracket),
        printing_cost=printing_cost,
        paper_cost=paper_cost,
        envelope_cost=envelope_cost,
        postal_postage=postal_postage,
        registered_mail_fee=registered_mail_fee,
        acknowledgment_of_receipt=acknowledgment_of_receipt,
        acknowledgment_fee=acknowledgment_fee,
        delivery_fee=delivery_fee,
        service_fee=service_fee,
        total=total,
        currency=settings.currency,
    )
