# AI 学习日志

零基础学 AI 并变现的记录。每天写代码、每天提交。

## 我在做什么

从零开始学 Python + AI 应用开发，方向是给小微企业做小工具和网站。
前 3 个月只练技术，不着急变现。

## 项目

| 文件 | week1 |
|---|---|
| `app_chat.py` | 网页版 AI 聊天工具（Streamlit + DeepSeek，流式输出）|
| `app.py` | 第一个 Streamlit 网页 |
| `chatbot.py` | 命令行 AI 聊天机器人，会记住上文 |
| `d06_hello_api.py` | 第一次调用 AI API |
| `my-prompts.md` | 提示词对比笔记 |
| `guess_number.py` / `redo*.py` | Python 基础练习 |

## 怎么跑

    python -m pip install openai streamlit
    # 建 .env，内容：DEEPSEEK_API_KEY=sk-你的key
    streamlit run app_chat.py

## 进度

- [x] Python 基础
- [x] 调通 AI API
- [x] git 版本管理 + 推送到 GitHub
- [x] 第一个网页应用
- [ ] 部署到公网（让别人能点开）

## 技术栈

Python 3.15 · Streamlit · DeepSeek API · Git
