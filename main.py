import discord
from discord import app_commands
from discord.ext import commands
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="/", intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync commands globally (can take up to 1 hour to propagate)
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        # Set status to watching X servers
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"))

bot = MyBot()

# Slash command: /ping
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# Slash command: /say <message>
@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.describe(message="Message for the bot to say")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

# Slash command: /add <a> <b>
@bot.tree.command(name="add", description="Add two numbers")
@app_commands.describe(a="First number", b="Second number")
async def add(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} + {b} = {a + b}")

# Slash command: /help
@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**Available Commands:**\n"
        "/ping — Check if bot is online\n"
        "/say <message> — Bot repeats your message\n"
        "/add <num1> <num2> — Adds two numbers\n"
        "/help — Shows this help message"
    )
    await interaction.response.send_message(help_text)

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
