# Work with Python 3.6
import os
import sys
import asyncio
import traceback
import discord, discord.ext.commands, discord.ext.tasks
from pprint import pprint
from aiohttp import connector
import random, signal

import time
import datetime

# swy: ugly discord.log file boilerplate
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(ch)

# swy: exit if we don't have a valid bot token
if not 'DISCORD_TOKEN' in os.environ:
  print('[!] Set your DISCORD_TOKEN environment variable to your Discord client secret.')
  sys.exit(-1)

# --
# swy: this discord.py cog includes a silly way of chatting with the babbling lizard, as well as offering a way to kill the bot completely.
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
    if message.author == self.bot.user or message.author.bot:
        return

    # swy: only handle private messages, ensure we are in DMs
    if isinstance(message.channel, discord.DMChannel):
        print("PM:", pprint(message), message.content, time.strftime("%Y-%m-%d %H:%M"))
        
        # swy: add an emergency killswitch; make it only work on selected moderation roles
        if message.content.lower().startswith('please stop'):
            for guild in self.bot.guilds:
                m = guild.get_member(message.author.id)
                if m and any(x in str(m.roles) for x in ['THQ Nordic', 'Titan (Owners)', 'Pharaohs (Admins)', 'Demigods (Mods)', 'Ambassador']):
                    await message.add_reaction('👌')
                    await message.channel.send("Disengaging.")
                    # swy: make it go inmediately offline and then exit the client
                    await self.bot.change_presence(status=discord.Status.offline)
                    await self.bot.close()
                    print(f"[!] Moderation user {message.author} requested an emergency shutdown")
                    return
        
        await asyncio.sleep(random.randint(4, 6))
        async with message.channel.typing():
            # swy: useful for testing
            messages = ["Weeeeeeeeee", "Groook", "Prreeeeeah", "Krr", "Chrurr", "Waaaeiaah", "Uhhhhwaaeee", "Roooohoo", "Wooheeee", "Woohioooaaa", "Aaarf", "Grrr", "Baaaaaouououo", "Hooorrrr", "Ooof", "Oofgh", "Grkarkarka", "Shheefgg", "Brrbrbr", "Uggeeeewewewww", "Prr-", "Jkafkapfff"]
            msg = "{0}, {1}.".format(random.choice(messages), random.choice(messages).lower())
            await asyncio.sleep(random.randint(2, 6))
            await message.channel.send(msg)

# --
# swy: this discord.py cog applies an «Unverified» role to any account that properly joins the server (i.e. not )
# swy: the final question will have three good and three bad answers, so have some extras of each to mix them up
questions = [
  {'question': 'Which character belongs to the game?', 'answers_good': ["Sphinx", "Tutankhamen", "Imhotep", "Horus", "Nefertiti"],                                                                                 'answers_bad': ["Link (the princess)", "Zelda (the guy with the sword)", "Master Chef", "The Four Horsemen", "Amaterasu", "Pepsiman", "Someone named Luigi" ]},
  {'question': 'Which location is part of the game?',  'answers_good': ["Luxor", "Heliopolis", "Abydos", "Uruk"],                                                                                                  'answers_bad': ["London", "Madrid", "Tokyo", "Athens", "Narnia", "Minas Tirith", "Hyrule", "Hogwarts", "Death Star"                      ]},
  {'question': 'Which thing belongs to the game?',     'answers_good': ["Gold Scarabs", "Blade of Osiris", "Shield of Osiris", "Hands of Amun", "Blowpipe (and magic darts)", "Capture Beetles", "Wings of Ibis"], 'answers_bad': ["Green Rupees", "Master Sword", "Boomerang", "Ocarina", "Fairy Slingshot", "Machete of Time", "Blue Cuccos", "Morph Gun" ]},
]

