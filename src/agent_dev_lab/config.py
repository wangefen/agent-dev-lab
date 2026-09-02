import os #Python 自带的 os 模块可以读取操作系统环境变量。

from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

#getenv()中第二个参数是默认值

DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com",
)

#DEEPSEEK_MODEL有明确说明就用这个，没用就默认v4-flash
DEEPSEEK_MODEL = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek_v4-flash"
)