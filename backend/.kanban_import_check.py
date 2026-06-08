import importlib.util

required_modules = ["fastapi", "pydantic", "pydantic_settings", "httpx"]
missing = [module for module in required_modules if importlib.util.find_spec(module) is None]
if missing:
    raise SystemExit(f"missing dependencies: {', '.join(missing)}")

import app.main

print(f"backend import ok: {app.main.app.title}")
