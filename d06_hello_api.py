"""
Day 6 最小版 · 只问 AI 一句话，看它回什么

这是你第一次真正调用 AI。先跑通这 30 行，再去写完整版的聊天机器人。

────────────────────────────────────────────
准备（两件事，缺一件就跑不了）

  1. 装库：
         python -m pip install openai

  2. 在这个脚本所在的文件夹里新建 .env 文件，内容一行：
         DEEPSEEK_API_KEY=sk-你的真实key
     （用 VS Code 新建，别用记事本 —— 记事本会加 .txt 后缀和 BOM）

运行：
     python d06_hello_api.py

看到「AI 说：……」= Day 6 最小版完成。
────────────────────────────────────────────
"""

import sys
from pathlib import Path

# Windows 上让中文正常显示（Python 3.15 已默认 UTF-8，这行是给老版本兜底）
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MODEL = "deepseek-flash"
BASE_URL = "https://api.deepseek.com"
ENV_NAME = "DEEPSEEK_API_KEY"

# 关掉「思考模式」。
# 为什么：DeepSeek 默认开启思考，且默认强度是 high —— 模型会先写一大段
# 思维链再给出回答，那段内容同样按输出 token 计费，而且每次要多等好几秒。
# 对入门练习来说，快和便宜比「多想一会儿」重要得多。
# 想打开：把 disabled 改成 enabled（见 api-docs.deepseek.com/guides/thinking_mode）
NO_THINKING = {"thinking": {"type": "disabled"}}


def find_env_file():
    """按顺序找 .env：脚本所在目录 → 当前工作目录。"""
    here = Path(__file__).resolve().parent
    for folder in (here, Path.cwd()):
        candidate = folder / ".env"
        if candidate.exists():
            return candidate
    return None


def load_api_key():
    """读 key。用 utf-8-sig 是因为记事本存的 .env 可能带 BOM。"""
    import os

    key = os.environ.get(ENV_NAME, "").strip()
    if key:
        return key, "系统环境变量"

    env_path = find_env_file()
    if env_path is None:
        return "", None

    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == ENV_NAME:
            return value.strip().strip('"').strip("'"), str(env_path)

    return "", str(env_path)


def main():
    key, source = load_api_key()

    if not key:
        print("=" * 62)
        print("没找到 API key，所以还没法问 AI。请检查：")
        print()
        if source is None:
            print("  ❌ 没找到 .env 文件")
            print("     在这个文件夹里新建一个：")
            print(f"     {Path(__file__).resolve().parent}")
        else:
            print(f"  ❌ 找到了 {source}，但里面没有 {ENV_NAME}=...")
        print()
        print("  .env 的内容应该是一行（注意等号两边不要加空格）：")
        print(f"     {ENV_NAME}=sk-你的真实key")
        print()
        print("  key 去哪拿：platform.deepseek.com → 左侧 API keys")
        print("=" * 62)
        return 1

    if "你的" in key or "在这里" in key or not key.startswith("sk-"):
        print("=" * 62)
        print(f"  ❌ {source} 里的 key 看起来还是占位符，不是真的 key。")
        print(f"     现在读到的是：{key[:12]}...")
        print("     正常应该以 sk- 开头，后面是一长串字符。")
        print("=" * 62)
        return 1

    print(f"✓ 找到 key（来自 {source}），前几位是 {key[:7]}...")
    print("正在问 AI……（第一次可能要等 3-5 秒）")

    try:
        from openai import OpenAI
    except ImportError:
        print()
        print("  ❌ 还没装 openai 这个库。先运行：")
        print("     python -m pip install openai")
        return 1

    client = OpenAI(api_key=key, base_url=BASE_URL)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "用一句话介绍你自己"}],
            extra_body=NO_THINKING,
        )
    except Exception as e:
        name = type(e).__name__
        print()
        print("=" * 62)
        print(f"  ❌ 调用失败：{name}")
        print()
        if name == "AuthenticationError" or "401" in str(e):
            print("  → key 不对。常见原因：")
            print("     · 复制时漏了开头或结尾的字符")
            print("     · key 中间多了空格或换行")
            print("     · 这个 key 已经被删掉了（去平台重新建一个）")
        elif name == "RateLimitError" or "402" in str(e) or "Insufficient" in str(e):
            print("  → 余额不足或请求太频繁。去 platform.deepseek.com 看一下余额。")
        elif name in ("APIConnectionError", "APITimeoutError"):
            print("  → 连不上服务器。检查网络 / VPN / 代理。")
        elif "model" in str(e).lower() and ("not exist" in str(e).lower() or "invalid" in str(e).lower()):
            # 模型名会随官方升级而变化。出现这条就说明 MODEL 常量该更新了。
            print(f"  → 模型名 `{MODEL}` 服务器不认了。")
            print("     去 api-docs.deepseek.com/quick_start/pricing 看当前的模型名，")
            print("     然后把本文件顶部的 MODEL = ... 改成新的。")
        else:
            print(f"  原始报错：{e}")
        print("=" * 62)
        print()
        print("把上面这一段整段发我，我帮你看。")
        return 1

    reply = response.choices[0].message.content
    print()
    print("-" * 62)
    print("AI 说：", reply)
    print("-" * 62)
    print()
    print("🎉 成功了 —— 这是你第一次让 AI 按你的指令干活。")
    print(f"   这次调用大约花了 {response.usage.total_tokens} 个 token（几分钱）。")
    print()
    print("下一步：把 starter-kit/d06_chatbot.py 复制到 C:\\ai-lab\\week1\\chatbot.py，")
    print("        那是个能连续对话的完整版。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
