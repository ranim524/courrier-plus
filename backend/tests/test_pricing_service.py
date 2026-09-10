from decimal import Decimal

import pytest

from app.core.exceptions import ValidationAppError
from app.services.pricing_service import calculate_price


@pytest.mark.parametrize(
    "page_count,ack,expected_weight,expected_bracket,expected_postage,expected_ack_fee,expected_total",
    [
        # 1 page, no AR: 5g -> 0-20g bracket
        (1, False, 5, "0-20g", "0.750", "0.000", "3.750"),
        # 4 pages, no AR: 20g -> still 0-20g bracket (boundary: <=20g)
        (4, False, 20, "0-20g", "0.750", "0.000", "3.750"),
        # 5 pages, no AR: 25g -> 20-100g bracket
        (5, False, 25, "20-100g", "1.200", "0.000", "4.200"),
        # 20 pages, with AR: 100g -> 20-100g bracket (boundary: <=100g)
        (20, True, 100, "20-100g", "1.200", "2.500", "6.700"),
        # 21 pages, with AR: 105g -> 100-250g bracket
        (21, True, 105, "100-250g", "1.500", "2.500", "7.000"),
        # 50 pages: 250g -> 100-250g bracket (boundary: <=250g)
        (50, False, 250, "100-250g", "1.500", "0.000", "4.500"),
        # 51 pages: 255g -> 250-500g bracket
        (51, False, 255, "250-500g", "2.000", "0.000", "5.000"),
        # 100 pages: 500g -> 250-500g bracket (boundary: <=500g)
        (100, False, 500, "250-500g", "2.000", "0.000", "5.000"),
        # 101 pages: 505g -> 500-1000g bracket
        (101, False, 505, "500-1000g", "2.500", "0.000", "5.500"),
        # 200 pages: 1000g -> 500-1000g bracket (boundary: <=1000g)
        (200, False, 1000, "500-1000g", "2.500", "0.000", "5.500"),
        # 201 pages: 1005g -> 1000-2000g bracket
        (201, False, 1005, "1000-2000g", "3.500", "0.000", "6.500"),
        # 400 pages: 2000g -> 1000-2000g bracket (boundary: <=2000g)
        (400, False, 2000, "1000-2000g", "3.500", "0.000", "6.500"),
    ],
)
def test_calculate_price_brackets(
    page_count, ack, expected_weight, expected_bracket, expected_postage, expected_ack_fee, expected_total
):
    breakdown = calculate_price(page_count, ack)
    assert breakdown.estimated_weight_g == expected_weight
    assert breakdown.weight_bracket == expected_bracket
    assert breakdown.base_postage == Decimal(expected_postage)
    assert breakdown.acknowledgment_fee == Decimal(expected_ack_fee)
    assert breakdown.total == Decimal(expected_total)
    assert breakdown.registered_fee == Decimal("3.000")


def test_acknowledgment_of_receipt_adds_exactly_2_500():
    without_ar = calculate_price(10, False)
    with_ar = calculate_price(10, True)
    assert with_ar.total - without_ar.total == Decimal("2.500")


def test_401_pages_is_rejected():
    with pytest.raises(ValidationAppError):
        calculate_price(401, False)


def test_zero_pages_is_rejected():
    with pytest.raises(ValidationAppError):
        calculate_price(0, False)


def test_total_uses_decimal_not_float():
    breakdown = calculate_price(5, True)
    assert isinstance(breakdown.total, Decimal)
    assert isinstance(breakdown.base_postage, Decimal)
    assert isinstance(breakdown.registered_fee, Decimal)
    assert isinstance(breakdown.acknowledgment_fee, Decimal)
