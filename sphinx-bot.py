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

def exception_handler(loop, context):
    print('Exception handler called', loop, context)

# swy: exit if we don't have a valid bot token
if not 'DISCORD_TOKEN' in os.environ:
  print('[!] Set your DISCORD_TOKEN environment variable to your Discord client secret.')
  sys.exit(-1)

# swy: implement our bot thingie
class SphinxDiscordClient(discord.Client):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    #self.loop.set_exception_handler(exception_handler)
    self.loop.set_debug(True)
    # create the background task and run it in the background
    self.bg_task = self.loop.create_task(self.checker_background_task())
    
  async def on_ready(self):
    print('Logged in as')
    print(self.user.name)
    print(self.user.id)
    print('------')
    self.channel_test   = self.get_channel(470890531061366787) # Swyter test -- #general
    self.moderation_log = self.get_channel(545777338130890752) # the moderation-log channel
    self.sphinx_guild   = self.get_guild  (409322660070424605) # Sphinx Community
    
    mem = self.sphinx_guild.members
    for m in mem:
        time_since_creation = (m.joined_at - m.created_at)
        seconds_since_creation = time_since_creation.total_seconds()
        #print(m.joined_at, m.bot, m.nick, m.name, m.discriminator, m.is_on_mobile(), time_since_creation, seconds_since_creation, "¨¨Possible bot" if (seconds_since_creation < 120) else "Not likely", m.avatar_url, m.id, m.is_avatar_animated(), m.activities)
        
        if (seconds_since_creation <= 60):
            print("calling on", m)
            await self.apply_ban_rules(member=m)
    print("done waiting")
    
  async def apply_ban_rules(self, member=None, user=None, on_member_join=False):

    # swy: sanity check; ensure we either have an user or a member, buth not both
    assert((member and user == None) or (member == None and user))

    if not member:
        member = self.sphinx_guild.get_member(user.id)

    if not user:
        user = self.get_user(member.id)
        
    print("--called", member)
    
    # swy: only apply these rules to unverified
    #      users as a basic safeguard
    #if len(member.roles) > 0:
    #    return
    print("--passed", member)
    time_since_creation    = (member.joined_at - member.created_at)
    seconds_since_creation = time_since_creation.total_seconds()
    
    reasons = []
    blacklisted_avatars = [
        '5a17f3a2cdcdadba5ad5cdb7a79e59c1', # https://cdn.discordapp.com/avatars/681745190590873610/5a17f3a2cdcdadba5ad5cdb7a79e59c1.png?size=128
        '1de82d515d5910830022864f369cb18e', # https://cdn.discordapp.com/avatars/681864778985242637/1de82d515d5910830022864f369cb18e.png?size=128
    ]
    
    # swy: avatars repeatedly used by known spammers.
    if member.avatar in blacklisted_avatars:
        reasons.append("Blacklisted [avatar](%s)." % member.avatar_url)
    
    # swy: when the user is created within seconds of joining but already has a set avatar; not humanly possible.
    if member.avatar and seconds_since_creation <= 30:
        reasons.append("Member instantly created with [avatar](%s)." % member.avatar_url)
    
    # swy: for some reason in newer ccounts there's a mismatch between the member avatar and the profile avatar.
    try:
        usr = await self.fetch_user(member.id)
    except discord.NotFound:
        print("ID %s is not a Discord user." % m.id)
        
    if (usr and member.avatar != usr.avatar):
        reasons.append("Avatar mismatch between [member](%s) and [user](%s)." % (member.avatar_url, usr.avatar_url))
    
    #if member.hypesquad and (datetime.utcnow() - member.created_at).days <= 3:
    #    reasons.append("3 day-old account with HypeSquad.")
    print("reasons", reasons)
    if reasons:
        embed = discord.Embed(colour=discord.Colour(0x1b2148), title='Reasons', description=(" - " + "\n - ".join(reasons)))
        
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name='➥ Seconds since creation', value=seconds_since_creation, inline=True)
        embed.add_field(name='➥ ID',                     value=member.id,              inline=True)
        embed.add_field(name='➥ Created at',             value=member.created_at,      inline=True)
        embed.add_field(name='➥ Joined at',              value=member.joined_at,       inline=True)
  
        # swy: send a message to the #off-topic channel
        await self.channel_test.send('Preemptively banned {0.mention}, probably some automated account. 🔨'.format(member), embed=embed)
        #await member.guild.ban(member, reason='[Automatic] Suspected bot or automated account.\n' + " - " + "\n - ".join(reasons))
      
      
  async def on_member_join(self, member):
    time_since_creation    = (member.joined_at - member.created_at)
    seconds_since_creation = time_since_creation.total_seconds()
    
    print('User joined: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"), member.avatar, member.created_at, "Seconds since account creation: " + str(seconds_since_creation))
    await self.apply_ban_rules(member=member, on_member_join=True)
  
  
  async def on_user_update(self, before, after):
    print(before, after)
    
    # swy: we only care about avatar changes
    #if (before.avatar == after.avatar):
    #    return
        
    await self.apply_ban_rules(user=after)

  async def on_message_delete(self, message):
    print('Deleted message:', pprint(message), message.content, time.strftime("%Y-%m-%d %H:%M"))

  async def checker_background_task(self):
    await self.wait_until_ready()
    print('[i] background ban checker ready')
    self.sphinx_guild   = self.get_guild  (409322660070424605) # Sphinx Community
    
    await asyncio.sleep(5)
    
    while not self.is_closed():
        #mem = self.sphinx_guild.members
        #for m in mem:
        #    time_since_creation = (m.joined_at - m.created_at)
        #    seconds_since_creation = time_since_creation.total_seconds()
        #    #print(m.joined_at, m.bot, m.nick, m.name, m.discriminator, m.is_on_mobile(), time_since_creation, seconds_since_creation, "¨¨Possible bot" if (seconds_since_creation < 120) else "Not likely", m.avatar_url, m.id, m.is_avatar_animated(), m.activities)
        #    
        #    if (seconds_since_creation <= 60):
        #        print("calling on", m)
        #        await self.apply_ban_rules(member=m)
        #print("done waiting")
        # task runs every 30 seconds; infinitely
        await asyncio.sleep(30 * 60)

# swy: launch our bot thingie, allow for Ctrl + C
client = SphinxDiscordClient()

while True:
  try:
    client.loop.run_until_complete(client.start(os.environ["DISCORD_TOKEN"]))
  except KeyboardInterrupt:
    client.loop.run_until_complete(client.logout())
    # cancel all tasks lingering
  except e:
    print(e)
  finally:
    client.loop.close()
    sys.exit(0)
