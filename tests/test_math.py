import pytest

from utils.math import add, divide


class TestAdd:
    def test_positive(self):
        assert add(1, 2) == 3

    def test_negative(self):
        assert add(-1, -1) == -2

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (0, 0, 0),
            (0.1, 0.2, 0.3),
            (1e10, 1e10, 2e10),
        ],
    )
    def test_param(self, a, b, expected):
        assert add(a, b) == pytest.approx(expected)


class TestDivide:
    def test_normal(self):
        assert divide(10, 2) == 5

    def test_zero_division(self):
        with pytest.raises(ValueError, match="division by zero"):
            divide(10, 0)
