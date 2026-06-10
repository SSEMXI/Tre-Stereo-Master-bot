"""
Packages Cog - Interactive booking flow for TRE Audio Services
"""

import asyncio
from datetime import datetime, timezone

import discord
from discord import ui
from discord.ext import commands

from config import OWNER_ID, PACKAGES, PAYMENT_INFO


# ---------------------------------------------------------------------------
# Package selection view (shown in the server channel)
# ---------------------------------------------------------------------------

class PackageSelect(ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label=info["name"],
                value=pkg_id,
                description=f"{info['currency']}{info['price']} {info['unit']}"
            )
            for pkg_id, info in PACKAGES.items()
        ]
        super().__init__(placeholder="Select a package to book...", options=options)

    async def callback(self, interaction: discord.Interaction):
        pkg_id = self.values[0]
        package = PACKAGES[pkg_id]
        await interaction.response.send_message(
            f"Great choice! Check your DMs — I'll guide you through booking **{package['name']}**. 🎧",
            ephemeral=True
        )
        cog: PackagesCog = self.bot.get_cog("PackagesCog")
        if cog:
            await cog.start_booking_flow(interaction.user, package)


class PackageSelectView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.add_item(PackageSelect(bot))


# ---------------------------------------------------------------------------
# Payment method view (shown in DM after booking details collected)
# ---------------------------------------------------------------------------

