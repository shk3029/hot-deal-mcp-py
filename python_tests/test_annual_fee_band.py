import pytest

from app.domain.annual_fee_band import AnnualFeeBand


def test_missing_value_defaults_to_no_limit() -> None:
    assert AnnualFeeBand.from_string(None) is AnnualFeeBand.NO_LIMIT
    assert AnnualFeeBand.from_string(" ") is AnnualFeeBand.NO_LIMIT


def test_parses_supported_bands_ignoring_spaces() -> None:
    assert AnnualFeeBand.from_string("0~1만원대") is AnnualFeeBand.TEN_THOUSAND_RANGE
    assert AnnualFeeBand.from_string(" 2~3만원대 ") is AnnualFeeBand.THIRTY_THOUSAND_RANGE
    assert AnnualFeeBand.from_string("제한없음") is AnnualFeeBand.NO_LIMIT


def test_rejects_unsupported_band() -> None:
    with pytest.raises(ValueError):
        AnnualFeeBand.from_string("지원하지 않는 구간")


def test_matches_ranges() -> None:
    assert AnnualFeeBand.TEN_THOUSAND_RANGE.matches(0)
    assert AnnualFeeBand.TEN_THOUSAND_RANGE.matches(19_999)
    assert not AnnualFeeBand.TEN_THOUSAND_RANGE.matches(20_000)

    assert AnnualFeeBand.THIRTY_THOUSAND_RANGE.matches(20_000)
    assert AnnualFeeBand.THIRTY_THOUSAND_RANGE.matches(39_999)
    assert not AnnualFeeBand.THIRTY_THOUSAND_RANGE.matches(40_000)

    assert AnnualFeeBand.NO_LIMIT.matches(1_000_000)
