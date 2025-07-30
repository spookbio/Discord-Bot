import os
import threading
import discord
from discord.ext import commands
from flask import Flask, render_template_string

# === Discord Bot Setup ===
intents = discord.Intents.default()
intents.guilds = True  # For server info
intents.message_content = True  # Optional

bot = commands.Bot(command_prefix="/", intents=intents)

# === Flask App Setup ===
app = Flask(__name__)

@app.route("/")
def dashboard():
    guilds = bot.guilds
    return render_template_string("""
        <h1>🤖 Bot Status</h1>
        <p>Status: <b style="color:green;">Online</b></p>
        <p>Connected to {{ guilds|length }} servers:</p>
        <ul>
            {% for g in guilds %}
                <li>{{ g.name }} ({{ g.id }})</li>
            {% endfor %}
        </ul>
    """, guilds=guilds)

# === Run Flask in Thread ===
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# === Bot Events ===
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))

# Example Slash Command
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# === Start Everything ===
if __name__ == "__main__":
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start Discord bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
