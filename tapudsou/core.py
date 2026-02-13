from __future__ import annotations

"""Core orchestration logic for Tapudsou."""

import argparse
from typing import Sequence

import keyring

from .api import InnovorderAPIError, InnovorderClient
from .config import SERVICE_ID, load_user_config
from .notify import notify_low_balance, notify_password_missing


def run_check(username: str, threshold_eur: float) -> int:
    """Run a single balance check for the given user.

    Args:
        username: Innovorder username (email).
        threshold_eur: Alert threshold in euros. If the account balance is
            strictly below this value, a notification will be triggered.

    Returns:
        An integer exit code compatible with :func:`sys.exit`:

        * ``0`` – execution succeeded.
        * ``1`` – no password found in keyring.
        * ``2`` – error while communicating with the Innovorder API.
    """

    config = load_user_config()
    language = config.language

    password = keyring.get_password(SERVICE_ID, username)
    if not password:
        notify_password_missing(username=username, language=language)
        return 1

    client = InnovorderClient()
    try:
        auth = client.login(username=username, password=password)
        balance_cents = client.get_balance_cents(auth)
    except InnovorderAPIError as exc:
        # For scheduled runs, stderr/stdout are already redirected to log files
        # by launchd/systemd; the textual message is usually enough.
        print(f"Tapudsou: {exc}")
        return 2

    balance_eur = float(balance_cents) / 100.0
    if balance_eur < threshold_eur:
        notify_low_balance(
            balance_eur,
            threshold_eur,
            language=language,
        )

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point used by both the top-level script and ``python -m tapudsou``."""

    parser = argparse.ArgumentParser(
        prog="tapudsou",
        description="Monitor your Innovorder lunch card balance and alert when low.",
    )
    parser.add_argument(
        "username",
        help="Innovorder username (email) used for the lunch card.",
    )
    parser.add_argument(
        "threshold",
        type=float,
        help="Account balance in € below which to alert.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_check(username=args.username, threshold_eur=args.threshold)


if __name__ == "__main__":
    raise SystemExit(main())

