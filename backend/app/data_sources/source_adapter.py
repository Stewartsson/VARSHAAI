"""
RainGuard AI - Source Adapter Interface

Provides a common interface for all external weather sources.

Source families:
    - INSAT satellite
    - DWR radar
    - AWS
    - ARG
    - NWP

The adapters currently provide a safe interface only.
They do NOT claim to have live access to IMD/MOSDAC data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.data_sources.schemas.weather_schema import (
    WeatherObservation,
)


class WeatherSourceAdapter(ABC):
    """
    Base interface for a RainGuard weather data source.
    """

    source_name: str = "unknown"

    @abstractmethod
    async def fetch(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[WeatherObservation]:
        """
        Fetch observations for a requested time window.

        Implementations must return normalized
        WeatherObservation objects.
        """
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Return True only when the source has the required
        authorized configuration/credentials.
        """
        raise NotImplementedError


class UnconfiguredSourceAdapter(
    WeatherSourceAdapter
):
    """
    Safe placeholder for sources whose authorized
    access has not yet been configured.

    This adapter never fabricates observations.
    """

    def __init__(
        self,
        source_name: str,
    ):
        self.source_name = source_name

    async def fetch(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[WeatherObservation]:
        raise RuntimeError(
            f"{self.source_name} is not configured. "
            "Authorized source access is required before "
            "data can be fetched."
        )

    def is_configured(self) -> bool:
        return False


class INSATAdapter(
    UnconfiguredSourceAdapter
):
    """INSAT-3D/3DR satellite adapter."""

    def __init__(self):
        super().__init__(
            "INSAT-3D/3DR"
        )


class DWRRadarAdapter(
    UnconfiguredSourceAdapter
):
    """IMD Doppler Weather Radar adapter."""

    def __init__(self):
        super().__init__(
            "DWR Radar"
        )


class AWSAdapter(
    UnconfiguredSourceAdapter
):
    """IMD Automatic Weather Station adapter."""

    def __init__(self):
        super().__init__(
            "AWS"
        )


class ARGAdapter(
    UnconfiguredSourceAdapter
):
    """IMD Automatic Rain Gauge adapter."""

    def __init__(self):
        super().__init__(
            "ARG"
        )


class NWPAdapter(
    UnconfiguredSourceAdapter
):
    """IMD/NWP model-data adapter."""

    def __init__(self):
        super().__init__(
            "NWP"
        )


def create_default_adapters() -> dict[
    str,
    WeatherSourceAdapter,
]:
    """
    Create all standard RainGuard source adapters.

    All adapters are intentionally unconfigured until
    authorized data access is available.
    """

    return {
        "satellite": INSATAdapter(),
        "radar": DWRRadarAdapter(),
        "aws": AWSAdapter(),
        "arg": ARGAdapter(),
        "nwp": NWPAdapter(),
    }


def adapter_status(
    adapters: dict[
        str,
        WeatherSourceAdapter,
    ],
) -> dict[str, dict[str, Any]]:
    """
    Return a simple status report for all adapters.
    """

    return {
        key: {
            "source": adapter.source_name,
            "configured": adapter.is_configured(),
        }
        for key, adapter in adapters.items()
    }


if __name__ == "__main__":

    adapters = create_default_adapters()

    print("\nRainGuard Source Adapter Registry")
    print("=================================")

    for key, adapter in adapters.items():
        print(
            f"{key:10s} | "
            f"{adapter.source_name:20s} | "
            f"configured={adapter.is_configured()}"
        )

    # Verify all required source families exist.
    required_sources = {
        "satellite",
        "radar",
        "aws",
        "arg",
        "nwp",
    }

    assert set(adapters.keys()) == required_sources

    # Verify no source falsely reports live access.
    assert all(
        not adapter.is_configured()
        for adapter in adapters.values()
    )

    print(
        "\nAll five source adapters registered ✓"
    )

    print(
        "No adapter claims live access ✓"
    )

    print(
        "\nSTATUS: Source adapter test PASSED"
    )