"""
TRE BOT - Discord Audio Services Bot
Manages audio production packages and customer pricing
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import COMMAND_PREFIX

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN not found in .env file!")

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    """Event triggered when bot successfully connects to Discord"""
    print(f"✅ {bot.user} has connected to Discord!")
    print(f"Bot is ready and listening for commands with prefix '{COMMAND_PREFIX}'")
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{COMMAND_PREFIX}packages for services"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Command not found. Use `{COMMAND_PREFIX}help_services` for available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use `{COMMAND_PREFIX}help_services` for command details.")
    else:
        print(f"Error in command {ctx.command}: {error}")
        await ctx.send("❌ An error occurred while processing your command.")


async def load_cogs():
    """Load all cogs from the cogs directory"""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"✅ Loaded cog: {filename[:-3]}")


async def main():
    """Main function to start the bot"""
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
