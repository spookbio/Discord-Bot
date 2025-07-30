import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True  # Needed for reading message content

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
