"""
Day 6 参考答案 · 调通第一个 AI API（命令行聊天机器人）

准备工作（必须做完，缺一步就会报错）：
    1. 在 starter-kit 目录下新建 .env 文件，内容一行：
           DEEPSEEK_API_KEY=sk-你的真实key
    2. 安装依赖：
           python -m pip install -r requirements.txt
    3. 确认同目录的 .gitignore 里有 .env（否则 key 会被传到 GitHub）

验收：
    运行 `python d06_chatbot.py`，能和 AI 连续对话，且它能记住上文。

核心原理（这一句值一整个月的学费）：
    messages 列表 = 对话历史。你每问一句就 append 一条，AI 才有"记忆"。
    所有聊天产品，本质都是在维护这样一个列表。
"""

import os
import sys
from pathlib import Path

from openai import APIConnectionError, AuthenticationError, OpenAI, RateLimitError

MODEL = "deepseek-flash"
BASE_URL = "https://api.deepseek.com"

# 关掉「思考模式」：默认是开启的，且默认强度 high。
# 思考过程同样按输出 token 计费，还会让每轮多等几秒。
# 聊天机器人要的是"秒回"，不是"想很久"。
NO_THINKING = {"thinking": {"type": "disabled"}}

SYSTEM_PROMPT = "你是一位耐心的编程入门老师。回答要简短、口语化，多用生活化的类比。"


def load_api_key() -> str:
    """按顺序找 key：环境变量 → 同目录的 .env 文件。"""
    # 先看系统环境变量里有没有
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()

    # 再看同目录下的 .env 文件
    if not key:
        env_path = Path(__file__).with_name(".env")
        if env_path.exists():
            # 注意用 utf-8-sig：Windows 记事本保存的 .env 会带 BOM，
            # 用普通 utf-8 读会导致变量名变成 "\ufeffDEEPSEEK_API_KEY" 而找不到
            for line in env_path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip().lstrip("\ufeff")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == "DEEPSEEK_API_KEY":
                    key = value.strip().strip('"').strip("'")

    if not key or not key.startswith("sk-") or "你的" in key or "在这里" in key:
        print("=" * 60)
        print("没找到可用的 DEEPSEEK_API_KEY。请检查：")
        print("  1. starter-kit 目录下有没有 .env 文件（注意前面有个点）")
        print("  2. .env 里是不是真的有 DEEPSEEK_API_KEY=sk-xxxx")
        print("  3. key 是不是从 platform.deepseek.com → API keys 复制的")
        print("=" * 60)
        sys.exit(1)

    return key


def build_client() -> OpenAI:
    """创建客户端。DeepSeek 兼容 OpenAI 的接口格式，所以只改 base_url 就行。"""
    return OpenAI(api_key=load_api_key(), base_url=BASE_URL)


def main() -> None:
    client = build_client()

    # 对话历史：system 那一条用来设定 AI 的身份和说话风格
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("已连接 DeepSeek。输入 exit 退出。")
    print("-" * 60)

    while True:
        user_input = input("你：").strip()

        if user_input.lower() in {"exit", "quit", "q"}:
            print("再见！")
            break
        if not user_input:
            continue

        # 1. 把用户这句话加进历史
        messages.append({"role": "user", "content": user_input})

        # 2. 把整段历史发给模型（注意发的是 messages，不是单句）
        #
        # ⚠️ 为什么必须写 try/except：
        # 调外部 API 一定会失败——key 会打错、余额会用完、网会断。
        # 不处理的话程序直接崩掉，甩给你一屏 traceback，
        # 你既不知道哪一步错了，也不知道该改什么。
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                extra_body=NO_THINKING,
            )
        except AuthenticationError:
            print("！key 不对。检查 .env 里的 DEEPSEEK_API_KEY 是否复制完整（sk- 开头，中间不能有空格）。")
            messages.pop()  # 这句话没发成功，从历史里撤掉，避免污染后续对话
            continue
        except RateLimitError:
            print("！请求被拒绝：多为账户余额不足，或请求太频繁。去 platform.deepseek.com 看余额，或等几秒重试。")
            messages.pop()
            continue
        except APIConnectionError:
            print("！连不上服务器。检查网络（用了代理的话确认代理开着），然后重新输入。")
            messages.pop()
            continue
        except Exception as e:  # noqa: BLE001
            print(f"！出错了：{type(e).__name__}。把这条消息发给我，我来定位。")
            messages.pop()
            continue

        reply = response.choices[0].message.content

        # 3. 把 AI 的回答也加进历史，下一轮它才能"记得"
        messages.append({"role": "assistant", "content": reply})

        print(f"AI：{reply}")
        print(f"（本轮 tokens：{response.usage.total_tokens}）")
        print("-" * 60)


if __name__ == "__main__":
    main()

# ===== 理解要点 =====
# role 只有三种：system（设定身份）/ user（你）/ assistant（AI 说过的话）
# temperature 控制随机性：0 更稳定保守，1 更发散有创意
# usage.total_tokens 是计费依据，后面做产品要盯着这个数字控制成本
#
# 为什么 AI 能"记住"上文？因为每次请求我们都把完整历史发过去了。
# 所以对话越长越贵。真实产品要做的"记忆压缩"，就是在这个列表上做文章。

# ===== 自己练 =====
# 1. 把 temperature 改成 0 和 1.5，感受回答的差别
# 2. 加一个指令：输入 "clear" 就清空历史（messages = [messages[0]]）
# 3. 让 AI 每次回答后附带一个"给新手的下一步建议"
# 4. 进阶：把对话纪录保存到 chat_log.json（用 json.dump 写文件）
