# TRE Stereo Master Bot

A Discord bot for managing and displaying TRE Audio Services packages and pricing.

## Features

- Browse all available audio service packages with pricing
- Get detailed info on individual packages
- Start a booking request directly from Discord

## Commands

| Command | Aliases | Description |
|---|---|---|
| `!packages` | `!services`, `!pricing` | List all packages with pricing |
| `!package <name>` | `!service <name>` | Details for a specific package |
| `!book <name>` | — | Start booking a package |
| `!help_services` | — | Show all available commands |

**Package names:** `stereo_mastering`, `recording_session`, `full_song_package`

## Packages & Pricing

| Package | Price | Includes |
|---|---|---|
| Stereo Mastering | $25/song | Loudness optimization, EQ, compression, limiting, streaming-ready WAV & MP3 |
| Recording Session | $40/hour | Pro mic, vocal coaching, multiple takes, session file export |
| Full Song Package | $150/song | Recording + mixing + mastering |

## Setup

### Prerequisites

- Python 3.12+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/SSEMXI/Tre-Stereo-Master-bot.git
   cd Tre-Stereo-Master-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## Deployment (Heroku)

A `Procfile` and `runtime.txt` are included for Heroku deployment:

```bash
heroku create
heroku config:set DISCORD_TOKEN=your_token_here
git push heroku main
```

## Project Structure

```
├── bot.py            # Bot entry point
├── config.py         # Package definitions and bot settings
├── cogs/
│   └── packages.py   # Commands for packages, booking, and help
├── requirements.txt
├── Procfile
└── runtime.txt
```
