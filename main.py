import discord
from discord import app_commands
from discord.ext import commands
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="/", intents=intents)
        # NO need to create a new CommandTree

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"))

bot = MyBot()

@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# ... other commands ...

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
