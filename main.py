import os
import sys
import threading
import time
import json
import signal
import asyncio
import discord
import aiohttp
from discord import app_commands
import requests
from discord.ext import commands
from discord.gateway import DiscordWebSocket, _log
from discord.ext.commands import Bot

# === Discord Bot Setup ===
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
owner = "sl.ip"
co_owner = 481295611417853982
MainURL = "https://spook.bio"

try:
    with open('TOKEN.txt', 'r') as f:
        token = f.read()
except FileNotFoundError:
    print("Error: The file 'TOKEN' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# === Globals for caching and ready state ===
cached_guilds = []
bot_ready = False

# === Background task to update cached guilds every 2 minutes ===
async def update_guild_cache():
    global cached_guilds
    while True:
        await bot.tree.sync()
        cached_guilds = list(bot.guilds)
        print(f"[Cache Update] Cached {len(cached_guilds)} guilds at {time.strftime('%X')}")
        await asyncio.sleep(120)

class MyGateway(DiscordWebSocket):

    async def identify(self):
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'Discord Android',
                    '$device': 'Discord Android',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                'compress': True,
                'large_threshold': 250,
                'v': 3
            }
        }

        if self.shard_id is not None and self.shard_count is not None:
            payload['d']['shard'] = [self.shard_id, self.shard_count]

        state = self._connection
        if state._activity is not None or state._status is not None:
            payload['d']['presence'] = {
                'status': state._status,
                'game': state._activity,
                'since': 0,
                'afk': False
            }

        if state._intents is not None:
            payload['d']['intents'] = state._intents.value

        await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
        await self.send_as_json(payload)
        _log.info('Shard ID %s has sent the IDENTIFY payload.', self.shard_id)


class MyBot(Bot):

    async def connect(self, *, reconnect: bool = True) -> None:
        """|coro|

        Creates a websocket connection and lets the websocket listen
        to messages from Discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        -----------
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).

        Raises
        -------
        :exc:`.GatewayNotFound`
            If the gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        :exc:`.ConnectionClosed`
            The websocket connection has been terminated.
        """

        backoff = discord.client.ExponentialBackoff()
        ws_params = {
            'initial': True,
            'shard_id': self.shard_id,
        }
        while not self.is_closed():
            try:
                coro = MyGateway.from_client(self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params['initial'] = False
                while True:
                    await self.ws.poll_event()
            except discord.client.ReconnectWebSocket as e:
                _log.info('Got a request to %s the websocket.', e.op)
                self.dispatch('disconnect')
                ws_params.update(sequence=self.ws.sequence, resume=e.resume, session=self.ws.session_id)
                continue
            except (OSError,
                    discord.HTTPException,
                    discord.GatewayNotFound,
                    discord.ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError) as exc:

                self.dispatch('disconnect')
                if not reconnect:
                    await self.close()
                    if isinstance(exc, discord.ConnectionClosed) and exc.code == 1000:
                        # clean close, don't re-raise this
                        return
                    raise

                if self.is_closed():
                    return

                # If we get connection reset by peer then try to RESUME
                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(sequence=self.ws.sequence, initial=False, resume=True, session=self.ws.session_id)
                    continue

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, no sharding, etc)
                # sometimes, discord sends us 1000 for unknown reasons so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(exc, discord.ConnectionClosed):
                    if exc.code == 4014:
                        raise discord.PrivilegedIntentsRequired(exc.shard_id) from None
                    if exc.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                _log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                # Always try to RESUME the connection
                # If the connection is not RESUME-able then the gateway will invalidate the session.
                # This is apparently what the official Discord client does.
                ws_params.update(sequence=self.ws.sequence, resume=True, session=self.ws.session_id)

#bot = commands.Bot(command_prefix="/", intents=intents)
bot = MyBot(command_prefix="/", intents=intents)
#tree = app_commands.CommandTree(bot)

# === Bot Events ===
@bot.event
async def on_ready():
    global bot_ready
    bot_ready = True
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=discord.CustomActivity(name=f"🔗 spook.bio/discord"))
    #if len(bot.guilds) == 1:
        #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=bot.guilds[0].name))
    #else:
       #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))

    # Start the cache updater task
    MyBot(command_prefix="/", intents=intents)
    bot.loop.create_task(update_guild_cache())

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name='Member')
    await member.add_roles(role)
    print(f"Gave {member.name} The Member Role!")

# === Commands ===
@bot.tree.command(name="status", description="Get the spook.bio status")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("[spook.bio Status Page](https://spook.bio/status)")

@bot.tree.command(name="pfp", description="Get a pfp from a user's spook.bio profile.")
async def pfp(interaction: discord.Interaction, username: str):
    url = f"https://spook.bio/u/{username}/pfp.jpg"
    response = requests.get(url)
    if response.status_code == 200:
        await interaction.response.send_message(url, ephemeral=False)
        print("Fetched data successfully!")
    else:
        await interaction.response.send_message(f":x: {response.status_code} Not Found :x:", ephemeral=True)
        print(f"Error fetching data: {response.status_code}")

@bot.tree.command(name="discord2spook", description="Get a spook.bio profile from a discord user.")
async def discord2spook(interaction: discord.Interaction, user: discord.Member): # = <@481295611417853982>):
    url = f"https://api.prp.bio/discord/{user.name}"
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
    port = int(os.environ.get("PORT", 13456))
    print(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

# === Run Bot + Flask Webserver ===
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(token)
