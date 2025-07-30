import os
import threading
import discord
from discord.ext import commands
from flask import Flask, render_template_string, request, redirect, url_for, session

# === Hardcoded Admin Key (change this to your desired password) ===
ADMIN_KEY = "lc1220"

# === Discord Bot Setup ===
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# === Flask App Setup ===
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")  # Change or set in Render environment

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
    </style>
</head>
<body>
    <h1>🤖 Bot Dashboard</h1>
    <p>Status: <b style="color:lime;">Online</b></p>
    <p>Connected to {{ guilds|length }} {{ 'server' if guilds|length == 1 else 'servers' }}</p>
    {% for g in guilds %}
        <div class="server">
            <h3>{{ g.name }}</h3>
            <form action="{{ url_for('send_message') }}" method="post">
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
        <a href="{{ url_for('admin_logout') }}" style="color: #ff5555;">Logout</a>
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

@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        key = request.form.get("key")
        if key == ADMIN_KEY:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return "<h3>Incorrect key.</h3><a href='/login'>Try again</a>"
    return '''
        <h2>Admin Login</h2>
        <form method="POST">
            <input type="password" name="key" placeholder="Enter admin key" required>
            <button type="submit">Login</button>
        </form>
    '''

@app.route("/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/", methods=["GET"])
@admin_required
def dashboard():
    return render_template_string(HTML_TEMPLATE, guilds=bot.guilds)

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

# === Flask Runner in Thread ===
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

# === Bot Events ===
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if len(bot.guilds) == 1:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=bot.guilds[0].name))
    else:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))

# === Optional Slash Command ===
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# === Run Bot + Web Server ===
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.environ.get("DISCORD_BOT_TOKEN"))
