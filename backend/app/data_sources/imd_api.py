"""
VARSHAAI - IMD API Client

Official India Meteorological Department API client.

Environment variables required:
    IMD_API_TOKEN
    IMD_JWT_TOKEN

The API key is sent using:
    x-api-key

The JWT is sent using:
    Authorization: Bearer <JWT>
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx


# ============================================================
# IMD API CONFIGURATION
# ============================================================

IMD_BASE_URL = "https://api.imd.gov.in/api/v1"


# ============================================================
# IMD API CLIENT
# ============================================================

class IMDApiClient:
    """Client for the official IMD API."""

    def __init__(
        self,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:

        # JWT token
        self.jwt_token = (
            token
            if token is not None
            else os.getenv("IMD_JWT_TOKEN")
        )

        # API key
        self.api_key = (
            api_key
            if api_key is not None
            else os.getenv("IMD_API_TOKEN")
        )

        self.timeout = timeout

    # ========================================================
    # HEADERS
    # ========================================================

    def _headers(self) -> dict[str, str]:
        """Create authentication headers for IMD."""

        headers: dict[str, str] = {
            "Accept": "application/json",
        }

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        if self.api_key:
            headers["x-api-key"] = self.api_key

        # ----------------------------------------------------
        # JWT
        # ----------------------------------------------------

        if self.jwt_token:
            headers["Authorization"] = (
                f"Bearer {self.jwt_token}"
            )

        return headers

    # ========================================================
    # COMMON GET REQUEST
    # ========================================================

    async def _get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Perform an authenticated GET request."""

        url = (
            f"{IMD_BASE_URL}/"
            f"{endpoint.lstrip('/')}"
        )

        headers = self._headers()

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:

            response = await client.get(
                url,
                params=params,
                headers=headers,
            )

            # Helpful error message
            if response.status_code != 200:
                print()
                print("===== IMD API ERROR =====")
                print("URL:", url)
                print("STATUS:", response.status_code)
                print(
                    "BODY:",
                    response.text[:1000]
                )
                print("=========================")
                print()

            response.raise_for_status()

            return response.json()

    # ========================================================
    # CURRENT WEATHER
    # ========================================================

    async def current_weather(
        self,
        station_id: Optional[str] = None,
    ) -> Any:
        """
        Get current weather observations.

        Endpoint:
            /current_wx

        Optional:
            ?id=<station_id>
        """

        params: dict[str, Any] = {}

        if station_id:
            params["id"] = station_id

        return await self._get(
            "current_wx",
            params=params,
        )

    # ========================================================
    # AWS / ARG DATA
    # ========================================================

    async def aws_data(
        self,
        station_id: Optional[str] = None,
        state_id: Optional[int] = None,
    ) -> Any:
        """
        Get AWS / ARG observations.

        Examples:

            /aws_data

            /aws_data?id=NDL

            /aws_data?sid=25
        """

        params: dict[str, Any] = {}

        if station_id:
            params["id"] = station_id

        if state_id is not None:
            params["sid"] = state_id

        return await self._get(
            "aws_data",
            params=params,
        )

    # ========================================================
    # DISTRICT NOWCAST
    # ========================================================

    async def district_nowcast(
        self,
        district_id: Optional[str] = None,
    ) -> Any:
        """
        Get district-wise nowcast information.
        """

        params: dict[str, Any] = {}

        if district_id:
            params["id"] = district_id

        return await self._get(
            "districtnowcast",
            params=params,
        )

    # ========================================================
    # STATION NOWCAST
    # ========================================================

    async def station_nowcast(
        self,
        station: Optional[str] = None,
    ) -> Any:
        """
        Get station-wise nowcast information.
        """

        params: dict[str, Any] = {}

        if station:
            params["id"] = station

        return await self._get(
            "stationnowcast",
            params=params,
        )

    # ========================================================
    # DISTRICT RAINFALL
    # ========================================================

    async def district_rainfall(
        self,
        district_id: Optional[str] = None,
    ) -> Any:
        """
        Get district rainfall information.
        """

        params: dict[str, Any] = {}

        if district_id:
            params["id"] = district_id

        return await self._get(
            "districtrainfall",
            params=params,
        )

    # ========================================================
    # RADAR
    # ========================================================

    async def radar_image(
        self,
        **params: Any,
    ) -> Any:
        """
        Access IMD radar endpoint.

        Parameters are passed directly because
        radar parameters may vary according to
        the IMD API specification.
        """

        return await self._get(
            "radar",
            params=params,
        )


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def describe_configuration() -> None:
    """Display safe IMD API configuration status."""

    jwt_configured = bool(
        os.getenv("IMD_JWT_TOKEN")
    )

    api_key_configured = bool(
        os.getenv("IMD_API_TOKEN")
    )

    print()
    print("========================================")
    print("       VARSHAAI - IMD API CONFIG")
    print("========================================")

    print(
        "Base URL:",
        IMD_BASE_URL
    )

    print(
        "JWT configured:",
        jwt_configured
    )

    print(
        "API key configured:",
        api_key_configured
    )

    if jwt_configured and api_key_configured:

        print(
            "Status: JWT + API key detected."
        )

    elif jwt_configured:

        print(
            "Status: JWT detected, API key missing."
        )

    elif api_key_configured:

        print(
            "Status: API key detected, JWT missing."
        )

    else:

        print(
            "Status: No IMD credentials configured."
        )

    print("========================================")
    print()


# ============================================================
# BASIC FILE TEST
# ============================================================

if __name__ == "__main__":

    describe_configuration()

    client = IMDApiClient()

    print(
        "Client created successfully."
    )

    print(
        "Timeout:",
        client.timeout
    )

    print(
        "Base URL:",
        IMD_BASE_URL
    )

    print(
        "STATUS: IMD API client configuration test PASSED"
    )