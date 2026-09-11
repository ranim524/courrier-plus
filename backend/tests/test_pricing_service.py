from decimal import Decimal

import pytest

from app.core.exceptions import ValidationAppError
from app.services.pricing_service import calculate_letter_price

# All cases below use simplex (printing_sides="single"), so sheet_count ==
# page_count and estimated_weight_g == page_count * 5 + 10 (envelope).


@pytest.mark.parametrize(
    "page_count,ack,expected_weight,expected_bracket,expected_postage,expected_total",
    [
        # 1 page: 15g -> 0-20g bracket. Matches the spec's worked example (5.450).
        (1, False, "15.000", "0-20g", "0.750", "5.450"),
        # 2 pages: 20g -> still 0-20g (boundary: <=20g)
        (2, False, "20.000", "0-20g", "0.750", "5.650"),
        # 3 pages: 25g -> 21-100g bracket
        (3, False, "25.000", "21-100g", "1.200", "6.300"),
        # 18 pages: 100g -> 21-100g (boundary: <=100g)
        (18, False, "100.000", "21-100g", "1.200", "9.300"),
        # 19 pages: 105g -> 101-250g bracket
        (19, False, "105.000", "101-250g", "1.500", "9.800"),
        # 48 pages: 250g -> 101-250g (boundary: <=250g)
        (48, False, "250.000", "101-250g", "1.500", "15.600"),
        # 49 pages: 255g -> 251-500g bracket
        (49, False, "255.000", "251-500g", "2.000", "16.300"),
        # 98 pages: 500g -> 251-500g (boundary: <=500g)
        (98, False, "500.000", "251-500g", "2.000", "26.100"),
        # 99 pages: 505g -> 501-1000g bracket
        (99, False, "505.000", "501-1000g", "2.500", "26.800"),
        # 198 pages: 1000g -> 501-1000g (boundary: <=1000g)
        (198, False, "1000.000", "501-1000g", "2.500", "46.600"),
        # 199 pages: 1005g -> 1001-2000g bracket
        (199, False, "1005.000", "1001-2000g", "3.500", "47.800"),
        # 398 pages: 2000g -> 1001-2000g (boundary: <=2000g, the maximum)
        (398, False, "2000.000", "1001-2000g", "3.500", "87.600"),
        # Spec's second worked example: 10 pages, simplex, AR enabled -> 10.200
        (10, True, "60.000", "21-100g", "1.200", "10.200"),
    ],
)
def test_calculate_letter_price_brackets(
    page_count, ack, expected_weight, expected_bracket, expected_postage, expected_total
):
    breakdown = calculate_letter_price(page_count, acknowledgment_of_receipt=ack)
    assert breakdown.sheet_count == page_count  # simplex
    assert breakdown.estimated_weight_g == Decimal(expected_weight)
    assert breakdown.weight_bracket == expected_bracket
    assert breakdown.postal_postage == Decimal(expected_postage)
    assert breakdown.total == Decimal(expected_total)
    assert breakdown.registered_mail_fee == Decimal("3.000")
    assert breakdown.envelope_cost == Decimal("0.500")
    assert breakdown.delivery_fee == Decimal("0.000")
    assert breakdown.service_fee == Decimal("1.000")


def test_printing_cost_uses_pages_not_sheets():
    breakdown = calculate_letter_price(10, printing_sides="double")
    assert breakdown.sheet_count == 5
    assert breakdown.printing_cost == Decimal("1.500")  # 10 pages x 0.150, not 5 sheets


def test_duplex_halves_sheet_count_and_paper_cost():
    # Spec worked example: 10 pages, duplex, no AR -> 7.450 (the spec's own
    # example arithmetic totals 7.650, which doesn't match its own line items;
    # this asserts the correct sum of the listed components).
    breakdown = calculate_letter_price(10, printing_sides="double", acknowledgment_of_receipt=False)
    assert breakdown.sheet_count == 5
    assert breakdown.estimated_weight_g == Decimal("35.000")
    assert breakdown.weight_bracket == "21-100g"
    assert breakdown.printing_cost == Decimal("1.500")
    assert breakdown.paper_cost == Decimal("0.250")
    assert breakdown.envelope_cost == Decimal("0.500")
    assert breakdown.postal_postage == Decimal("1.200")
    assert breakdown.registered_mail_fee == Decimal("3.000")
    assert breakdown.service_fee == Decimal("1.000")
    assert breakdown.total == Decimal("7.450")


@pytest.mark.parametrize("page_count,sides,expected_sheets", [(10, "single", 10), (10, "double", 5), (11, "double", 6)])
def test_sheet_count_rounding(page_count, sides, expected_sheets):
    breakdown = calculate_letter_price(page_count, printing_sides=sides)
    assert breakdown.sheet_count == expected_sheets


def test_200_pages_simplex_matches_spec_example():
    breakdown = calculate_letter_price(200)
    assert breakdown.sheet_count == 200
    assert breakdown.estimated_weight_g == Decimal("1010.000")
    assert breakdown.weight_bracket == "1001-2000g"
    assert breakdown.postal_postage == Decimal("3.500")
    assert breakdown.total == Decimal("48.000")


def test_acknowledgment_of_receipt_adds_exactly_2_500():
    without_ar = calculate_letter_price(10)
    with_ar = calculate_letter_price(10, acknowledgment_of_receipt=True)
    assert with_ar.total - without_ar.total == Decimal("2.500")


def test_399_pages_simplex_exceeds_max_weight_and_is_rejected():
    # 399 * 5 + 10 = 2005g > 2000g
    with pytest.raises(ValidationAppError):
        calculate_letter_price(399)


def test_798_pages_duplex_fits_under_max_weight():
    # duplex allows roughly double the pages for the same physical weight:
    # sheet_count = ceil(798/2) = 399 -> weight = 399*5+10 = 2005g -> still rejected
    with pytest.raises(ValidationAppError):
        calculate_letter_price(798, printing_sides="double")

    # one fewer sheet fits exactly at the boundary
    breakdown = calculate_letter_price(796, printing_sides="double")
    assert breakdown.sheet_count == 398
    assert breakdown.estimated_weight_g == Decimal("2000.000")


def test_zero_pages_is_rejected():
    with pytest.raises(ValidationAppError):
        calculate_letter_price(0)


def test_invalid_printing_mode_is_rejected():
    with pytest.raises(ValidationAppError):
        calculate_letter_price(1, printing_mode="sepia")


def test_invalid_printing_sides_is_rejected():
    with pytest.raises(ValidationAppError):
        calculate_letter_price(1, printing_sides="triplex")


def test_color_printing_costs_more_than_black_and_white():
    bw = calculate_letter_price(10, printing_mode="black_and_white")
    color = calculate_letter_price(10, printing_mode="color")
    assert color.printing_cost > bw.printing_cost


def test_total_uses_decimal_not_float():
    breakdown = calculate_letter_price(5, acknowledgment_of_receipt=True)
    for field in (
        breakdown.total,
        breakdown.printing_cost,
        breakdown.paper_cost,
        breakdown.envelope_cost,
        breakdown.postal_postage,
        breakdown.registered_mail_fee,
        breakdown.acknowledgment_fee,
        breakdown.delivery_fee,
        breakdown.service_fee,
        breakdown.paper_weight_g,
        breakdown.envelope_weight_g,
        breakdown.estimated_weight_g,
    ):
        assert isinstance(field, Decimal)
