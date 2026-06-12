"""
Packages Cog - Interactive booking flow for TRE Audio Services
"""

import asyncio
from datetime import datetime, timezone

import discord
from discord import ui
from discord.ext import commands

from config import OWNER_ID, PACKAGES, PAYMENT_INFO, STAFF_IDS


# ---------------------------------------------------------------------------
# Owner approval view (sent to owner's DM after customer confirms payment)
# ---------------------------------------------------------------------------

class OwnerApprovalView(ui.View):
    def __init__(self, customer: discord.User, booking_data: dict, customer_message: discord.Message):
        super().__init__(timeout=None)  # No timeout — owner can approve anytime
        self.customer = customer
        self.booking_data = booking_data
        self.customer_message = customer_message

    @ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        now = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
        method = self.booking_data.get("payment_method", "Unknown")

        # Update owner's message to show approved
        approved_embed = discord.Embed(
            title="✅ Booking Approved",
            color=discord.Color.green()
        )
        approved_embed.add_field(name="👤 Customer", value=f"{self.customer}", inline=True)
        approved_embed.add_field(name="📦 Package", value=self.booking_data["package_name"], inline=True)
        approved_embed.add_field(name="🎤 Artist", value=self.booking_data["artist_name"], inline=True)
        approved_embed.add_field(name="🎵 Songs", value=str(self.booking_data["num_songs"]), inline=True)
        approved_embed.add_field(name="⏱️ Turnaround", value=self.booking_data["turnaround"], inline=True)
        approved_embed.add_field(name="💳 Payment", value=f"{method} — {self.booking_data['currency']}{self.booking_data['total']}", inline=True)
        approved_embed.set_footer(text=f"Approved: {now}")
        await interaction.response.edit_message(embed=approved_embed, view=None)

        # Send receipt to customer
        receipt = discord.Embed(
            title="✅ Booking Confirmed — TRE Audio Services",
            description=(
                "Your booking has been **confirmed**! 🎧\n"
                "We'll get started on your order and reach out with any updates."
            ),
            color=discord.Color.green()
        )
        receipt.add_field(name="📦 Package", value=self.booking_data["package_name"], inline=True)
        receipt.add_field(name="🎤 Artist", value=self.booking_data["artist_name"], inline=True)
        receipt.add_field(name="🎵 Songs", value=str(self.booking_data["num_songs"]), inline=True)
        receipt.add_field(name="⏱️ Turnaround", value=self.booking_data["turnaround"], inline=True)
        receipt.add_field(name="💳 Payment Method", value=method, inline=True)
        receipt.add_field(name="💰 Amount", value=f"{self.booking_data['currency']}{self.booking_data['total']}", inline=True)
        receipt.add_field(name="📁 Files", value="\n".join(self.booking_data["file_names"]), inline=False)
        receipt.set_footer(text=f"Confirmed: {now}")

        try:
            await self.customer_message.edit(embed=receipt, view=None)
        except discord.NotFound:
            await self.customer.send(embed=receipt)

    @ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: ui.Button):
        now = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")

        # Update owner's message to show declined
        declined_embed = discord.Embed(
            title="❌ Booking Declined",
            color=discord.Color.red()
        )
        declined_embed.add_field(name="👤 Customer", value=f"{self.customer}", inline=True)
        declined_embed.add_field(name="📦 Package", value=self.booking_data["package_name"], inline=True)
        declined_embed.set_footer(text=f"Declined: {now}")
        await interaction.response.edit_message(embed=declined_embed, view=None)

        # Notify customer of decline
        declined_customer = discord.Embed(
            title="❌ Booking Not Confirmed — TRE Audio Services",
            description=(
                "Unfortunately your booking could **not** be confirmed at this time.\n"
                "Please reach out to the studio directly for more information."
            ),
            color=discord.Color.red()
        )
        try:
            await self.customer_message.edit(embed=declined_customer, view=None)
        except discord.NotFound:
            await self.customer.send(embed=declined_customer)


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
            success = await cog.start_booking_flow(interaction.user, package)
            if not success:
                await interaction.followup.send(
                    "⚠️ I couldn't send you a DM! Please enable DMs from server members:\n"
                    "**Right-click the server icon → Privacy Settings → turn on Direct Messages**\n"
                    "Then select your package again.",
                    ephemeral=True
                )


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
            return False  # DMs are disabled

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
            return False

        # 2. Number of songs
        num_songs_raw = await ask("🎵 **How many songs do you need?**")
        if num_songs_raw is None:
            return False
        try:
            num_songs = int(num_songs_raw)
            if num_songs < 1:
                raise ValueError
        except ValueError:
            await dm.send("❌ That doesn't look like a valid number. Use `!services` to start over.")
            return False

        # 3. Turnaround time
        turnaround = await ask("⏱️ **What is your desired turnaround time?** (e.g., 3 days, 1 week)")
        if turnaround is None:
            return False

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
            return False

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
        return True

    # ------------------------------------------------------------------
    # Finalize booking — called after customer confirms payment
    # ------------------------------------------------------------------

    async def finalize_booking(
        self,
        user: discord.User,
        booking_data: dict,
        message: discord.Message
    ):
        """Notify the owner to approve or decline the booking."""
        now = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
        method = booking_data.get("payment_method", "Unknown")

        # Tell customer their booking is pending approval
        pending_embed = discord.Embed(
            title="⏳ Booking Pending Confirmation",
            description=(
                "Your payment has been submitted! ✅\n"
                "The studio is reviewing your booking and will confirm shortly.\n"
                "You'll receive a DM here once it's approved."
            ),
            color=discord.Color.yellow()
        )
        pending_embed.add_field(name="📦 Package", value=booking_data["package_name"], inline=True)
        pending_embed.add_field(name="🎤 Artist", value=booking_data["artist_name"], inline=True)
        pending_embed.add_field(name="🎵 Songs", value=str(booking_data["num_songs"]), inline=True)
        pending_embed.add_field(name="⏱️ Turnaround", value=booking_data["turnaround"], inline=True)
        pending_embed.add_field(name="💳 Payment Method", value=method, inline=True)
        pending_embed.add_field(name="💰 Amount", value=f"{booking_data['currency']}{booking_data['total']}", inline=True)
        pending_embed.set_footer(text=f"Submitted: {now}")
        await message.edit(embed=pending_embed, view=None)

        # Build the notification embed
        def build_notify_embed():
            notify = discord.Embed(
                title="🔔 New Booking — Awaiting Your Approval",
                description="A customer has submitted a booking and confirmed payment. Approve or decline below.",
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
            return notify

        # Send approval request to owner and all staff
        recipients = list({OWNER_ID} | set(STAFF_IDS))  # deduplicate in case of overlap
        for recipient_id in recipients:
            if not recipient_id:
                continue
            try:
                recipient = await self.bot.fetch_user(recipient_id)
                approval_view = OwnerApprovalView(user, booking_data, message)
                await recipient.send(embed=build_notify_embed(), view=approval_view)
            except (discord.NotFound, discord.Forbidden):
                pass  # Recipient DM failed silently

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
