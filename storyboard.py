"""分镜生成器 · 一段剧情 → 分镜表

为什么用 JSON 而不是人看的表格：
    分镜表后面要喂给"画面生成""视频生成"那些工具，
    它们只吃结构化数据。所以从第一天就用 JSON。

运行：
    python storyboard.py

输出：
    1. 屏幕上打印一张人看的分镜表
    2. 同目录生成 分镜.json（给后面流水线用的）
"""

import json
from pathlib import Path

from openai import APIConnectionError, AuthenticationError, OpenAI, RateLimitError

MODEL = "deepseek-flash"
BASE_URL = "https://api.deepseek.com"
NO_THINKING = {"thinking": {"type": "disabled"}}
ENV_NAME = "DEEPSEEK_API_KEY"

# ============================================================
# 想试你自己的剧本？改下面这段就行。
# ============================================================
STORY = """
清晨七点，兰海麒在宿舍被闹钟吵醒。
他想起今天要交的期末作业还没写完。
他冲到图书馆，发现座位都被占满了。
隔壁桌的同学递过来一杯咖啡。
他笑着坐下，开始赶最后两章。
"""

# ============================================================
# system 提示词：告诉它"要什么格式"。
# 关键三件事：只说 JSON、给出字段说明、给一个例子。
# ============================================================
SYSTEM_PROMPT = """你是一位短剧分镜师。用户给你一段剧情，你把它拆成分镜。

只输出一个 JSON 数组，不要任何解释，不要 markdown 代码块。

每个元素必须包含这 5 个字段：
  shot     镜头号，从 1 开始递增
  visual   画面描述，具体到人物动作、环境、光线（给画师看的）
  line     台词，没有就写空字符串
  seconds  这个镜头的时长，单位秒，数字
  mood     情绪基调，两个字以内

示例输出：
[{"shot": 1, "visual": "深夜办公室，主角独自盯着屏幕，只有屏幕光照在脸上", \
"line": "", "seconds": 3, "mood": "压抑"}]
"""


def load_api_key() -> str:
    """从本文件旁边的 .env 读 key。用 utf-8-sig 兼容记事本存的 BOM。"""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return ""
    for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == ENV_NAME:
            return value.strip().strip('"').strip("'")
    return ""


def parse_json_array(text: str) -> list:
    """从模型回复里抠出 JSON 数组。

    为什么要这么麻烦：模型不会永远听话。它可能：
      · 用 ```json ... ``` 包起来
      · 前面先说一句"好的，这是分镜："
      · 结尾多补一句解释
    所以不能直接 json.loads(整个回复)，得先把数组那一截找出来。
    """
    cleaned = text.strip()

    # 情况 1：被 markdown 代码块包住了
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    # 情况 2：前后有废话 —— 取第一个 [ 到最后一个 ]
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(
            "模型回复里找不到 JSON 数组。原始回复开头是：" + cleaned[:120]
        )

    return json.loads(cleaned[start : end + 1])


def make_storyboard(client: OpenAI, story: str) -> list:
    """问模型要分镜，返回解析好的列表。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": story},
        ],
        extra_body=NO_THINKING,
    )
    return parse_json_array(response.choices[0].message.content)


def print_table(shots: list) -> None:
    """打印成人看的表格。"""
    print()
    print("=" * 78)
    print(f"{'镜头':<5}{'时长':<7}{'情绪':<7}画面 / 台词")
    print("-" * 78)
    for shot in shots:
        visual = str(shot.get("visual", ""))
        line = str(shot.get("line", "")).strip()
        head = f"{shot.get('shot', '?'):<5}{str(shot.get('seconds', '?')) + 's':<7}"
        head += f"{str(shot.get('mood', '')):<7}"
        print(head + visual)
        if line:
            print(" " * 19 + f"“{line}”")
    print("=" * 78)
    total = sum(s.get("seconds", 0) for s in shots if isinstance(s.get("seconds"), (int, float)))
    print(f"共 {len(shots)} 个镜头，总时长约 {total} 秒")
    print()


def main() -> int:
    api_key = load_api_key()
    if not api_key:
        print("=" * 70)
        print("没找到 API key。")
        print(f"在 {Path(__file__).with_name('.env')} 里写一行：")
        print(f"    {ENV_NAME}=sk-你的key")
        print("=" * 70)
        return 1

    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    print("正在把剧本拆成分镜……（等 5-10 秒）")
    try:
        shots = make_storyboard(client, STORY)
    except AuthenticationError:
        print("key 不对。检查 .env 里的 key 是否复制完整。")
        return 1
    except RateLimitError:
        print("余额不足或请求太频繁。去 platform.deepseek.com 看余额。")
        return 1
    except APIConnectionError:
        print("连不上服务器。检查网络——Steam++ 不需要开，DeepSeek 是国内的。")
        return 1
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"解析分镜失败：{exc}")
        print("这是模型没按格式回话。把上面的原始回复发我，我调提示词。")
        return 1

    print_table(shots)

    out = Path(__file__).with_name("分镜.json")
    out.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存：{out.name}（给后面画面/视频生成用的）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
