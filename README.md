# Telegram YouTube Downloader Bot

## Deployment to Render

1. Create a new Web Service on Render
2. Connect your repository
3. Configure the service:
   - Name: your-bot-name
   - Environment: Docker
   - Region: Choose nearest to you
   - Branch: main
   - Build Command: Leave empty (using Dockerfile)
   - Start Command: Leave empty (using Dockerfile)

4. Add Environment Variable:
   - Key: TELEGRAM_BOT_TOKEN
   - Value: Your bot token from @BotFather

5. Click "Create Web Service"

The bot will automatically deploy and start running 24/7 on Render's servers.

Note: Free tier has some limitations, consider using a paid plan for better performance.