class PaymentMethodView(ui.View):
    def __init__(self, booking_data: dict, cog: "PackagesCog"):
        super().__init__(timeout=600)
        self.booking_data = booking_data
        self.cog = cog

    @ui.button(label="Venmo", style=discord.ButtonStyle.primary, emoji="💸")
    async def venmo(self, interaction: discord.Interaction, button: ui.Button):
        await self._handle(interaction, "Venmo")

    @ui.button(label="Zelle", style=discord.ButtonStyle.success, emoji="🏦")
    async def zelle(self, interaction: discord.Interaction, button: ui.Button):
        await self._handle(interaction, "Zelle")

    @ui.button(label="PayPal", style=discord.ButtonStyle.secondary, emoji="💳")
    async def paypal(self, interaction: discord.Interaction, button: ui.Button):
        await self._handle(interaction, "PayPal")

    async def _handle(self, interaction: discord.Interaction, method: str):
        self.booking_data["payment_method"] = method
        info = PAYMENT_INFO[method.lower()]
        total = self.booking_data["total"]
        currency = self.booking_data["currency"]
        artist = self.booking_data["artist_name"]

        embed = discord.Embed(
            title=f"💳 Pay via {method}",
            description=(
                f"Please send **{currency}{total}** using {method}.\n\n"
                f"**{method} info:** `{info}`\n\n"
                f"In the memo/note field write: **{artist}**"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Click the button below once you've sent payment.")

        view = ConfirmPaymentView(self.booking_data, self.cog)
        await interaction.response.edit_message(embed=embed, view=view)


# ---------------------------------------------------------------------------
# Confirm payment view
# ---------------------------------------------------------------------------

class ConfirmPaymentView(ui.View):
    def __init__(self, booking_data: dict, cog: "PackagesCog"):
        super().__init__(timeout=600)
        self.booking_data = booking_data
        self.cog = cog

    @ui.button(label="✅ I've Sent Payment", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self.cog.finalize_booking(interaction.user, self.booking_data, interaction.message)

    @ui.button(label="↩️ Change Payment Method", style=discord.ButtonStyle.secondary)
    async def change(self, interaction: discord.Interaction, button: ui.Button):
        total = self.booking_data["total"]
        currency = self.booking_data["currency"]
        embed = discord.Embed(
            title="💳 Choose a Payment Method",
            description=f"Total due: **{currency}{total}**",
            color=discord.Color.blurple()
        )
        view = PaymentMethodView(self.booking_data, self.cog)
        await interaction.response.edit_message(embed=embed, view=view)


# ---------------------------------------------------------------------------
# Main cog
# ---------------------------------------------------------------------------

class PackagesCog(commands.Cog, name="PackagesCog"):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # !services command — shows all packages with a booking dropdown
    # ------------------------------------------------------------------

    @commands.command(name="services", aliases=["packages", "pricing"])
    async def list_packages(self, ctx):
        """Display all packages with an interactive booking selector."""
        embed = discord.Embed(
            title="🎵 TRE Audio Services — Packages & Pricing",
            description="Choose a package from the dropdown below to start your booking!",
            color=discord.Color.blurple()
        )
        for info in PACKAGES.values():
            details = "\n".join(f"• {d}" for d in info["details"])
            embed.add_field(
                name=f"**{info['name']}** — {info['currency']}{info['price']} {info['unit']}",
                value=f"{info['description']}\n\n**Includes:**\n{details}",
                inline=False
            )
        embed.set_footer(text="Select a package below — I'll DM you to complete your order.")
        await ctx.send(embed=embed, view=PackageSelectView(self.bot))

    # ------------------------------------------------------------------
    # Booking flow — called after a package is selected
    # ------------------------------------------------------------------

    async def start_booking_flow(self, user: discord.User, package: dict):
        """Walk the user through collecting booking details via DM."""
        try:
            dm = await user.create_dm()
        except discord.Forbidden:
            return  # Can't DM the user

        def dm_check(m: discord.Message):
            return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)

        async def ask(prompt: str) -> str | None:
            await dm.send(prompt)
            try:
                msg = await self.bot.wait_for("message", check=dm_check, timeout=300)
                return msg.content.strip()
            except asyncio.TimeoutError:
                await dm.send("⏰ Your booking session timed out. Use `!services` to start over.")
                return None

        await dm.send(
            f"👋 Hey {user.display_name}! Let's get your **{package['name']}** booking set up.\n"
            "I'll ask you a few quick questions — just type your answers here."
        )

        # 1. Artist name
        artist_name = await ask("🎤 **What is the artist name?**")
        if artist_name is None:
            return

        # 2. Number of songs
        num_songs_raw = await ask("🎵 **How many songs do you need?**")
        if num_songs_raw is None:
            return
        try:
            num_songs = int(num_songs_raw)
            if num_songs < 1:
                raise ValueError
        except ValueError:
            await dm.send("❌ That doesn't look like a valid number. Use `!services` to start over.")
            return

        # 3. Turnaround time
        turnaround = await ask("⏱️ **What is your desired turnaround time?** (e.g., 3 days, 1 week)")
        if turnaround is None:
            return

        # 4. File upload
        await dm.send(
            "📁 **Please upload your audio file(s) now.**\n"
            "Attach the file(s) to your next message. *(WAV, AIFF, MP3, or FLAC)*\n"
            "Type `skip` if you'll send files later."
        )

        def file_check(m: discord.Message):
            return dm_check(m) and (m.attachments or m.content.lower() == "skip")

        try:
            file_msg = await self.bot.wait_for("message", check=file_check, timeout=600)
            if file_msg.attachments:
                file_names = [a.filename for a in file_msg.attachments]
                file_urls = [a.url for a in file_msg.attachments]
            else:
                file_names = ["To be sent later"]
                file_urls = []
        except asyncio.TimeoutError:
            await dm.send("⏰ Your booking session timed out. Use `!services` to start over.")
            return

        # Calculate total
        if package["unit"] == "per song":
            total = package["price"] * num_songs
        else:
            total = package["price"]

        booking_data = {
            "package_name": package["name"],
            "artist_name": artist_name,
            "num_songs": num_songs,
            "turnaround": turnaround,
            "file_names": file_names,
            "file_urls": file_urls,
            "price_per": package["price"],
            "total": total,
            "currency": package["currency"],
        }

        # Show summary
        summary = discord.Embed(
            title="📋 Booking Summary",
            description="Here's everything I have for your order:",
            color=discord.Color.green()
        )
        summary.add_field(name="📦 Package", value=package["name"], inline=True)
        summary.add_field(name="🎤 Artist", value=artist_name, inline=True)
        summary.add_field(name="🎵 Songs", value=str(num_songs), inline=True)
        summary.add_field(name="⏱️ Turnaround", value=turnaround, inline=True)
        summary.add_field(name="📁 Files", value="\n".join(file_names), inline=False)
        summary.add_field(name="💰 Total Due", value=f"{package['currency']}{total}", inline=True)
        await dm.send(embed=summary)

        # Show payment options
        payment_embed = discord.Embed(
            title="💳 How would you like to pay?",
            description=f"Total: **{package['currency']}{total}**\n\nChoose your preferred payment method below.",
            color=discord.Color.blurple()
        )
        view = PaymentMethodView(booking_data, self)
        await dm.send(embed=payment_embed, view=view)

    # ------------------------------------------------------------------
    # Finalize booking — called after customer confirms payment
    # ------------------------------------------------------------------

    async def finalize_booking(
        self,
        user: discord.User,
        booking_data: dict,
        message: discord.Message
    ):
        """Send receipt to customer and notify the owner."""
        now = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
        method = booking_data.get("payment_method", "Unknown")

        # Receipt for customer
        receipt = discord.Embed(
            title="🧾 Receipt — TRE Audio Services",
            description=(
                "Thank you! Your payment confirmation has been received.\n"
                "We'll get started on your order and reach out with updates. 🎧"
            ),
            color=discord.Color.green()
        )
        receipt.add_field(name="📦 Package", value=booking_data["package_name"], inline=True)
        receipt.add_field(name="🎤 Artist", value=booking_data["artist_name"], inline=True)
        receipt.add_field(name="🎵 Songs", value=str(booking_data["num_songs"]), inline=True)
        receipt.add_field(name="⏱️ Turnaround", value=booking_data["turnaround"], inline=True)
        receipt.add_field(name="💳 Payment Method", value=method, inline=True)
        receipt.add_field(name="💰 Amount", value=f"{booking_data['currency']}{booking_data['total']}", inline=True)
        receipt.add_field(name="📁 Files", value="\n".join(booking_data["file_names"]), inline=False)
        receipt.set_footer(text=f"Order confirmed: {now}")

        await message.edit(embed=receipt, view=None)

        # Notify owner
        if OWNER_ID:
            try:
                owner = await self.bot.fetch_user(OWNER_ID)
                notify = discord.Embed(
                    title="🔔 New Order Received!",
                    color=discord.Color.orange()
                )
                notify.add_field(name="👤 Customer", value=f"{user} (ID: {user.id})", inline=False)
                notify.add_field(name="📦 Package", value=booking_data["package_name"], inline=True)
                notify.add_field(name="🎤 Artist", value=booking_data["artist_name"], inline=True)
                notify.add_field(name="🎵 Songs", value=str(booking_data["num_songs"]), inline=True)
                notify.add_field(name="⏱️ Turnaround", value=booking_data["turnaround"], inline=True)
                notify.add_field(
                    name="💳 Payment",
                    value=f"{method} — {booking_data['currency']}{booking_data['total']}",
                    inline=True
                )
                if booking_data["file_urls"]:
                    notify.add_field(
                        name="📁 Uploaded Files",
                        value="\n".join(booking_data["file_urls"]),
                        inline=False
                    )
                else:
                    notify.add_field(name="📁 Files", value="Customer will send files separately.", inline=False)
                notify.set_footer(text=f"Received: {now}")
                await owner.send(embed=notify)
            except (discord.NotFound, discord.Forbidden):
                pass  # Owner DM failed silently

    # ------------------------------------------------------------------
    # Help command
    # ------------------------------------------------------------------

    @commands.command(name="help_services")
    async def help_services(self, ctx):
        """Show available commands."""
        embed = discord.Embed(
            title="🎛️ TRE Audio Services — Commands",
            color=discord.Color.blurple()
        )
        embed.add_field(name="`!services`", value="Browse packages and start an interactive booking", inline=False)
        embed.add_field(name="`!help_services`", value="Show this help message", inline=False)
        embed.set_footer(text="For support, contact the studio owner directly.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PackagesCog(bot))
