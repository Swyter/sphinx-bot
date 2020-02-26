# Work with Python 3.6
import os
import sys
import asyncio
import discord
from pprint import pprint
import random

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
    
    self.loop.set_debug(True)
    # create the background task and run it in the background
    self.post_init_event = asyncio.Event()
    self.bg_task = self.loop.create_task(self.checker_background_task())
    
  async def on_ready(self):
    # swy: see checker_background_task() for the initialized "global" variables
    print('Logged in as')
    print(self.user.name)
    print(self.user.id)
    print('------')
    
    # swy: global variables for this client instance, this is loaded right after on_ready, so it's a good place()
    self.channel_test   = self.get_channel(470890531061366787) # Swyter test -- #general
    self.moderation_log = self.get_channel(545777338130890752) # the moderation-log channel
    self.sphinx_guild   = self.get_guild  (409322660070424605) # Sphinx Community
    self.post_init_event.set()
    
  async def apply_ban_rules(self, member=None, on_member_join=False):
    # swy: sanity check; ensure we either have a member
    assert(member)
        
    # swy: only apply these rules to unverified users as a basic safeguard (they only have one role; called @everyone)
    #      if this member has more than one role, skip it. that's it.
    if len(member.roles) > 1:
        return
        
    time_since_creation    = (member.joined_at - member.created_at)
    seconds_since_creation = time_since_creation.total_seconds()
    
    # swy: for some reason fetching a fresh user profile brings different results
    try:
        usr = await self.fetch_user(member.id)
    except discord.NotFound:
        print("ID %s is not a Discord user." % m.id)
        return
    
    reasons = []
    blacklisted_avatars = [
        '5a17f3a2cdcdadba5ad5cdb7a79e59c1', # https://cdn.discordapp.com/avatars/681745190590873610/5a17f3a2cdcdadba5ad5cdb7a79e59c1.png?size=128
        '1de82d515d5910830022864f369cb18e', # https://cdn.discordapp.com/avatars/681864778985242637/1de82d515d5910830022864f369cb18e.png?size=128
        '67d05954883e8c5ba39f6e61ab681964', # https://cdn.discordapp.com/avatars/682013036659474434/67d05954883e8c5ba39f6e61ab681964.png?size=128
        '334b09e66c36ffbb0ea946d7641f1018', # https://cdn.discordapp.com/avatars/681774685377003527/334b09e66c36ffbb0ea946d7641f1018.png?size=128
        'd97d9ee1f09baa485ac06bc33ef644b2', # https://cdn.discordapp.com/avatars/681885340457369632/d97d9ee1f09baa485ac06bc33ef644b2.png?size=128
    ]
    
    # swy: avatars repeatedly used by known spammers.
    if usr.avatar in blacklisted_avatars:
        reasons.append("Blacklisted [avatar](%s)." % usr.avatar_url)
    
    # swy: when the user is created within seconds of joining but already has a set avatar; not humanly possible.
    if on_member_join and (member.avatar or usr.avatar) and seconds_since_creation <= 30:
        reasons.append("Member instantly created with [avatar](%s)." % member.avatar_url)
        
    # swy: when the user is created within seconds of joining but already is set to offline; not humanly possible.
    if on_member_join and member.status == discord.Status.offline and seconds_since_creation <= 30:
        reasons.append("Member instantly created and joined as offline.")
        
    # swy: for some reason in newer bot accounts there's a mismatch between the member avatar and the profile avatar.       
    if member.avatar != usr.avatar:
        reasons.append("Avatar mismatch between [member](%s) and [user](%s)." % (member.avatar_url, usr.avatar_url))
    
    #if member.hypesquad and (datetime.utcnow() - member.created_at).days <= 3:
    #    reasons.append("3 day-old account with HypeSquad.")
    
    if reasons:
        embed = discord.Embed(colour=discord.Colour(0x1b2148), title='Reasons', description=(" - " + "\n - ".join(reasons)))
        
        embed.set_thumbnail(url=usr.avatar_url)
        embed.add_field(name='➥ Seconds since creation', value=seconds_since_creation, inline=True)
        embed.add_field(name='➥ ID',                     value=member.id,              inline=True)
        embed.add_field(name='➥ Created at',             value=member.created_at,      inline=True)
        embed.add_field(name='➥ Joined at',              value=member.joined_at,       inline=True)
        embed.add_field(name='➥ Name and discriminator', value=member.name + '#' + member.discriminator)
      
        if member.nick:
            embed.add_field(name='➥ Server nick', value=member.nick)
  
        # swy: send a message to the #off-topic channel
        await self.moderation_log.send('Preemptively banned {0.mention}, probably some automated account. 🔨'.format(member), embed=embed)
        await self.channel_test.send  ('Preemptively banned {0.mention}, probably some automated account. 🔨'.format(member), embed=embed)
        await member.guild.ban(member, reason='[Automatic] Suspected bot or automated account.\n' + " - " + "\n - ".join(reasons))

    return reasons


  async def on_member_join(self, member):
    time_since_creation    = (member.joined_at - member.created_at)
    seconds_since_creation = time_since_creation.total_seconds()
    
    print('User joined: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"), member.avatar, member.created_at, "Seconds since account creation: " + str(seconds_since_creation), "Status", member.status)
    reasons = await self.apply_ban_rules(member=member, on_member_join=True)
    
    # swy: while we didn't ban anyone we can still warn about fishy accounts
    if not reasons:
        if seconds_since_creation < 60:
            await self.moderation_log.send('The account {0.mention} was created only {1} seconds ago. Fishy. 🤔'.format(member, seconds_since_creation))
        elif seconds_since_creation < (60 * 60 * 2) and member.status == discord.Status.offline:
            await self.moderation_log.send('The account {0.mention} was created only {1} seconds ago and joined offline. Fishy. 🤔'.format(member, seconds_since_creation))
            
  
  async def on_user_update(self, before, after):
    print(before, after)
    
    # swy: we only care about avatar changes
    if (before.avatar == after.avatar):
        return

    # swy: ensure this is a member of the correct server; check that that it only has the default role
    m = self.sphinx_guild.get_member(after.id)
    
    if m and len(m.roles) <= 1:
        await self.apply_ban_rules(member=m)


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
        await asyncio.sleep(random.randint(4, 6))
        async with message.channel.typing():
            # swy: useful for testing
            messages = ["Weeeeeeeeee", "Groook", "Prreeeeeah", "Krr", "Chrurr", "Waaaeiaah", "Uhhhhwaaeee", "Roooohoo", "Wooheeee", "Woohioooaaa", "Aaarf", "Grrr", "Baaaaaouououo", "Hooorrrr", "Ooof", "Oofgh", "Grkarkarka", "Shheefgg", "Brrbrbr", "Uggeeeewewewww", "Prr-", "Jkafkapfff"]
            msg = "{0}, {1}.".format(random.choice(messages), random.choice(messages).lower())
            await asyncio.sleep(random.randint(2, 6))
            await message.channel.send(msg)


  async def checker_background_task(self):
    await self.wait_until_ready()
    print('[i] background ban checker ready')
    
    await self.post_init_event.wait()
    print('[i] running loop')
    
    while not self.is_closed():
        mem = self.sphinx_guild.members
        for m in mem:
            time_since_creation = (m.joined_at - m.created_at)
            seconds_since_creation = time_since_creation.total_seconds()
            #print(m.joined_at, m.bot, m.nick, m.name, m.discriminator, m.is_on_mobile(), time_since_creation, seconds_since_creation, "¨¨Possible bot" if (seconds_since_creation < 120) else "Not likely", m.avatar_url, m.id, m.is_avatar_animated(), m.activities)
            
            if (seconds_since_creation <= 60 * 60 and len(m.roles) <= 1):
                await self.apply_ban_rules(member=m)

        # task runs every 30 seconds; infinitely
        await asyncio.sleep(30)

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
