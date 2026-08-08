"""取得スクリプトの設定。

値は環境変数、または `.analytics/config.env` から読む。
config.env は .gitignore 済みのディレクトリにあるため、リポジトリへは入らない。

    WAKA_DS_GA_CREDENTIALS   サービスアカウントのJSON鍵のパス
    WAKA_DS_GA4_PROPERTY_ID  GA4の数値プロパティID（計測ID G-XXXX とは別物）
    WAKA_DS_GSC_SITE_URL     Search Consoleの登録名
                             ドメインプロパティなら sc-domain:waka-ds.com
                             URLプレフィックスなら https://waka-ds.com/
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / ".analytics"
CONFIG_ENV = OUTPUT_ROOT / "config.env"

DEFAULT_CREDENTIALS = Path.home() / ".config" / "waka-ds-analytics" / "service-account.json"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


class ConfigError(Exception):
    """設定が足りないときに投げる。原因と対処をメッセージへ含める。"""


def _load_env_file(path: Path) -> dict[str, str]:
    """KEY=VALUE 形式の素朴なファイルを読む。# 以降はコメント。"""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass
class Config:
    credentials_path: Path
    ga4_property_id: str
    gsc_site_url: str

    @property
    def ga4_property(self) -> str:
        return f"properties/{self.ga4_property_id}"


def load_config() -> Config:
    file_values = _load_env_file(CONFIG_ENV)

    def get(key: str, default: str | None = None) -> str | None:
        return os.environ.get(key) or file_values.get(key) or default

    credentials = Path(get("WAKA_DS_GA_CREDENTIALS", str(DEFAULT_CREDENTIALS))).expanduser()
    property_id = get("WAKA_DS_GA4_PROPERTY_ID")
    site_url = get("WAKA_DS_GSC_SITE_URL")

    missing = []
    if not property_id:
        missing.append("WAKA_DS_GA4_PROPERTY_ID（GA4管理画面 > プロパティの設定 に出る数値のID）")
    if not site_url:
        missing.append(
            "WAKA_DS_GSC_SITE_URL（sc-domain:waka-ds.com もしくは https://waka-ds.com/）"
        )
    if missing:
        raise ConfigError(
            "設定が足りない。次の値を環境変数か "
            f"{CONFIG_ENV} へ書く。\n  - " + "\n  - ".join(missing)
        )

    if not credentials.exists():
        raise ConfigError(
            f"サービスアカウントの鍵が見つからない: {credentials}\n"
            "Google Cloud でサービスアカウントを作り、JSON鍵をこのパスへ置くか、"
            "WAKA_DS_GA_CREDENTIALS でパスを指定する。"
        )

    # 型チェッカ向け。missing の検査を通過した時点で None ではない。
    assert property_id and site_url
    return Config(credentials, property_id, site_url)


def build_credentials(config: Config):
    from google.oauth2 import service_account

    return service_account.Credentials.from_service_account_file(
        str(config.credentials_path), scopes=SCOPES
    )
