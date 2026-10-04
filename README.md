# Apartment Listing Monitor

![CI](https://github.com/K-Ziganshin/avito-apartment-monitor/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Monitors a classifieds search page and sends new rental listings to Telegram, skipping unwanted metro stations.

<!-- TODO (author): project description, screenshots / demo GIF -->

## Features
- Polls the search URL every 2.5-4 minutes with randomised delays
- Blacklist filter by metro station
- Remembers seen listings (no duplicates after restart)
- Remote control from Telegram: `/stop` pauses, `/start` resumes (owner chat only)

## Stack
Python 3.11+, Selenium + undetected-chromedriver, Telegram Bot API (requests)

## Setup
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # fill in your values
python monitor.py
```
Requires Google Chrome installed.

## Configuration
| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Numeric ID of your chat |
| `SEARCH_URL` | Search results page to monitor |
| `BLACKLIST_METRO` | Optional, comma-separated stations to skip |

## Disclaimer
For personal use. Respect the terms of service of any site you query.

## Development
```bash
pip install pytest ruff
ruff check . && pytest
```

License: MIT
