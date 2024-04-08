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
logger.setLevel(logging.INFO)
handler_to_file = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler_to_file.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler_to_file)

handler_to_screen = logging.StreamHandler()
handler_to_screen.setLevel(logging.INFO)
handler_to_screen.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler_to_screen)

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
  {'question': 'Which characters belong to the game?',   'answers_good': ["Sphinx", "Tutankhamen", "Imhotep", "Horus", "Nefertiti"],                                                                                 'answers_bad': ["Link (the princess)", "Zelda (the guy with the sword)", "Master Chef", "The Four Horsemen", "Amaterasu", "Pepsiman", "Someone named Luigi" ]},
  {'question': 'Which locations are part of the game?',  'answers_good': ["Luxor", "Heliopolis", "Abydos", "Uruk"],                                                                                                  'answers_bad': ["London", "Madrid", "Tokyo", "Athens", "Narnia", "Minas Tirith", "Hyrule", "Hogwarts", "Death Star"                      ]},
  {'question': 'Which things belong to the game?',       'answers_good': ["Gold Scarabs", "Blade of Osiris", "Shield of Osiris", "Hands of Amun", "Blowpipe (and magic darts)", "Capture Beetles", "Wings of Ibis"], 'answers_bad': ["Green Rupees", "Master Sword", "Boomerang", "Ocarina", "Fairy Slingshot", "Machete of Time", "Blue Cuccos", "Morph Gun" ]},
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
          rand_answers_good = rand_quest['answers_good'][:3]
          rand_answers_bad  = rand_quest['answers_bad' ][:3]

          # swy: fill out the combobox; we need to randomize the order again after mixing the good and bad ones
          question_text = rand_quest['question']
          answers_all   = (rand_answers_good + rand_answers_bad); random.shuffle(answers_all); print("answers:", answers_all)
          ans_options   = [discord.SelectOption(label=cur_answer)  for cur_answer in answers_all]

          class TldVerifyQuiz(discord.ui.View):
              def __init__(self):
                super().__init__(timeout=60)
                self.rand_answers_good = rand_answers_good

              # swy: make a selector box with three good and three bad selectable options
              @discord.ui.select(placeholder=question_text, min_values=3, max_values=3, options=ans_options)
              async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
                print("click")

                # swy: are all the options correct? even one bad one will cause it to fail
                if len(set(select.values).intersection(rand_answers_good)) != len(rand_answers_good):
                  await interaction.response.send_message(f"Darn, try again!", ephemeral=True)
                  await client.log_to_channel(interaction.user, f"has **failed** validation by responding {select.values}.")
                  return

                # swy: unquarantine the user by getting rid of this role
                if unverified_role:
                  await interaction.user.remove_roles(unverified_role)

                # swy: give the discord client a couple of secconds to refresh the available channel list after getting rid of the probation role.
                #      gotta love this stuff, otherwise it shows #not available instead of #rules.
                await interaction.response.send_message(f"Awesome! I like {select.values[0]} too!\nNow you are in. Head over to {interaction.guild.rules_channel.mention}.", ephemeral=True)


                await client.log_to_channel(interaction.user, f"has **passed** validation by responding {rand_answers_good}.")

                # swy: add a distinctive «badge» in the join log message to distinguish it from the people that get kicked out
                async for message in interaction.guild.system_channel.history(limit=30):
                  if message and message.is_system() and message.type == discord.MessageType.new_member and message.author == interaction.user:
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
    await client.log_to_channel(member, f" has **joined**. Account created at {member.created_at}. Quarantining and adding *Unverified* role.")

    if self.unverified_role:
      await member.add_roles(self.unverified_role)
      mes = await self.channel_door.send(f"{member.mention} Hey, come here!") # swy: ping them to make the hidden channel pop up more
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

    if self.unverified_role not in member.roles:
      return
    
    print('User left: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"))
    was_kicked = False; five_seconds_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)

    async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, user=self.bot.user, limit=3, after=five_seconds_ago):
      if entry.target == member:
        was_kicked = True
        break
      
    if not was_kicked:
      await client.log_to_channel(member, f" has **left** on its own.")

    # swy: remove the welcome message from #general if we kick them out, suggested by @Medea Fleecestealer
    async for message in member.guild.system_channel.history(limit=30):
      if message and message.is_system() and message.type == discord.MessageType.new_member and message.author == member:
        print(message, pprint(message))
        await message.delete()
        break

# --
# swy: implement our base discord.py bot thingie; it hosts the "cogs" we can attach to add extra functionality
#      it doesn't really do anything else by itself, other than having a common audit channel log function
class SphinxDiscordClient(discord.ext.commands.Bot):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  async def setup_hook(self):
    self.loop.set_debug(True)

    # swy: enable the silly goofy lizard reply plug-in
    await self.add_cog(SphinxDiscordGoofyLizard(self, self.log_to_channel))

    # swy: enable the member verification plug-in
    await self.add_cog(TldDiscordValidator(self, self.log_to_channel))

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
      
# --

intents = discord.Intents.default()
intents.members = True

# swy: launch our bot thingie, allow for Ctrl + C
client = SphinxDiscordClient(intents=intents, command_prefix='goofyl')
loop = asyncio.get_event_loop()

def handle_exit():
    raise KeyboardInterrupt

if os.name != 'nt': # swy: if this isn't running on Windows (i.e. Linux/UNIX/macOS)
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
