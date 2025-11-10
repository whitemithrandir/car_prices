from __future__ import annotations
import os, sys, json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Python 3.11+ için stdlib tomllib; daha eski ise tomli'yi deneyelim.
try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    import tomli as tomllib  # type: ignore

# -------------------------
# Helpers
# -------------------------
def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)

def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")

def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    return int(v) if v is not None and v.strip() else default

def _env_str(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v.strip() else default

def _expand(p: str) -> str:
    # ~ ve env var’ları genişlet, Windows/WSL fark etmeksizin normalize et
    return os.path.expandvars(os.path.expanduser(p))

# -------------------------
# Config dataclasses
# -------------------------
@dataclass
class Paths:
    app_dir: Path
    venv_dir: Path
    db_path: Path
    data_dir: Path
    logs_dir: Path

@dataclass
class Server:
    port: int
    address: str
    headless: bool
    gather_usage_stats: bool

@dataclass
class Markets:
    gold_symbol: str
    usdtry_symbol: str
    bist100_symbol: str
    btc_symbol: str

@dataclass
class AppCfg:
    title: str
    year_min: int
    year_max: int

@dataclass
class Cfg:
    paths: Paths
    server: Server
    markets: Markets
    app: AppCfg

# -------------------------
# Build config
# -------------------------
def load_cfg() -> Cfg:
    # 1) Ana config yolu: ENV ile override edilebilir

    base_dir = Path(_expand(os.getenv("CARPRICES_CONFIG_DIR", Path(__file__).resolve().parent))).resolve()
    main_toml = base_dir / "config.toml"

    data = _read_toml(main_toml)

    # 2) İsteğe bağlı lokal override (ör: config.local.toml)
    local_path = base_dir / _env_str("CARPRICES_LOCAL_CONFIG", "config.local.toml")
    data_local = _read_toml(local_path)
    # shallow merge
    for section, content in data_local.items():
        data.setdefault(section, {}).update(content or {})

    # 3) Varsayılanlar + ENV overrides
    # paths
    p = data.get("paths", {})
    app_dir   = Path(_expand(_env_str("CARPRICES_APP_DIR", p.get("app_dir", ""))))
    if not str(app_dir):
        # config.py dosyasının olduğu konumu baz al: repo kökü
        app_dir = Path(__file__).resolve().parent

    venv_dir  = Path(_expand(_env_str("CARPRICES_VENV_DIR", p.get("venv_dir", "")))) or (app_dir / "myenv")
    if not str(venv_dir):
        venv_dir = app_dir / "myenv"

    db_path   = Path(_expand(_env_str("CARPRICES_DB_PATH", p.get("db_path", ""))))
    if not str(db_path):
        db_path = app_dir / "car_prices_test.db"

    data_dir  = Path(_expand(_env_str("CARPRICES_DATA_DIR", p.get("data_dir", ""))))
    if not str(data_dir):
        data_dir = app_dir / "data"

    logs_dir  = Path(_expand(_env_str("CARPRICES_LOGS_DIR", p.get("logs_dir", ""))))
    if not str(logs_dir):
        logs_dir = app_dir / "logs"

    paths = Paths(
        app_dir=app_dir.resolve(),
        venv_dir=venv_dir.resolve(),
        db_path=db_path.resolve(),
        data_dir=data_dir.resolve(),
        logs_dir=logs_dir.resolve(),
    )

    # server
    s = data.get("server", {})
    server = Server(
        port=_env_int("CARPRICES_PORT", int(s.get("port", 8220))),
        address=_env_str("CARPRICES_ADDRESS", s.get("address", "0.0.0.0")),
        headless=_env_bool("CARPRICES_HEADLESS", bool(s.get("headless", True))),
        gather_usage_stats=_env_bool("CARPRICES_GATHER_USAGE_STATS", bool(s.get("gather_usage_stats", False))),
    )

    # markets
    m = data.get("markets", {})
    markets = Markets(
        gold_symbol=_env_str("CARPRICES_GOLD", m.get("gold_symbol", "GC=F")),
        usdtry_symbol=_env_str("CARPRICES_USDTRY", m.get("usdtry_symbol", "USDTRY=X")),
        bist100_symbol=_env_str("CARPRICES_BIST", m.get("bist100_symbol", "XU100.IS")),
        btc_symbol=_env_str("CARPRICES_BTC", m.get("btc_symbol", "BTC-USD")),
    )

    # app
    a = data.get("app", {})
    app = AppCfg(
        title=_env_str("CARPRICES_TITLE", a.get("title", "Araç Değerleri, Dolar Bazında Analiz ve Kıyaslama")),
        year_min=_env_int("CARPRICES_YEAR_MIN", int(a.get("year_min", 2010))),
        year_max=_env_int("CARPRICES_YEAR_MAX", int(a.get("year_max", 2025))),
    )

    return Cfg(paths=paths, server=server, markets=markets, app=app)

# Global config objesi:
cfg = load_cfg()

# -------------------------
# Convenience helpers
# -------------------------
def sqlite_engine_url() -> str:
    # SQLAlchemy için sqlite URL’i
    return f"sqlite:///{cfg.paths.db_path}"

def ensure_dirs():
    cfg.paths.logs_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.app_dir.mkdir(parents=True, exist_ok=True)

# Bu modül CLI benzeri çıktılar üretmek için de kullanılabilir
if __name__ == "__main__":
    ensure_dirs()
    print(json.dumps({
        "app_dir": str(cfg.paths.app_dir),
        "venv_dir": str(cfg.paths.venv_dir),
        "db_path": str(cfg.paths.db_path),
        "data_dir": str(cfg.paths.data_dir),
        "logs_dir": str(cfg.paths.logs_dir),
        "port": cfg.server.port,
        "address": cfg.server.address
    }, ensure_ascii=False, indent=2))
