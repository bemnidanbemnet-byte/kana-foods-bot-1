# Kana Foods Telegram Bot

This repository contains a one-file Telegram bot that runs:
- a customer-facing bot for browsing products and placing orders
- an admin bot that can view all orders with `/orders`

## Files included
- `main.py` - main application (reads tokens from environment variables)
- `requirements.txt` - Python dependencies
- `Procfile` - start command for Railway/Heroku
- `runtime.txt` - specifies Python 3.11
- `.env.example` - example environment file (do NOT commit real tokens)
- `.gitignore` - ignores local files and `.env`

## Setup (local)
1. Create a virtual environment and install dependencies:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your tokens:
   ```
   cp .env.example .env
   # then edit .env to add real tokens
   ```
3. Export environment variables (or use a .env loader):
   ```bash
   export BOT_TOKEN="<your-customer-bot-token>"
   export ADMIN_TOKEN="<your-admin-bot-token>"
   python main.py
   ```

## Deploy to Railway (recommended)
1. Push this repo to GitHub.
2. Go to https://railway.app and sign in with GitHub.
3. Create a new project → Deploy from GitHub repo → choose this repository.
4. In Railway's Project Settings add Environment Variables:
   - `BOT_TOKEN` = <your_customer_bot_token>
   - `ADMIN_TOKEN` = <your_admin_bot_token>
5. Set the Start Command to:
   ```
   python main.py
   ```
Railway will install `requirements.txt` and start the worker defined in `Procfile`.

## Security notes
- **Do not** commit real tokens to GitHub. Use Railway's environment variables or a local `.env` file that is listed in `.gitignore`.
- Rotate tokens if you ever accidentally leak them.
