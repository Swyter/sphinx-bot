# Work with Python 3.6
import os
import sys
import asyncio
import discord
from pprint import pprint

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

# swy: implement our bot thingie
class SphinxDiscordClient(discord.Client):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
  async def on_ready(self):
    print('Logged in as')
    print(self.user.name)
    print(self.user.id)
    print('------')
    
    self.moderation_log = self.get_channel(545777338130890752) # the moderation-log channel
    self.sphinx_guild   = self.get_guild  (409322660070424605) # Sphinx Community
    
    mem = self.sphinx_guild.members
    
    for m in mem:
        time_since_creation = (m.joined_at - m.created_at)
        seconds_since_creation = time_since_creation.total_seconds()
        print(m.joined_at, m.bot, m.nick, m.name, m.discriminator, m.is_on_mobile(), time_since_creation, seconds_since_creation, "¨¨Possible bot" if (seconds_since_creation < 120) else "Not likely", m.avatar_url, m.id, m.is_avatar_animated(), m.activities)
        
        if (seconds_since_creation > 60*60):
            continue
        
        # swy: for some reason in the newer accounts there's a mismatch between the member avatar and the profile avatar
        usr = await self.fetch_user(m.id)
        print("/</ ", usr, usr.avatar, usr.avatar_url)
        
        if (m.avatar != usr.avatar):
            print("**Avatar mismatch: ", m, m.avatar, usr.avatar)

  async def on_member_join(self, member):
    time_since_creation = (m.joined_at - m.created_at)
    seconds_since_creation = time_since_creation.total_seconds()
    print('User joined: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"), member.avatar, member.created_at, "Seconds since account creation: " + str(seconds_since_creation))
    
    reasons = []
    blacklisted_avatars = [
        '5a17f3a2cdcdadba5ad5cdb7a79e59c1', # https://cdn.discordapp.com/avatars/681745190590873610/5a17f3a2cdcdadba5ad5cdb7a79e59c1.png?size=128
        '1de82d515d5910830022864f369cb18e', # https://cdn.discordapp.com/avatars/681864778985242637/1de82d515d5910830022864f369cb18e.png?size=128
    ]
    
    if member.avatar in blacklisted_avatars:
        reasons.append("Blacklisted avatar: " + member.avatar_url)
    
    # swy: when the user is created within seconds of joining but already has a set avatar; not humanly possible.
    if member.avatar and seconds_since_creation <= 30:
        reasons.append("Member instantly created with avatar: " + member.avatar_url)
    
    #if member.hypesquad and (datetime.utcnow() - member.created_at).days <= 3:
    #    reasons.append("3 day-old account with HypeSquad.")
    
    if reasons:
        # swy: send a message to the #off-topic channel
        await self.moderation_log.send('Preemptively banned {0.mention}, probably some automated account. 🔨'.format(member))
        await member.guild.ban(member, reason='[Automatic] Suspected bot or automated account.\n' + " - " + "\n - ".join(reasons))
      
  async def on_user_update(before, after):
    # swy: only apply these rules to unverified users as a basic safeguard
    
    print(before, after)
    
    if (before.avatar == after.avatar)
        return
    
    if len(member.roles):
        return
        
    self.sphinx_guild.get_member(after.id)
    

  async def on_message_delete(self, message):
    print('Deleted message:', pprint(message), message.content, time.strftime("%Y-%m-%d %H:%M"))

# swy: launch our bot thingie, allow for Ctrl + C
client = SphinxDiscordClient()

while True:
  try:
    client.loop.run_until_complete(client.start(os.environ["DISCORD_TOKEN"]))
  except KeyboardInterrupt:
    client.loop.run_until_complete(client.logout())
    # cancel all tasks lingering
  finally:
    client.loop.close()
    sys.exit(0)
