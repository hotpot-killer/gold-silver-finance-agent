# GitHub Actions Secrets 配置说明

要使用 GitHub Actions 定时运行监控，需要在你的 GitHub 仓库设置中添加以下 Secrets：

## 必需的 Secrets

| Secret 名称 | 说明 |
|-------------|------|
| `TUSHARE_TOKEN` | 你的 Tushare Pro API token，从 https://tushare.pro/ 获取 |

## 可选的 Secrets

| Secret 名称 | 说明 |
|-------------|------|
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook URL，用于接收通知 |
| `LLM_API_KEY` | LLM API Key（OpenAI 或兼容接口），用于生成综合分析 |
| `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook（如果使用钉钉通知）|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（如果使用 Telegram 通知）|
| `TELEGRAM_CHAT_ID` | Telegram Chat ID（如果使用 Telegram 通知）|

## 配置步骤

1. 在 GitHub 打开你的仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. 添加上面列出的需要的 Secrets
5. 保存完成

## 定时频率

当前配置是 **每天 UTC 0:00（北京时间 8:00）运行一次**

如果你想修改频率，编辑 `.github/workflows/scheduled-monitor.yml` 中的 `cron` 表达式：
- `0 0 * * *` → 每天一次（默认）
- `0 */6 * * *` → 每6小时一次
- `0 0 * * 1-5` → 每周一到周五每天一次

## 注意事项

1. GitHub Actions 免费配额足够，每天运行一次完全没问题
2. 所有敏感信息都存在 GitHub Secrets 中，不会暴露在代码里
3. 如果网络访问海外网站（Nitter/GLD/SLV）需要代理，可以在 workflow 中配置代理
4. 如果只需要Web查看，可以单独运行 `python main.py --web` 自行部署

## 手动运行

除了定时运行，你也可以手动触发：
1. 打开 GitHub 仓库 → Actions → 选择 `Scheduled Gold-Silver Monitoring`
2. 点击 `Run workflow` → 选择分支 → 点击运行
