from nautilus_trader.test_kit.stubs.data import TestDataStubs
import pytest

# Import the compiled indicator
try:
    from my_trading.indicators.future_bollinger_bands import FutureBollingerBands
except ImportError:
    pytest.fail("Could not import FutureBollingerBands. Did you compile the extension?")


class TestFutureBollingerBands:
    def test_name_returns_expected_name(self):
        # Arrange
        indicator = FutureBollingerBands(20, 2.0, 2.0, 0)

        # Act, Assert
        assert indicator.name == "FutureBollingerBands"

    def test_str_repr_returns_expected_string(self):
        # Arrange
        indicator = FutureBollingerBands(20, 2.0, 2.0, 5)

        # Act, Assert
        # By default Indicator.__repr__ uses name and params
        # Our params are [period, k_upper, k_lower, pred]
        # Floats might format differently, let's just check standard repr behavior
        assert str(indicator) == "FutureBollingerBands(20, 2.0, 2.0, 5)"

    def test_properties_after_instantiation(self):
        # Arrange
        indicator = FutureBollingerBands(20, 2.0, 2.0, 10)

        # Act, Assert
        assert indicator.period == 20
        assert indicator.k_upper == 2.0
        assert indicator.k_lower == 2.0
        assert indicator.pred == 10
        assert indicator.upper == 0
        assert indicator.lower == 0
        assert indicator.middle == 0

    def test_initialized_with_required_inputs_returns_true(self):
        # Arrange
        indicator = FutureBollingerBands(5, 2.0, 2.0, 0)

        # Act
        for _ in range(5):
            indicator.update_raw(1.0)

        # Assert
        assert indicator.initialized is True

    def test_handle_bar_updates_indicator(self):
        # Arrange
        indicator = FutureBollingerBands(20, 2.0, 2.0, 0)
        bar = TestDataStubs.bar_5decimal()

        # Act
        for _ in range(20):
            indicator.handle_bar(bar)

        # Assert
        assert indicator.has_inputs
        assert indicator.initialized
        # Logic is SMA(20) of first update which is just the value
        assert indicator.middle == pytest.approx(1.00003, abs=0.00001)

    def test_standard_behavior_pred_0(self):
        """With pred=0, should behave effectively like standard BB behavior."""
        # Arrange
        indicator = FutureBollingerBands(5, 2.0, 2.0, 0)
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]

        # Act
        for p in prices:
            indicator.update_raw(p)

        # Assert
        # Window: [10, 20, 30, 40, 50]
        # Mean: 30.0
        # Std: 14.1421356
        assert indicator.initialized
        assert indicator.middle == 30.0
        assert round(indicator.upper, 4) == 58.2843
        assert round(indicator.lower, 4) == 1.7157

    def test_prediction_behavior_pred_1(self):
        """With pred=1, should repeat the last price once in the window."""
        # Arrange
        indicator = FutureBollingerBands(5, 2.0, 2.0, 1)
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]

        # Act
        for p in prices:
            indicator.update_raw(p)

        # Assert
        # Expected Window for Pred=1: [20, 30, 40, 50, 50]
        # Mean: 38.0
        # Std: 11.661903 (approx)
        assert indicator.initialized
        assert indicator.middle == 38.0
        assert round(indicator.upper, 4) == 61.3238
        assert round(indicator.lower, 4) == 14.6762

    def test_reset_successfully_returns_indicator_to_fresh_state(self):
        # Arrange
        indicator = FutureBollingerBands(5, 2.0, 2.0, 0)
        for _ in range(5):
            indicator.update_raw(1.0)

        # Act
        indicator.reset()

        # Assert
        assert not indicator.initialized
        assert indicator.upper == 0
        assert indicator.middle == 0
        assert indicator.lower == 0
