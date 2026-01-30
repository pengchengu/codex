# Morning Brief Hub

一个用于“爬虫 → 智能筛选/总结 → 网站展示 → 手机推送 → TTS播报”的晨间新闻项目，默认聚焦金融资讯。

## 功能概览
- 配置化抓取主流金融资讯网站（RSS/HTML）。
- 支持 OpenAI / Kimi / GLM 等 LLM 摘要与重点提炼。
- Web UI 展示今日简报与新闻列表。
- 可通过 Webhook 推送到手机（如 Bark、企业微信、飞书机器人等）。
- 支持 OpenAI TTS 生成晨报语音。

## 快速开始
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

uvicorn app.main:app --reload
```

访问 http://localhost:8000

## 配置说明
修改 `config.yaml` 即可：
- `sources`: 选择资讯来源，支持 RSS 与 HTML 解析。
- `crawl.interval_minutes`: 抓取频率。
- `crawl.proxy`: 代理设置（如 `http://127.0.0.1:7890`）。
- `summary`: LLM 供应商、模型、摘要长度。
- `push`: Webhook 推送配置。
- `speech`: TTS 语音配置。

## 常见推送示例
- 飞书机器人: 在 `push.providers` 中填写机器人 webhook 地址（type=feishu）
- 企业微信机器人: 在 `push.providers` 中填写机器人 webhook 地址（type=wecom）

## 本地 TTS 说明
- 默认使用 `pyttsx3`（本地 CPU 可运行）。若系统缺少对应语音引擎（如 eSpeak），需要按系统提示安装。

## 注意事项
- Bloomberg/Perplexity 等网站对抓取频率与合法使用有明确要求，请确保遵守服务条款。
- 建议优先使用 RSS，以降低封禁风险。
