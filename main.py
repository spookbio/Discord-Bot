import os
import sys
import threading
import time
import signal
import asyncio
import discord
from discord import app_commands
import requests
from discord.ext import commands
from discord.gateway import DiscordWebSocket, _log
from discord.ext.commands import Bot
from flask import Flask, render_template_string, request, redirect, url_for, session

# === Hardcoded Admin Key (change this!) ===
ADMIN_KEY = "lc1220"

# === Discord Bot Setup ===
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
owner = "<@481295611417853982>"
co_owner = "lcjunior1220"

bot = commands.Bot(command_prefix="/", intents=intents)
# tree = app_commands.CommandTree(bot)

try:
    with open('TOKEN.txt', 'r') as f:
        token = f.read()
except FileNotFoundError:
    print("Error: The file 'TOKEN' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
# === Flask App Setup ===
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e2f; color: #fff; padding: 20px; }
        h1 { color: #50fa7b; }
        select, input[type=text] { padding: 6px; border-radius: 5px; border: none; margin: 5px 0; }
        input[type=submit] { background: #50fa7b; border: none; padding: 8px 12px; border-radius: 5px; color: #000; cursor: pointer; }
        .server { background: #282a36; padding: 10px; margin-bottom: 15px; border-radius: 10px; }
        .logout { margin-top: 20px; }
        .presence-button {
            display: inline-block;
            margin-top: 10px;
            background-color: #7289da;
            color: white;
            padding: 10px 18px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        .presence-button:hover {
            background-color: #5b6eae;
        }
    </style>
</head>
<body>
    <h1>🤖 Bot Dashboard</h1>
    <p>Status: <b style="color:lime;">Online</b></p>
    <p>Connected to {{ guilds|length }} {{ 'server' if guilds|length == 1 else 'servers' }}</p>
    
    <!-- Presence Button -->
    <a href="https://dsc.gg/spookbio" target="_blank" rel="noopener" class="presence-button">
        Join Our Server
    </a>
    
    {% for g in guilds %}
        <div class="server">
            <h3>{{ g.name }}</h3>
            <form action="/send" method="post">
                <input type="hidden" name="guild_id" value="{{ g.id }}">
                <label for="channel">Channel:</label>
                <select name="channel_id">
                    {% for c in g.text_channels %}
                        <option value="{{ c.id }}">{{ c.name }}</option>
                    {% endfor %}
                </select>
                <br>
                <label for="message">Message:</label>
                <input type="text" name="message" placeholder="Enter your message" required>
                <br>
                <input type="submit" value="Send">
            </form>
        </div>
    {% endfor %}
    <div class="logout">
        <a href="/logout" style="color: #ff5555;">Logout</a>
    </div>
</body>
</html>
"""

# === Admin Auth Decorator ===
def admin_required(f):
    def wrapped(*args, **kwargs):
        if session.get("admin") != True:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    wrapped.__name__ = f.__name__
    return wrapped

# === Flask Routes ===
@app.route("/status")
def status():
    return "OK", 200

@app.route("/activity")
def activity():
    return redirect(url_for("admin_login"))

@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin") == True:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        key = request.form.get("key")
        if key == ADMIN_KEY:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return '''
                <h3 style="color: red; font-family: Arial, sans-serif;">Incorrect key.</h3>
                <a href="/login" style="font-family: Arial, sans-serif; color: #50fa7b;">Try again</a>
            '''

    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body {
                background: #121212;
                color: #eee;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .login-container {
                background: #282a36;
                padding: 40px 50px;
                border-radius: 12px;
                box-shadow: 0 0 15px #50fa7b;
                text-align: center;
                width: 320px;
            }
            h2 {
                margin-bottom: 25px;
                color: #50fa7b;
            }
            input[type=password] {
                width: 100%;
                padding: 12px;
                margin-bottom: 20px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                background: #44475a;
                color: #f8f8f2;
            }
            input[type=password]::placeholder {
                color: #bd93f9;
            }
            button {
                background: #50fa7b;
                border: none;
                color: #000;
                padding: 12px 0;
                width: 100%;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                cursor: pointer;
                transition: background 0.3s ease;
            }
            button:hover {
                background: #44d366;
            }
            a {
                display: inline-block;
                margin-top: 15px;
                color: #50fa7b;
                text-decoration: none;
                font-size: 14px;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>Admin Login</h2>
            <form method="POST">
                <input type="password" name="key" placeholder="Enter admin key" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route("/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# Dashboard at root /
@app.route("/", methods=["GET"])
@admin_required
def dashboard():
    if not bot_ready:
        return "<h3>Bot is not ready yet, please try again in a moment.</h3>"
    return render_template_string(HTML_TEMPLATE, guilds=cached_guilds)

# Redirect /activity to /
@app.route("/activity")
def activity_redirect():
    return redirect(url_for("dashboard"))

@app.route("/send", methods=["POST"])
@admin_required
def send_message():
    guild_id = int(request.form["guild_id"])
    channel_id = int(request.form["channel_id"])
    message = request.form["message"]

    guild = discord.utils.get(bot.guilds, id=guild_id)
    if guild:
        channel = discord.utils.get(guild.text_channels, id=channel_id)
        if channel:
            try:
                bot.loop.create_task(channel.send(message))
            except Exception as e:
                print(f"Failed to send message: {e}")

    return redirect(url_for("dashboard"))

# === Globals for caching and ready state ===
cached_guilds = []
bot_ready = False

# === Background task to update cached guilds every 10 seconds ===
async def update_guild_cache():
    global cached_guilds
    while True:
        await bot.tree.sync()
        cached_guilds = list(bot.guilds)
        if len(bot.guilds) == 1:
            await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=bot.guilds[0].name))
            for server in bot.guilds:
                print(server.name)
                print(server)
        else:
            await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))
            for server in bot.guilds:
                print(server.name)
                print(server)
            
        print(f"[SYSTEM] Synced {len(cached_guilds)} guild(s) at {time.strftime('%X')}")
        await asyncio.sleep(10)

# === Bot Events ===
@bot.event
async def on_ready():
    global bot_ready
    bot_ready = True
    await bot.tree.sync()
    await bot.change_presence(status=discord.Status.do_not_disturb)
    print(f"Logged in as {bot.user}")
    if len(bot.guilds) == 1:
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=bot.guilds[0].name))
        for server in bot.guilds:
            print(server.name)
            print(server)
    else:
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))
        for server in bot.guilds:
            print(server.name)
            print(server)

    # Start the cache updater task
    bot.loop.create_task(update_guild_cache())


@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name='Member')
    if role:
        await member.add_roles(role)
        print(f"Gave {member.name} The Member Role!")
    else:
        print(f" Member Role Not Found! | {member.name}")


def restartbot():
    print("Bot Restarting.")
    os.execv(sys.executable, ["python3 main.py =)"])
    os.kill(os.getpid(), signal.SIGINT)

# === App Commands === #
@bot.tree.command(name="status", description="Get the spook.bio status")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("[spook.bio Status Page](https://spookbio.statuspage.io)")

@bot.tree.command(name="stop", description="Stop the bot.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def stop(interaction: discord.Interaction):
    if interaction.user.name == {owner} or {co_owner}:
        await interaction.response.send_message(":white_check_mark: Shutdown Successfully!", ephemeral=False)
        await bot.close()
        print("Bot Stopped.")
        sys.exit("Bot Stopped.")
    else:
        await interaction.response.send_message(f"Only {owner}, and {co_owner} can use this command.", ephemeral=True)

@bot.tree.command(name="restart", description="Restart the bot.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def restart(interaction: discord.Interaction):
    if interaction.user.name == {owner} or {co_owner}:
        await interaction.response.send_message(":white_check_mark: Restarted Successfully!!", ephemeral=False)
        restartbot()
    else:
        await interaction.response.send_message(f"Only {owner}, and {co_owner} can use this command.", ephemeral=True)

@bot.tree.command(name="pfp", description="Get a pfp from a user's spook.bio profile.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def pfp(interaction: discord.Interaction, username: str = "phis"):
    url = f"https://spook.bio/u/{username}/pfp.jpg"
    response = requests.get(url)
    if response.status_code == 200:
        await interaction.response.send_message(url, ephemeral=False)
        print("Fetched data successfully!")
    else:
        await interaction.response.send_message(f":x: {response.status_code} Not Found :x:", ephemeral=True)
        print(f"Error fetching data: {response.status_code}")

@bot.tree.command(name="discord2spook", description="Get a spook.bio profile from a discord user.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def discord2spook(interaction: discord.Interaction, user: discord.Member): # = <@481295611417853982>):
    url = f"https://prp.bio/discord/{user.name}"
    print(url)
    response = requests.get(url)
    print(response.text)
    if response.status_code == 200:
        await interaction.response.send_message(f"{user.mention}'s [Profile]({response.text})", ephemeral=False)
        print("Fetched data successfully!")
    else:
        if interaction.user.name == user.name:
            await interaction.response.send_message(f":x: You don't have a spook.bio profile linked to your account {user.mention}! :x: To link your profile to your account please DM {owner} or {co_owner}")
            return
        await interaction.response.send_message(f":x: {user.mention} doesn't have a spook.bio profile linked to their account! :x:", ephemeral=False)
        print(f"Error fetching data: {response.status_code}")

# === Guild Commands === #
#async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("[spook.bio Status Page](https://spookbio.statuspage.io)")

#async def stop(interaction: discord.Interaction):
    if interaction.user.name == {owner} or {co_owner}:
        await interaction.response.send_message(":white_check_mark: Shutdown Successfully!", ephemeral=False)
        await bot.close()
        print("Bot Stopped.")
        sys.exit("Bot Stopped.")
    else:
        await interaction.response.send_message(f"Only {owner}, and {co_owner} can use this command.", ephemeral=True)

#async def restart(interaction: discord.Interaction):
    if interaction.user.name == {owner} or {co_owner}:
        await interaction.response.send_message(":white_check_mark: Restarted Successfully!!", ephemeral=False)
        restartbot()
    else:
        await interaction.response.send_message(f"Only {owner}, and {co_owner} can use this command.", ephemeral=True)

#async def pfp(interaction: discord.Interaction, username: str = "phis"):
    url = f"https://spook.bio/u/{username}/pfp.jpg"
    response = requests.get(url)
    if response.status_code == 200:
        await interaction.response.send_message(url, ephemeral=False)
        print("Fetched data successfully!")
    else:
        await interaction.response.send_message(f":x: {response.status_code} Not Found :x:", ephemeral=True)
        print(f"Error fetching data: {response.status_code}")

# async def discord2spook(interaction: discord.Interaction, user: discord.Member): # = <@481295611417853982>):
    url = f"https://prp.bio/discord/{user.name}"
    print(url)
    response = requests.get(url)
    print(response.text)
    if response.status_code == 200:
        await interaction.response.send_message(f"{user.mention}'s [Profile]({response.text})", ephemeral=False)
        print("Fetched data successfully!")
    else:
        if interaction.user.name == user.name:
            await interaction.response.send_message(f":x: You don't have a spook.bio profile linked to your account {user.mention}! :x: To link your profile to your account please DM {owner} or {co_owner}")
            return
        await interaction.response.send_message(f":x: {user.mention} doesn't have a spook.bio profile linked to their account! :x:", ephemeral=False)
        print(f"Error fetching data: {response.status_code}")

# === Flask Runner in Thread ===
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

# === Run Bot + Flask Webserver ===
if __name__ == "__main__":
    bot.run(token)
    threading.Thread(target=run_flask).start()