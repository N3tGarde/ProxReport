from __future__ import annotations

import argparse
import getpass
import os
import sys

from .config import DEFAULT_CONFIG_PATH, load_config
from .auth import _sha256_hex  # local helper
from .server import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="proxreport")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_serve = sub.add_parser("serve", help="Run HTTPS dashboard + HTTP redirect")
    p_serve.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to config.ini")
    p_serve.add_argument("--bind", default="0.0.0.0", help="Bind address")

    p_hash = sub.add_parser("hash-password", help="Generate a users.txt entry")
    p_hash.add_argument("--username", required=True)
    p_hash.add_argument(
        "--password",
        help="If omitted, you'll be prompted (recommended).",
    )
    p_hash.add_argument(
        "--salt-hex",
        help="Optional salt in hex (defaults to random 16 bytes).",
    )

    args = parser.parse_args(argv)

    if args.cmd == "serve":
        cfg = load_config(args.config)
        serve(cfg, bind=args.bind)
        return 0

    if args.cmd == "hash-password":
        password = args.password
        if password is None:
            password = getpass.getpass("Password: ")

        salt_hex = args.salt_hex
        if salt_hex is None:
            salt_hex = os.urandom(16).hex()

        salt_bytes = bytes.fromhex(salt_hex)
        sha256_hex = _sha256_hex(salt_bytes, password)
        sys.stdout.write(f"{args.username}:{salt_hex}:{sha256_hex}\n")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
