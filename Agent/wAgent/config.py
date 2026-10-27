import configparser

BASE_URL = "https://api.siliconflow.cn/v1"
API_KEY = "sk-igtalceyhffxixsnwpenwhwzligfonizdumwcmxxzenxwnjj"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

# 从 config.ini 读取百度千帆搜索 API Key
_config = configparser.ConfigParser()
_config.read("config.ini", encoding="utf-8")
BAIDU_QIANFAN_API_KEY = _config.get("search", "baidu_qianfan_api_key", fallback="")
