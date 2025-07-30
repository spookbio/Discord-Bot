import os
import sys
import threading
from flask import Flask, redirect
import discord
from discord.ext import commands, tasks
from discord import app_commands

# === Configuration ===
ADMIN_DISCORD_NAME = "lcjunior1220"
ADMIN_KEY = "lc1220"

# === Flask Setup ===
app = Flask(__name__)

@app.route("/")
def root():
    return redirect("/dashboard")

@app.route("/status")
def status():
    return "OK", 200

@app.route("/dashboard")
def dashboard():
    return f"<h1>Bot Dashboard</h1><p>In {len(bot.guilds)} server(s).</p>"

@app.route("/activity")
def activity():
    return f"<h1>Discord Activity View</h1><p>Bot is active in {len(bot.guilds)} server(s).</p>"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# === Bot Setup ===
intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await update_presence()
    presence_updater.start()

async def update_presence():
    if len(bot.guilds) == 1:
        name = f"{bot.guilds[0].name}"
    else:
        name = f"{len(bot.guilds)} servers"
    activity = discord.Activity(type=discord.ActivityType.watching, name=name)
    await bot.change_presence(activity=activity)

@tasks.loop(seconds=90)
async def presence_updater():
    await update_presence()

# === Slash Commands ===
@tree.command(name="stop", description="Stop the bot (admin only)")
async def stop(interaction: discord.Interaction):
    if interaction.user.name != ADMIN_DISCORD_NAME:
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    await bot.close()

@tree.command(name="restart", description="Restart the bot (admin only)")
async def restart(interaction: discord.Interaction):
    if interaction.user.name != ADMIN_DISCORD_NAME:
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Restarting bot...", ephemeral=True)
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)

@tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 Latency: `{latency_ms}ms`", ephemeral=True)

# === Run Everything ===
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
