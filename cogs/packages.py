"""
Packages Cog - Handles audio service packages and pricing information
"""

import discord
from discord.ext import commands
from config import PACKAGES


class PackagesCog(commands.Cog):
    """Cog for managing and displaying audio service packages"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="packages", aliases=["services", "pricing"])
    async def list_packages(self, ctx):
        """Display all available audio service packages with pricing and details"""
        embed = discord.Embed(
            title="🎵 TRE Audio Services - Packages & Pricing",
            description="Choose the perfect package for your audio production needs!",
            color=discord.Color.blurple()
        )

        for package_id, package_info in PACKAGES.items():
            details_text = "\n".join([f"• {detail}" for detail in package_info["details"]])
            
            price_display = f"{package_info['currency']}{package_info['price']} {package_info['unit']}"
            
            embed.add_field(
                name=f"**{package_info['name']}** - {price_display}",
                value=f"{package_info['description']}\n\n**Includes:**\n{details_text}",
                inline=False
            )

        embed.set_footer(text="React with 🎛️ to get more information or use !book <package_name>")
        await ctx.send(embed=embed)

    @commands.command(name="package", aliases=["service"])
    async def package_details(self, ctx, package_name: str = None):
        """Get detailed information about a specific package"""
        if package_name is None:
            await ctx.send("Please specify a package. Use `!packages` to see all available options.")
            return

        package_name = package_name.lower().replace(" ", "_")

        if package_name not in PACKAGES:
            await ctx.send(f"❌ Package '{package_name}' not found. Use `!packages` to see available options.")
            return

        package_info = PACKAGES[package_name]

        embed = discord.Embed(
            title=package_info["name"],
            description=package_info["description"],
            color=discord.Color.gold()
        )

        price_display = f"{package_info['currency']}{package_info['price']} {package_info['unit']}"
        embed.add_field(name="💰 Price", value=price_display, inline=False)

        details_text = "\n".join([f"• {detail}" for detail in package_info["details"]])
        embed.add_field(name="✨ Includes", value=details_text, inline=False)

        embed.add_field(
            name="📩 Next Steps",
            value="React to this message or use `!book` to schedule your session!",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="book")
    async def book_session(self, ctx, package_name: str = None):
        """Start the booking process for an audio service package"""
        if package_name is None:
            await ctx.send("Please specify a package to book. Use `!packages` to see available options.")
            return

        package_name = package_name.lower().replace(" ", "_")

        if package_name not in PACKAGES:
            await ctx.send(f"❌ Package '{package_name}' not found. Use `!packages` to see available options.")
            return

        package_info = PACKAGES[package_name]

        embed = discord.Embed(
            title=f"Booking: {package_info['name']}",
            description=f"You're about to book the **{package_info['name']}** package.",
            color=discord.Color.green()
        )

        price_display = f"{package_info['currency']}{package_info['price']} {package_info['unit']}"
        embed.add_field(name="💰 Total Price", value=price_display, inline=False)

        details_text = "\n".join([f"• {detail}" for detail in package_info["details"]])
        embed.add_field(name="✨ Includes", value=details_text, inline=False)

        embed.add_field(
            name="📌 Important",
            value="Please send a DM to the bot owner or use the provided contact method to confirm your booking and arrange payment.",
            inline=False
        )

        embed.set_footer(text="Thank you for your interest in TRE Audio Services!")
        
        await ctx.send(embed=embed)
        await ctx.author.send(f"✅ You've requested to book: **{package_info['name']}** ({price_display})\n\nPlease await confirmation from the studio.")

    @commands.command(name="help_services")
    async def help_services(self, ctx):
        """Show available commands for the audio services bot"""
        embed = discord.Embed(
            title="🎛️ Audio Services Bot - Commands",
            description="Here are the available commands:",
            color=discord.Color.blurple()
        )

        commands_info = [
            ("!packages", "Display all available packages with pricing"),
            ("!package <name>", "Get detailed info about a specific package"),
            ("!book <name>", "Start the booking process for a package"),
            ("!help_services", "Show this help message"),
        ]

        for command, description in commands_info:
            embed.add_field(name=command, value=description, inline=False)

        embed.set_footer(text="For more help, contact the studio owner!")
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the packages cog into the bot"""
    await bot.add_cog(PackagesCog(bot))
