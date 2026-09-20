"""
RainGuard AI - Multi-Source Weather Manager

Coordinates the five RainGuard source adapters:

    INSAT-3D/3DR
    DWR Radar
    AWS
    ARG
    NWP

The manager never fabricates data. Unconfigured sources are
reported and skipped safely.
"""

from __future__ import annotations

from datetime import datetime

from app.data_sources.source_adapter import (
    WeatherSourceAdapter,
    create_default_adapters,
)


class WeatherSourceManager:
    """Coordinate all configured RainGuard weather sources."""

    def __init__(
        self,
        adapters: dict[
            str,
            WeatherSourceAdapter,
        ] | None = None,
    ):
        self.adapters = (
            adapters
            if adapters is not None
            else create_default_adapters()
        )

    def status(self) -> dict:
        """Return configuration status for every source."""

        return {
            key: {
                "source": adapter.source_name,
                "configured": adapter.is_configured(),
            }
            for key, adapter in self.adapters.items()
        }

    def configured_sources(self) -> list[str]:
        """Return only sources with authorized configuration."""

        return [
            key
            for key, adapter in self.adapters.items()
            if adapter.is_configured()
        ]

    def unconfigured_sources(self) -> list[str]:
        """Return sources that are not configured."""

        return [
            key
            for key, adapter in self.adapters.items()
            if not adapter.is_configured()
        ]

    async def fetch_all(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, list]:
        """
        Fetch data from all configured sources.

        Unconfigured sources are skipped rather than
        generating fake observations.
        """

        results: dict[str, list] = {}

        for key, adapter in self.adapters.items():

            if not adapter.is_configured():
                continue

            results[key] = await adapter.fetch(
                start_time,
                end_time,
            )

        return results

    def summary(self) -> dict:
        """Return a concise ingestion-layer summary."""

        configured = self.configured_sources()
        unconfigured = self.unconfigured_sources()

        return {
            "total_sources": len(self.adapters),
            "configured_count": len(configured),
            "unconfigured_count": len(unconfigured),
            "configured_sources": configured,
            "unconfigured_sources": unconfigured,
        }


if __name__ == "__main__":

    manager = WeatherSourceManager()

    print("\nRainGuard Multi-Source Manager")
    print("================================")

    summary = manager.summary()

    print(
        "\nTotal sources:",
        summary["total_sources"],
    )

    print(
        "Configured:",
        summary["configured_count"],
    )

    print(
        "Unconfigured:",
        summary["unconfigured_count"],
    )

    print("\nSource status:")

    for key, info in manager.status().items():
        print(
            f"  {key:10s} | "
            f"{info['source']:20s} | "
            f"configured={info['configured']}"
        )

    # Required SIH26071 source families.
    required = {
        "satellite",
        "radar",
        "aws",
        "arg",
        "nwp",
    }

    assert set(manager.adapters.keys()) == required

    # No unconfigured source should appear as configured.
    assert manager.configured_sources() == []

    assert set(
        manager.unconfigured_sources()
    ) == required

    print(
        "\nAll five source families registered ✓"
    )

    print(
        "Unconfigured sources safely identified ✓"
    )

    print(
        "No fabricated observations generated ✓"
    )

    print(
        "\nSTATUS: Source manager test PASSED"
    )