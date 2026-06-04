# TRE BOT - Discord Audio Services Bot

## Project Overview
A fully functional Discord bot for managing audio production service packages with pricing, booking, and customer management features.

## Key Files
- **bot.py** - Main bot initialization and event handling
- **config.py** - All package definitions and pricing configuration
- **cogs/packages.py** - Commands for displaying packages and handling bookings
- **requirements.txt** - Python dependencies
- **README.md** - Complete setup and usage guide

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your Discord token
3. Run: `python3 bot.py`

## Available Commands
- `!packages` - Show all audio services with pricing
- `!package <name>` - Get details about a specific package
- `!book <name>` - Start booking process
- `!help_services` - Show all commands

## Packages Included
1. **Stereo Mastering** - $25/song (loudness optimization, EQ, compression, limiting, WAV & MP3)
2. **Recording Session** - $40/hour (professional mic, coaching, multiple takes, export)
3. **Full Song Package** - $150/song (recording, mixing, mastering)

All configurations are in `config.py` - easily customizable for your specific needs.
