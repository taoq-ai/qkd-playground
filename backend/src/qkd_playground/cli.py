"""CLI entry point for QKD Playground."""

from __future__ import annotations

import argparse


def main() -> None:
    """Launch the QKD Playground server."""
    desc = "QKD Playground — Quantum Key Distribution simulator"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()

    import uvicorn  # noqa: TCH002

    print(f"🔐 QKD Playground starting at http://{args.host}:{args.port}")
    uvicorn.run(
        "qkd_playground.api.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
