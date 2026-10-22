"""把 AI 接进网页 · 从"能显示"到"能对话"

这是 app.py 最小版的升级版：把 chatbot.py 的 AI 调用搬进来，
变成一个真正有界面的 AI 工具。

准备（缺一样就跑不了）：
    1. python -m pip install openai streamlit
    2. 和本文件同一个文件夹里有 .env，内容一行：
           DEEPSEEK_API_KEY=sk-你的key

运行：
    streamlit run app_chat.py
"""

from pathlib import Path

import streamlit as st
from openai import APIConnectionError, AuthenticationError, OpenAI, RateLimitError

MODEL = "qwen-plus"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ENV_NAME = "ALIYUN_API_KEY"

# 关掉思考模式：默认是开的，思考内容也计费，而且每轮要多等几秒。
NO_THINKING = {"thinking": {"type": "disabled"}}


def load_api_key() -> str:
    """从本文件旁边的 .env 读 key。

    用 utf-8-sig 是因为 Windows 记事本保存的 .env 会带 BOM，
    用普通 utf-8 读会让变量名变成 "\\ufeffDEEPSEEK_API_KEY" 而找不到。
    """
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == ENV_NAME:
            return value.strip().strip('"').strip("'")
    return ""


@st.cache_resource
def get_client(api_key: str) -> OpenAI:
    """API 客户端只创建一次。

    页面每点一下都会重跑整个脚本，不缓存的话每次都会新建一个客户端。
    """
    return OpenAI(api_key=api_key, base_url=BASE_URL)


def stream_reply(client: OpenAI, messages: list):
    """把流式返回拆成一段段纯文字，交给 st.write_stream 逐字显示。"""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        extra_body=NO_THINKING,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


st.title("AI 聊天工具")
st.caption("这个页面是 Python 画出来的，没写一行 HTML。")

api_key = load_api_key()
if not api_key:
    st.error(
        f"在 {Path(__file__).with_name('.env')} 里没找到 {ENV_NAME}。\n\n"
        f"新建一个 .env 文件，内容一行：{ENV_NAME}=sk-你的key",
        title="缺少 API key",
    )
    st.stop()

client = get_client(api_key)

# 对话历史放在 session_state 里，重跑页面不会丢
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 只在第一次打开时放进去一条"规矩",之后不会重复添加
    st.session_state.messages.append(
        {
            "role": "system",
            "content": "你是一位耐心的编程入门老师。回答要简短，口语化，多用生活里的类比。",
        }
    )

for message in st.session_state.messages:
    if message["role"] == "system":
        continue                      # ← 加这两行:规矩是给 AI 看的，不给用户看
    with st.chat_message(message["role"]):
        st.write(message["content"])

# submit_mode="disable"：回答过程中先禁用输入框，避免打断
if prompt := st.chat_input("问点什么…", submit_mode="disable"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(stream_reply(client, st.session_state.messages))
        except AuthenticationError:
            st.error(
                "key 不对。检查 .env 里的 key 是否复制完整（sk- 开头，中间不能有空格）。",
                title="认证失败",
            )
            st.session_state.messages.pop()
            st.stop()
        except RateLimitError:
            st.error(
                "多半是余额不足或请求太频繁。去 platform.deepseek.com 看余额。",
                title="额度问题",
            )
            st.session_state.messages.pop()
            st.stop()
        except APIConnectionError:
            st.error("连不上服务器。检查网络——Steam++ 还开着吗？", title="网络不通")
            st.session_state.messages.pop()
            st.stop()
        except Exception as exc:
            st.error(f"{type(exc).__name__}。把这条消息发我。", title="出错了")
            st.session_state.messages.pop()
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": answer})
