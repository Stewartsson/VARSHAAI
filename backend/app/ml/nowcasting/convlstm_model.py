"""
RainGuard AI - ConvLSTM Nowcasting Model

Purpose:
    0–3 hour rainfall nowcasting using spatiotemporal weather sequences.

Input convention:
    (batch, time, latitude, longitude, features)

Example:
    6 input frames × 30 minutes = 3 hours of history

Output:
    6 future rainfall grids × 30 minutes = 3 hours forecast
"""

from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import layers, models


def build_convlstm_model(
    height: int,
    width: int,
    channels: int,
    input_steps: int = 6,
    forecast_steps: int = 6,
) -> tf.keras.Model:
    """
    Build a ConvLSTM-based rainfall nowcasting model.

    Parameters
    ----------
    height:
        Number of latitude/grid rows.

    width:
        Number of longitude/grid columns.

    channels:
        Number of input weather features.

    input_steps:
        Number of historical time frames.
        Default: 6 × 30 min = 3 hours.

    forecast_steps:
        Number of forecast frames.
        Default: 6 × 30 min = 3 hours.

    Returns
    -------
    tf.keras.Model
        Compiled ConvLSTM model.
    """

    inputs = layers.Input(
        shape=(input_steps, height, width, channels),
        name="weather_sequence",
    )

    # Spatiotemporal feature extraction
    x = layers.ConvLSTM2D(
        filters=32,
        kernel_size=(3, 3),
        padding="same",
        return_sequences=True,
        activation="tanh",
        name="convlstm_1",
    )(inputs)

    x = layers.BatchNormalization(
        name="batch_norm_1"
    )(x)

    x = layers.ConvLSTM2D(
        filters=32,
        kernel_size=(3, 3),
        padding="same",
        return_sequences=True,
        activation="tanh",
        name="convlstm_2",
    )(x)

    x = layers.BatchNormalization(
        name="batch_norm_2"
    )(x)

    # Keep the temporal dimension and map each frame
    # to a rainfall field.
    x = layers.Conv3D(
        filters=16,
        kernel_size=(3, 3, 3),
        padding="same",
        activation="relu",
        name="spatiotemporal_features",
    )(x)

    # Produce one rainfall channel per time frame.
    rainfall = layers.Conv3D(
        filters=1,
        kernel_size=(1, 1, 1),
        padding="same",
        activation="relu",
        name="rainfall_output",
    )(x)

    # The ConvLSTM stack preserves the input temporal length.
    # For our default configuration input_steps == forecast_steps.
    outputs = layers.Lambda(
        lambda tensor: tensor[:, -forecast_steps:, :, :, 0],
        name="rainfall_forecast",
    )(rainfall)

    model = models.Model(
        inputs=inputs,
        outputs=outputs,
        name="RainGuard_ConvLSTM_Nowcaster",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=0.001
        ),
        loss="mse",
        metrics=[
            tf.keras.metrics.MeanAbsoluteError(name="mae")
        ],
    )

    return model


if __name__ == "__main__":
    # Architecture smoke test.
    #
    # This does NOT train the model and does NOT claim
    # real-world nowcasting performance.

    HEIGHT = 51
    WIDTH = 52
    CHANNELS = 10

    model = build_convlstm_model(
        height=HEIGHT,
        width=WIDTH,
        channels=CHANNELS,
        input_steps=6,
        forecast_steps=6,
    )

    model.summary()

    dummy_input = tf.random.normal(
        shape=(1, 6, HEIGHT, WIDTH, CHANNELS)
    )

    prediction = model(dummy_input)

    print("\nRainGuard ConvLSTM smoke test")
    print("--------------------------------")
    print("Input shape:     ", dummy_input.shape)
    print("Prediction shape:", prediction.shape)
    print("Expected shape:  ", (1, 6, HEIGHT, WIDTH))
    print("--------------------------------")

    assert prediction.shape == (
        1,
        6,
        HEIGHT,
        WIDTH,
    )

    print("STATUS: ConvLSTM architecture test PASSED")