# swy: keep in mind that the bot needs the «Manage Roles» permission for user.remove_roles() and user.add_roles() to work.
class TldDiscordValidator(discord.ext.commands.Cog):
  def __init__(self, bot: discord.ext.commands.Bot, log_to_channel):
    self.bot = bot
    self.log_to_channel = log_to_channel
    print('[i] portal-god validator plug-in ready')

  @discord.ext.commands.Cog.listener()
  async def on_ready(self):
    self.channel_test = self.bot.get_channel( 470890531061366787) # Swyter test -- #general
    self.channel_door = self.bot.get_channel(1225464253415424022) # Sphinx and the Cursed Mummy -- #portal-god

    self.unverified_role = unverified_role = discord.utils.get(self.channel_door.guild.roles, name="Unverified")
    self.memberpass_role = memberpass_role = discord.utils.get(self.channel_door.guild.roles, name="Member")
    self.kick_stuck_members.start()

    # swy: there's a permanent message with a button (TldVerifyPresentation), when clicking it we
    #      create a random quiz (TldVerifyQuiz) that only the clicker can see
    class TldVerifyPresentation(discord.ui.View):
        def __init__(self):
          super().__init__(timeout=None)
          self.add_item(discord.ui.Button(label="Visit the Steam Community page", style=discord.ButtonStyle.link, url="https://steamcommunity.com/app/606710"))
