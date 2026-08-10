import pytest

from apps.dashboard.utils import format_bytes


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "0 MB"),
        (500, "500 bytes"),
        (2048, "2.0 KB"),
        (5 * 1024 * 1024, "5.0 MB"),
        (3 * 1024 * 1024 * 1024, "3.0 GB"),
    ],
)
def test_format_bytes(value, expected):
    assert format_bytes(value) == expected
