# TRE Stereo Master Bot

A Discord bot for managing TRE Audio Services bookings, payments, and customer interactions.

## Features

- Browse all available audio service packages with pricing
- Interactive booking flow entirely through Discord (no forms or third-party links)
- DM-based wizard that collects artist name, song count, turnaround time, and file uploads
- Payment options via **Venmo** and **PayPal** with your payment info sent directly to the customer
- Automatic receipt generated after payment is confirmed
- Owner and staff receive a DM with **Approve / Decline** buttons for every new booking
- Customer is notified when their booking is confirmed or declined

## Booking Flow

1. Customer runs `!services` in the server and selects a package from the dropdown
2. Bot DMs the customer and asks for:
   - Artist name
   - Number of songs
   - Desired turnaround time
   - Audio file upload (WAV, AIFF, MP3, or FLAC)
3. Customer reviews a booking summary
4. Customer selects a payment method (**Venmo** or **PayPal**) and is shown your payment info
5. Customer clicks **"I've Sent Payment"**
6. Customer sees a **Pending Confirmation** message
7. Owner and staff receive a DM with full order details and **Approve / Decline** buttons
8. Once approved, the customer receives a **receipt** and confirmation message

## Commands

| Command | Description |
|---|---|
| `!services` | Browse packages and start an interactive booking |
| `!help_services` | Show available commands |

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

4. Copy `.env.example` to `.env` and fill in your values:
   ```
   DISCORD_TOKEN=your_bot_token_here
   OWNER_DISCORD_ID=your_discord_user_id
   VENMO_HANDLE=@YourVenmoHandle
   PAYPAL_LINK=paypal.me/YourPayPalLink
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

### Finding Your Discord User ID

1. Open Discord → Settings → Advanced → enable **Developer Mode**
2. Right-click your name anywhere in Discord
3. Click **Copy User ID**

## Deployment (Railway)

This bot is hosted on [Railway](https://railway.com). To deploy:

1. Push this repo to GitHub
2. Connect the repo to a new Railway project
3. Go to your service → **Variables** tab and add:

| Variable | Value |
|---|---|
| `DISCORD_TOKEN` | Your bot token |
| `OWNER_DISCORD_ID` | Your Discord user ID |
| `VENMO_HANDLE` | Your Venmo handle |
| `PAYPAL_LINK` | Your PayPal.me link |

4. Railway will automatically deploy on every push to `main`

## Adding Staff (Approval Permissions)

To give another person permission to approve or decline bookings, open `config.py` and add their Discord user ID to the `STAFF_IDS` list:

```python
STAFF_IDS = [706276455444906056, 123456789012345678]
```

Both the owner and all staff members will receive approval DMs for every new booking.

## Project Structure

```
├── bot.py            # Bot entry point
├── config.py         # Package definitions, bot settings, staff IDs, payment info
├── cogs/
│   └── packages.py   # Interactive booking flow, payment views, approval system
├── .env.example      # Environment variable template
├── requirements.txt
├── Procfile
└── runtime.txt
```
