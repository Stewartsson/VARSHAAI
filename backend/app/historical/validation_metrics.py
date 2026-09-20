import numpy as np


def regression_metrics(observed, predicted):
    """
    Calculate rainfall regression metrics.

    Returns:
        MAE and RMSE.
    """

    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    if observed.shape != predicted.shape:
        raise ValueError(
            "Observed and predicted arrays "
            "must have the same shape."
        )

    mask = (
        np.isfinite(observed)
        & np.isfinite(predicted)
    )

    if not mask.any():
        raise ValueError(
            "No valid observed/predicted values."
        )

    observed = observed[mask]
    predicted = predicted[mask]

    errors = predicted - observed

    mae = float(
        np.mean(np.abs(errors))
    )

    rmse = float(
        np.sqrt(np.mean(errors ** 2))
    )

    return {
        "mae": mae,
        "rmse": rmse,
    }


def categorical_metrics(
    observed,
    predicted,
    threshold=64.5,
):
    """
    Calculate rainfall event-detection metrics.

    threshold:
        Rainfall threshold in mm.

    Returns:
        POD, FAR, CSI and confusion-matrix counts.
    """

    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    if observed.shape != predicted.shape:
        raise ValueError(
            "Observed and predicted arrays "
            "must have the same shape."
        )

    mask = (
        np.isfinite(observed)
        & np.isfinite(predicted)
    )

    if not mask.any():
        raise ValueError(
            "No valid observed/predicted values."
        )

    observed_event = (
        observed[mask] >= threshold
    )

    predicted_event = (
        predicted[mask] >= threshold
    )

    true_positive = int(
        np.sum(
            observed_event
            & predicted_event
        )
    )

    false_positive = int(
        np.sum(
            ~observed_event
            & predicted_event
        )
    )

    false_negative = int(
        np.sum(
            observed_event
            & ~predicted_event
        )
    )

    true_negative = int(
        np.sum(
            ~observed_event
            & ~predicted_event
        )
    )

    pod_denominator = (
        true_positive
        + false_negative
    )

    far_denominator = (
        true_positive
        + false_positive
    )

    csi_denominator = (
        true_positive
        + false_positive
        + false_negative
    )

    pod = (
        true_positive / pod_denominator
        if pod_denominator > 0
        else np.nan
    )

    far = (
        false_positive / far_denominator
        if far_denominator > 0
        else np.nan
    )

    csi = (
        true_positive / csi_denominator
        if csi_denominator > 0
        else np.nan
    )

    return {
        "threshold_mm": float(threshold),
        "pod": float(pod),
        "far": float(far),
        "csi": float(csi),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
    }


def evaluate(
    observed,
    predicted,
    threshold=64.5,
):
    """
    Calculate both regression and
    categorical rainfall validation metrics.
    """

    result = {}

    result.update(
        regression_metrics(
            observed,
            predicted,
        )
    )

    result.update(
        categorical_metrics(
            observed,
            predicted,
            threshold=threshold,
        )
    )

    return result


if __name__ == "__main__":
    observed = np.array(
        [10, 70, 120, 0, 200, 50]
    )

    predicted = np.array(
        [20, 80, 100, 10, 180, 90]
    )

    metrics = evaluate(
        observed,
        predicted,
        threshold=64.5,
    )

    print("RainGuard Validation Metrics")
    print("----------------------------")

    for key, value in metrics.items():
        print(f"{key}: {value}")