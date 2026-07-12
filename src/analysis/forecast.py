"""Forecasting module — linear and exponential trend projection."""

import numpy as np
from scipy import stats


def linear_forecast(
    x_values: list[float],
    y_values: list[float],
    forecast_periods: int = 5,
) -> dict:
    """Simple linear regression forecast.

    Args:
        x_values: Independent variable (e.g., years as floats).
        y_values: Dependent variable.
        forecast_periods: Number of periods to forecast forward.

    Returns:
        Dict with fitted values, forecast, and model stats.
    """
    x = np.array(x_values)
    y = np.array(y_values)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Fitted values
    fitted = slope * x + intercept

    # Forecast
    last_x = x[-1]
    step = x[1] - x[0] if len(x) > 1 else 1
    forecast_x = [last_x + step * (i + 1) for i in range(forecast_periods)]
    forecast_y = [slope * fx + intercept for fx in forecast_x]

    # Confidence intervals (95%)
    residuals = y - fitted
    residual_std = np.std(residuals, ddof=2)
    ci_multiplier = 1.96

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_value ** 2,
        "p_value": p_value,
        "std_err": std_err,
        "fitted": fitted.tolist(),
        "forecast_x": forecast_x,
        "forecast_y": forecast_y,
        "forecast_ci_lower": [fy - ci_multiplier * residual_std for fy in forecast_y],
        "forecast_ci_upper": [fy + ci_multiplier * residual_std for fy in forecast_y],
    }


def exponential_forecast(
    x_values: list[float],
    y_values: list[float],
    forecast_periods: int = 5,
) -> dict:
    """Exponential growth forecast (log-linear regression).

    Transforms y → log(y) for linear fit, then exponentiates.
    """
    y_log = np.log(np.maximum(np.array(y_values), 1e-10))
    result = linear_forecast(x_values, y_log.tolist(), forecast_periods)

    return {
        "cagr": np.exp(result["slope"]) - 1,
        "r_squared": result["r_squared"],
        "fitted": np.exp(result["fitted"]).tolist(),
        "forecast_x": result["forecast_x"],
        "forecast_y": np.exp(result["forecast_y"]).tolist(),
        "forecast_ci_lower": np.exp(result["forecast_ci_lower"]).tolist(),
        "forecast_ci_upper": np.exp(result["forecast_ci_upper"]).tolist(),
    }
