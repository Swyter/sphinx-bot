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
    self.post_join_event = asyncio.Event()
    self.last_member_joined = datetime.utcfromtimestamp(0)
    self.member_heart = {}
    self.bg_task = self.loop.create_task(self.checker_background_task())
    
    
  async def on_ready(self):
    # swy: see checker_background_task() for the initialized "global" variables
    print('Logged in as | ' + time.strftime("%Y-%m-%d %H:%M"))
    print(self.user.name)
    print(self.user.id)
    print('------')
    
    # swy: global variables for this client instance, all the other background tasks wait for post_init_event, so it's a good place
    self.channel_test   = self.get_channel(470890531061366787) # Swyter test -- #general
    self.moderation_log = self.get_channel(545777338130890752) # the #moderation-log channel
    self.post_init_event.set()
    
    
  async def apply_ban_rules(self, member=None, on_member_join=False, on_member_update=False):
    # swy: sanity check; ensure that at least we have a member
    assert(member)
        
    # swy: only apply these rules to unverified users as a basic safeguard (they only have one role; called @everyone)
    #      if this member has more than one role, skip it. that's it.
    if len(member.roles) > 1:
        return
        
    time_since_creation    = (member.joined_at - member.created_at)
    seconds_since_creation = time_since_creation.total_seconds()
    
    time_since_joining     = (datetime.utcnow() - member.joined_at)
    seconds_since_joining  = time_since_joining.total_seconds()
    
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
        'fc3e70aec60efb5b7f48c9bf6c34db3a', # https://cdn.discordapp.com/avatars/682516445887987714/fc3e70aec60efb5b7f48c9bf6c34db3a.png?size=128
        'f2f5fe1ad679ceb59787cb1b5853168f', # https://cdn.discordapp.com/avatars/682599331433545760/f2f5fe1ad679ceb59787cb1b5853168f.png?size=128
    ]
    
  # print("   Member status:", member.name, member.discriminator, member.id, member.status, member.mobile_status, member.desktop_status, member.web_status, member.activity, member.avatar, time_since_joining, seconds_since_joining)
    
    # swy: add a heartbeat detector during the first 120 seconds, to detect a modicum of user activity in new accounts
    if (member.id in self.member_heart and member.status is not discord.Status.offline and seconds_since_joining <= 120):
        self.member_heart[member.id] += 1 * on_member_update # organic movement is worth a lot more than just sitting there
        print("MMBSTTE", member.id, self.member_heart, seconds_since_joining)
    
    # swy: avatars repeatedly used by known spammers.
    if usr.avatar in blacklisted_avatars:
        reasons.append("Blacklisted [avatar](%s)." % usr.avatar_url)
    
    # swy: when the user is created within seconds of joining but already has a set avatar; not humanly possible.
    if on_member_join and (member.avatar or usr.avatar) and seconds_since_creation <= 30:
        reasons.append("Member instantly created with [avatar](%s)." % member.avatar_url)

    # swy: when the user is created within seconds of joining but already is set to offline; not humanly possible.
    heartbeats = self.member_heart.get(member.id, None)
    
    if heartbeats and heartbeats < 10 and seconds_since_creation <= 120 and seconds_since_joining >= 30:
        print("heartbeats", heartbeats, seconds_since_creation, seconds_since_joining)
        reasons.append("Member instantly created and joined as offline. Heartbeats: %u." % heartbeats)
        del self.member_heart[member.id] # swy: safeguard to get here only once

  # # swy: for some reason in newer bot accounts there's a mismatch between the member avatar and the profile avatar.       
  # if member.avatar != usr.avatar:
  #     reasons.append("Avatar mismatch between [member](%s) and [user](%s)." % (member.avatar_url, usr.avatar_url))
    
  #  if member.hypesquad and (datetime.utcnow() - member.created_at).days <= 3:
  #      reasons.append("3 day-old account with HypeSquad.")
    
    if reasons:
        embed = discord.Embed(colour=discord.Colour(0x1b2148), title='Reasons', description=(" - " + "\n - ".join(reasons)))
        
        embed.set_thumbnail(url=usr.avatar_url)
        embed.add_field(name='➥ Seconds since creation', value=seconds_since_creation, inline=True)
        embed.add_field(name='➥ Seconds since joining',  value=seconds_since_joining,  inline=True)
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
    
    # swy: last_member_joined improves the cadence of checker_background_task(), and with the post_join_event we can skip the wait.
    #      if member_heart is set to zero we know that the member joined in this session, as there is not persistent storage
    self.last_member_joined = datetime.utcnow()
    self.member_heart[member.id] = 0
    self.post_join_event.set()
    self.post_join_event.clear()
    
    print('User joined: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"), member.avatar, member.created_at, "Seconds since account creation: " + str(seconds_since_creation), "Status", member.status, member.mobile_status, member.desktop_status, member.web_status, member.activity)
    reasons = await self.apply_ban_rules(member=member, on_member_join=True)
    
    # swy: while we didn't ban anyone we can still warn about fishy accounts
    if not reasons:
        if seconds_since_creation < 60:
            await self.moderation_log.send('The account {0.mention} was created only {1} seconds ago. Fishy. 🤔'.format(member, seconds_since_creation))
        elif seconds_since_creation < (60 * 60 * 2) and member.status == discord.Status.offline:
            await self.moderation_log.send('The account {0.mention} was created only {1} seconds ago and joined offline. Fishy. 🤔'.format(member, seconds_since_creation))
            

  async def on_member_update(self, before, after):
    if len(after.roles) > 1:
        return
  
    print("omu", before, after)
    
    # swy: we only care about status and activity changes; not role or nickname changes
    if (before.status == after.status and before.activity == after.activity):
        return

    if after and len(after.roles) <= 1:
        await self.apply_ban_rules(member=after, on_member_update=True)
  

  async def on_user_update(self, before, after):       
    print("ouu", before, after)
    
    # swy: we only care about avatar changes
    if (before.avatar == after.avatar):
        return

    # swy: ensure this is a member of the correct server; check that that it only has the default role
    for guild in self.guilds:
        m = guild.get_member(after.id)
    
    if m and len(m.roles) <= 1:
        await self.apply_ban_rules(member=m)


  async def on_message_delete(self, message):
    print('Deleted message:', pprint(message), message.content, time.strftime("%Y-%m-%d %H:%M"))


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


  async def checker_background_task(self):
    await self.wait_until_ready()
    print('[i] background ban checker ready')
    
    await self.post_init_event.wait()
    print('[i] running loop')
    
    while not self.is_closed():
        for guild in self.guilds:
            mem = guild.members
            for m in mem:
                time_since_creation    = (m.joined_at - m.created_at)
                seconds_since_creation = time_since_creation.total_seconds()

                if (seconds_since_creation <= 60 * 60 and len(m.roles) <= 1):
                  # print("ssc", m.name, m.discriminator, seconds_since_creation, time_since_creation, m.joined_at, m.created_at)
                    await self.apply_ban_rules(member=m)

            # task runs every 30 seconds; infinitely. but run at a faster rate right after someone joins to try to get more heartbeats
          # print("cadence", datetime.utcnow(), self.last_member_joined, (datetime.utcnow() - self.last_member_joined), (datetime.utcnow() - self.last_member_joined).total_seconds())
            if (datetime.utcnow() - self.last_member_joined).total_seconds() < 30:
                cadence = 1
            else:
                cadence = 30
                
        try:
            await asyncio.wait_for(self.post_join_event.wait(), timeout=cadence) # https://stackoverflow.com/a/49632779
        except asyncio.TimeoutError:
            pass
            
# swy: launch our bot thingie, allow for Ctrl + C
client = SphinxDiscordClient()

while True:
  try:
    client.loop.run_until_complete(client.start(os.environ["DISCORD_TOKEN"]))
  except KeyboardInterrupt:
    client.loop.run_until_complete(client.logout())
    # cancel all lingering tasks
  except e:
    print(e)
  finally:
    client.loop.close()
    sys.exit(0)
