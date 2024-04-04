# Work with Python 3.6
import os
import sys
import asyncio
import traceback
import discord
from pprint import pprint
from aiohttp import connector
import random, signal

import time
from datetime import datetime, timedelta

# swy: ugly discord.log file boilerplate
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# swy: exit if we don't have a valid bot token
if not 'DISCORD_TOKEN' in os.environ:
  print('[!] Set your DISCORD_TOKEN environment variable to your Discord client secret.')
  sys.exit(-1)


class SphinxDiscordGoofyLizard(discord.ext.commands.Cog):
  def __init__(self, bot: discord.ext.commands.Bot, log_to_channel):
    self.bot = bot
    print('[i] goofy lizard plug-in ready')

  @discord.ext.commands.Cog.listener()
  async def on_message(self, message):
    # swy: thanks!
    if message.content.lower().startswith('good bot'):
        await message.add_reaction('🐧')
        await message.add_reaction('🤖')

    # swy: we do not want the bot to reply to itself or web-hooks
    if message.author == self.user or message.author.bot:
        return
        
    # swy: only handle private messages, ensure we are in DMs
    if isinstance(message.channel, discord.DMChannel):
        print("PM:", pprint(message), message.content, time.strftime("%Y-%m-%d %H:%M"))
        
        # swy: add an emergency killswitch
        if message.content.lower().startswith('please stop'):
            for guild in self.guilds:
                m = guild.get_member(message.author.id)
                if m and any(x in str(m.roles) for x in ['THQ Nordic', 'Titan (Owners)', 'Pharaohs (Admins)', 'Demigods (Mods)']):
                    await message.add_reaction('👌')
                    await message.channel.send("Disengaging.")
                    await self.logout()
        
        await asyncio.sleep(random.randint(4, 6))
        async with message.channel.typing():
            # swy: useful for testing
            messages = ["Weeeeeeeeee", "Groook", "Prreeeeeah", "Krr", "Chrurr", "Waaaeiaah", "Uhhhhwaaeee", "Roooohoo", "Wooheeee", "Woohioooaaa", "Aaarf", "Grrr", "Baaaaaouououo", "Hooorrrr", "Ooof", "Oofgh", "Grkarkarka", "Shheefgg", "Brrbrbr", "Uggeeeewewewww", "Prr-", "Jkafkapfff"]
            msg = "{0}, {1}.".format(random.choice(messages), random.choice(messages).lower())
            await asyncio.sleep(random.randint(2, 6))
            await message.channel.send(msg)


# swy: implement our bot thingie
class SphinxDiscordClient(discord.Client):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  async def setup_hook(self):
    self.loop.set_debug(True)

    # swy: enable the silly goofy lizard reply plug-in
    await self.add_cog(SphinxDiscordGoofyLizard(self, self.log_to_channel))

  async def on_ready(self):
    # swy: see checker_background_task() for the initialized "global" variables
    print('Logged in as | ' + time.strftime("%Y-%m-%d %H:%M"))
    print(self.user.name)
    print(self.user.id)
    print('------')
    
    # swy: global variables for this client instance, all the other background tasks wait for post_init_event, so it's a good place
    self.channel_test   = self.get_channel( 470890531061366787) # Swyter test -- #general
    self.moderation_log = self.get_channel( 545777338130890752) # the #moderation-log channel
    
    self.portal_god     = self.get_channel(1225464253415424022) # the #portal-god channel 
    self.portal_god_log = self.get_channel(1225486542597001316) # the #portal-god-log channel 
    self.post_init_event.set()

  async def log_to_channel(self, user: discord.Member, text):
    if self.portal_god_log:
      await self.portal_god_log.send(f"{user.mention} `{user.name}#{user.discriminator} ({user.id})` {text}")
    
# --

intents = discord.Intents.default()
intents.members = True

# swy: launch our bot thingie, allow for Ctrl + C
client = SphinxDiscordClient(intents=intents)
loop = asyncio.get_event_loop()

def handle_exit():
    raise KeyboardInterrupt

if os.name != 'nt':
  loop.add_signal_handler(signal.SIGTERM, handle_exit, signal.SIGTERM)
  loop.add_signal_handler(signal.SIGABRT, handle_exit, signal.SIGABRT, None)


while True:
  try:
    loop.run_until_complete(client.start(os.environ["DISCORD_TOKEN"]))
    
  except connector.ClientConnectorError:
    traceback.print_exc()
    pass

  # swy: cancel all lingering tasks and close shop
  except KeyboardInterrupt:
    loop.run_until_complete(client.change_presence(status=discord.Status.offline))
    print("[i] ctrl-c detected")
    loop.run_until_complete(client.close())
    print("[-] exiting...")
    sys.exit(0)