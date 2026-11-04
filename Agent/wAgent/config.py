import os
import configparser

CONFIG_PATH = os.path.join(os.getcwd(), "config.ini")

DEFAULTS = {
    "api": {
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key": "sk-your-key-here",
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "context_window": "128000",
    },
    "search": {
        "baidu_qianfan_api_key": "",
    },
}


def ensure_config():
    if os.path.exists(CONFIG_PATH):
        return
    cfg = configparser.ConfigParser()
    for section, values in DEFAULTS.items():
        cfg[section] = values
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        cfg.write(f)
    print(f"已创建 config.ini，请填写 API Key 后重启。")
    input("按回车退出...")
    exit()


ensure_config()

_cfg = configparser.ConfigParser()
_cfg.read(CONFIG_PATH, encoding="utf-8")

BASE_URL = _cfg.get("api", "base_url", fallback=DEFAULTS["api"]["base_url"])
API_KEY = _cfg.get("api", "api_key", fallback=DEFAULTS["api"]["api_key"])
MODEL = _cfg.get("api", "model", fallback=DEFAULTS["api"]["model"])
CONTEXT_WINDOW = int(_cfg.get("api", "context_window", fallback=DEFAULTS["api"]["context_window"]))
BAIDU_QIANFAN_API_KEY = _cfg.get("search", "baidu_qianfan_api_key", fallback="")
