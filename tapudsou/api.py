from __future__ import annotations

"""Innovorder API client used by Tapudsou."""

from dataclasses import dataclass
from typing import Final

import requests

from .config import API_BASE_URL, BRAND_ID


class InnovorderAPIError(Exception):
    """Raised when the Innovorder API returns an unexpected response."""


@dataclass
class AuthContext:
    """Authentication context returned by the login endpoint.

    Attributes:
        access_token: Bearer token used to authenticate subsequent requests.
        customer_id: Identifier of the authenticated customer.
    """

    access_token: str
    customer_id: int


class InnovorderClient:
    """Minimal typed client for the subset of Innovorder endpoints Tapudsou uses."""

    _LOGIN_PATH: Final[str] = "/oauth/login"
    _BALANCE_PATH_TEMPLATE: Final[str] = "/customers/{customer_id}/balance"

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        brand_id: int = BRAND_ID,
        session: requests.Session | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL of the Innovorder API.
            brand_id: Brand identifier for the Dupont Restauration instance.
            session: Optional reusable :class:`requests.Session`. If omitted, a
                new session is created internally.
            timeout_seconds: Network timeout in seconds for HTTP requests.
        """

        self._base_url = base_url.rstrip("/")
        self._brand_id = brand_id
        self._session = session or requests.Session()
        self._timeout = timeout_seconds

    def login(self, username: str, password: str) -> AuthContext:
        """Authenticate the user and return an authentication context.

        Args:
            username: Innovorder username (email).
            password: Innovorder password.

        Returns:
            An :class:`AuthContext` with an access token and customer identifier.

        Raises:
            InnovorderAPIError: If the API response is unsuccessful or has an
                unexpected shape.
        """

        url = f"{self._base_url}{self._LOGIN_PATH}"
        payload = {
            "username": username,
            "password": password,
            "rememberMe": False,
            "grant_type": "password",
            "brandId": self._brand_id,
        }

        try:
            response = self._session.post(url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise InnovorderAPIError("Unable to reach Innovorder login endpoint.") from exc
        except ValueError as exc:
            raise InnovorderAPIError("Invalid JSON payload from Innovorder login endpoint.") from exc

        try:
            access_token = str(data["access_token"])
            customer_id = int(data["data"]["customer"]["customerId"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InnovorderAPIError("Unexpected structure in Innovorder login response.") from exc

        return AuthContext(access_token=access_token, customer_id=customer_id)

    def get_balance_cents(self, auth: AuthContext) -> int:
        """Retrieve the customer's balance in cents.

        Args:
            auth: Authentication context returned by :meth:`login`.

        Returns:
            The current balance in cents.

        Raises:
            InnovorderAPIError: If the API response is unsuccessful or malformed.
        """

        path = self._BALANCE_PATH_TEMPLATE.format(customer_id=auth.customer_id)
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {auth.access_token}"}

        try:
            response = self._session.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise InnovorderAPIError("Unable to reach Innovorder balance endpoint.") from exc
        except ValueError as exc:
            raise InnovorderAPIError("Invalid JSON payload from Innovorder balance endpoint.") from exc

        try:
            balance_cents = int(data["data"]["customerBalance"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InnovorderAPIError("Unexpected structure in Innovorder balance response.") from exc

        return balance_cents