#         self.add_item(discord.ui.Button(label="Submit bug reports",             style=discord.ButtonStyle.link, url="https://redmine.thqnordic.com/news/15"))

        @discord.ui.button(label="Verify my account", style=discord.ButtonStyle.blurple, custom_id='tld:verify')
        async def blurple_button(self, interaction: discord.Interaction, button: discord.ui.Button):
          await client.log_to_channel(interaction.user, f" has clicked on the verify button.")

          # swy: select one question from the lot
          rand_quest = random.choice(questions)

          # swy: randomize the order so that the first three aren't always the same
          random.shuffle(rand_quest['answers_good'])
          random.shuffle(rand_quest['answers_bad' ])

          # swy: get the first three of each after shuffling
          rand_answers_good = rand_quest['answers_good'][:1]
          rand_answers_bad  = rand_quest['answers_bad' ][:2]

          # swy: fill out the combobox; we need to randomize the order again after mixing the good and bad ones
          question_text = rand_quest['question']
          answers_all   = (rand_answers_good + rand_answers_bad); random.shuffle(answers_all); print("answers:", answers_all)
          ans_options   = [discord.SelectOption(label=cur_answer)  for cur_answer in answers_all]

          class TldVerifyQuiz(discord.ui.View):
              def __init__(self):
                super().__init__(timeout=120)
                self.rand_answers_good = rand_answers_good

              # swy: make a selector box with three good and three bad selectable options
              @discord.ui.select(placeholder=question_text, min_values=1, max_values=1, options=ans_options)
              async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
                print("click")

                # swy: make it 'think' when this has complete its function instead of answering again and again
                if unverified_role not in interaction.user.roles and len(interaction.user.roles) == 1:
                  #await interaction.response.defer(thinking=True, ephemeral=True)
                  return

                # swy: are all the options correct? even one bad one will cause it to fail
                if len(set(select.values).intersection(rand_answers_good)) != len(rand_answers_good):
                  await interaction.response.send_message(f"Darn, try again!", ephemeral=True)
                  await client.log_to_channel(interaction.user, f"has **failed** validation by responding {select.values}.")
                  return

                # swy: unquarantine the user by getting rid of this role
                if unverified_role:
                  await interaction.user.remove_roles(unverified_role)
                  await interaction.user.add_roles(memberpass_role)

                # swy: give the discord client a couple of seconds to refresh the available channel list after getting rid of the probation role.
                #      gotta love this stuff, otherwise it shows #not available instead of #rules.
                await interaction.response.send_message(f"Awesome! I like {select.values[0]} too!\nNow you are in. Head over to {interaction.guild.rules_channel.mention}.", ephemeral=True)
                await client.log_to_channel(interaction.user, f"has **passed** validation by responding {rand_answers_good}.")

                # swy: add a distinctive «badge» in the join log message to distinguish it from the people that get kicked out
                async for message in interaction.guild.system_channel.history(limit=60):
                  if message and message.is_system() and message.type == discord.MessageType.new_member and message.author == interaction.user:
                    print("trying to add reaction", message, pprint(message))
                    await message.add_reaction('💯')
                    break

          await interaction.response.send_message("Respond to the following question, or click on the button above again to get a different one:", view=TldVerifyQuiz(), ephemeral=True)

    # swy: make the first post's buttons persistent across bot reboots
    self.bot.add_view(TldVerifyPresentation())

    # swy: only make it send this message the first time around, disable it after that
    '''
    await self.channel_door.send(
      "As much as the team hates to do this, we've been receiving too much spam from new accounts lately. 🐧\n" +
      "So we need to make sure you are a real person to let you in. Pretty easy; a one-question quiz about *the game and Egyptian stuff*!", view=TldVerifyPresentation()
    )
    '''

  @discord.ext.commands.Cog.listener()
  async def on_member_join(self, member: discord.Member):
    print('User joined: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"))

    # swy: experiment: let veteran (pre-2020) accounts through unscathed, if they are still being used it's unlikely this is spam
    if self.memberpass_role and member.created_at <= datetime.datetime(2019, 12, 31, tzinfo=datetime.timezone.utc):
      await member.add_roles(self.memberpass_role)
      await client.log_to_channel(member, f" has **joined**. Account created at {member.created_at}; old enough to *skip* validation.")
      return
    # --

    await client.log_to_channel(member, f" has **joined**. Account created at {member.created_at}. Quarantining and adding *Unverified* role.")

    if self.unverified_role:
      await member.add_roles(self.unverified_role)
      mes = await self.channel_door.send(f"{member.mention}") # swy: ping them to make the hidden channel pop up more
      await mes.delete(delay=2) # swy: phantom ping

  @discord.ext.tasks.loop(seconds=30)
  async def kick_stuck_members(self):
    for member in self.unverified_role.members:
      # swy: ignore users (with more roles than just this and @everyone) that may have this role for testing or to mess around
      if len(member.roles) > 2:
        continue

      # swy: if the member with the «Unverified» role has idled more than 10 minutes in the gate since
      #      joining, then kick them out; they can still safely rejoin later if they want to :-)
      then = member.joined_at; now = datetime.datetime.now(datetime.timezone.utc)

      if (now - then) > datetime.timedelta(minutes=10):
        await client.log_to_channel(member, f"is getting **kicked** for being on quarantine for too long.")
        await member.kick(reason='bot: waited too long before passing the test')

  @discord.ext.commands.Cog.listener()
  async def on_member_remove(self, member: discord.Member):

    # swy: ignore users (with more roles than just Unverified + @everyone, or Member + @everyone) that may have these roles for testing or to mess around
    if len(member.roles) > 2:
      return
    
    # swy: only delete welcome messages from members who very recently joined (< 20 hours), don't delete stuff in the backlog from way back
    then = member.joined_at; now = datetime.datetime.now(datetime.timezone.utc)
    if (now - then) > datetime.timedelta(hours=20):
      return
    
    print('User left: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"))

    # swy: find if the user was kicked or banned by moderation (i.e. not this bot), or just left by itself, and show it
    was_kicked_or_banned = False; five_seconds_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)

    async for entry in member.guild.audit_logs(limit=100, after=five_seconds_ago):
      if entry.target == member and entry.action in [discord.AuditLogAction.kick, discord.AuditLogAction.ban]:
        was_kicked_or_banned = entry
        break

    if was_kicked_or_banned:
      if was_kicked_or_banned.user != self.bot.user: # swy: if we did the kick/ban then ignore it, there's already a message above
        await client.log_to_channel(member, f" has been **{was_kicked_or_banned.action is discord.AuditLogAction.kick and 'kicked' or 'banned'}** by {was_kicked_or_banned.user.mention}.")
    else:
      await client.log_to_channel(member, f" has **left** on its own.")

    # swy: remove the welcome message from #general if we kick them out or they leave after passing the quiz, suggested by @Medea Fleecestealer
    five_seconds_before_joining = member.joined_at - datetime.timedelta(seconds=5)

    async for message in member.guild.system_channel.history(limit=30, after=five_seconds_before_joining):
      if message and message.is_system() and message.type == discord.MessageType.new_member and message.author == member:
        print("trying to delete", message, pprint(message))
        await message.delete()

# --
# swy: implement our base discord.py bot thingie; it hosts the "cogs" we can attach to add extra functionality
#      it doesn't really do anything else by itself, other than having a common audit channel log function
class SphinxDiscordClient(discord.ext.commands.Bot):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  async def setup_hook(self):
    # swy: enable the silly goofy lizard reply plug-in
    await self.add_cog(SphinxDiscordGoofyLizard(self, self.log_to_channel))

    # swy: enable the member verification plug-in
    await self.add_cog(TldDiscordValidator(self, self.log_to_channel))

    def handle_exit(*args):
      raise KeyboardInterrupt
    if os.name != 'nt':
      loop = asyncio.get_running_loop()
      loop.add_signal_handler(signal.SIGTERM, handle_exit, signal.SIGTERM)
      loop.add_signal_handler(signal.SIGABRT, handle_exit, signal.SIGABRT, None)
      loop.add_signal_handler(signal.SIGINT,  handle_exit, signal.SIGINT) # swy: catch Ctrl-C, just in case: https://stackoverflow.com/a/1112350/674685

  async def close(self):
    # swy: cancel all lingering tasks and close shop
    await self.change_presence(status=discord.Status.offline)
    print("[-] exiting...")
    await super().close() # swy: https://stackoverflow.com/a/69684341/674685

  async def on_ready(self):
    # swy: see checker_background_task() for the initialized "global" variables
    print('Logged in as | ' + time.strftime("%Y-%m-%d %H:%M"))
    print(self.user.name)
    print(self.user.id)
    print('------')
    await self.change_presence(activity=discord.CustomActivity(name='Baaaaaouououo, krr.'))
    
    # swy: global variables for this client instance, all the other background tasks wait for post_init_event, so it's a good place
    self.channel_test   = self.get_channel( 470890531061366787) # Swyter test -- #general
    self.portal_god     = self.get_channel(1225464253415424022) # the #portal-god channel 
    self.portal_god_log = self.get_channel(1225486542597001316) # the #portal-god-log channel 

  async def log_to_channel(self, user: discord.Member, text):
    print(user, text); send_to_channel = user.guild.system_channel

    if self.portal_god_log and self.portal_god_log.guild == user.guild:
      send_to_channel = self.portal_god_log
    
    await send_to_channel.send(f"{user.mention} `{user.name}#{user.discriminator} ({user.id})` {text}")

  async def connect(self, *, reconnect: bool = True) -> None:
    print("connect")
    return await super().connect(reconnect=reconnect)
# --

intents = discord.Intents.default()
intents.members = True
intents.dm_messages = True
intents.guild_messages = True
intents.message_content = True

# swy: launch our bot thingie, allow for Ctrl + C
client = SphinxDiscordClient(intents=intents, command_prefix='goofyl')

try:
  while True:
    asyncio.run(client.start(os.environ["DISCORD_TOKEN"]))
except KeyboardInterrupt:
  print("[i] ctrl-c detected")
  asyncio.run(client.close()) # swy: make sure the bot disappears from the member list immediately
  sys.exit(130) # swy: means Bash's 128 + 2 (SIGINT) i.e. exiting gracefully
except Exception as e:
  print('  [!] loop error. Ignoring:', e)
  traceback.print_exc()
  pass