"""App Runner entrypoint — sets backend path and starts uvicorn."""
from __future__ import annotations

import os
import sys
import traceback


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    backend = os.path.join(root, "backend")
    os.chdir(backend)
    if backend not in sys.path:
        sys.path.insert(0, backend)

    port = int(os.getenv("PORT", "8080"))
    print(f"[startup] cwd={os.getcwd()} port={port}", flush=True)

    try:
        from app.core.config import get_settings

        settings = get_settings()
        print(
            f"[startup] settings ok debug={settings.debug} "
            f"lightweight={settings.lightweight_predictions}",
            flush=True,
        )
    except Exception:
        traceback.print_exc()
        raise SystemExit(1) from None

    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
