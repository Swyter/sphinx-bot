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


# swy: the final question will have three good and three bad answers, so have some extras of each to mix them up
questions = [
  {'question': 'Which of these characters belong to the game?',   'answers_good': ["Sphinx", "Tutankhamen", "Imhotep", "Horus", "Nefertiti"],                                                                                 'answers_bad': ["Link (the princess)", "Zelda (the guy with the sword)", "Jade", "The Four Horsemen", "Amaterasu", "Jak", "Daxter"       ] },
  {'question': 'Which of these locations are part of game?',      'answers_good': ["Luxor", "Heliopolis", "Abydos", "Uruk"],                                                                                                  'answers_bad': ["London", "Madrid", "Tokyo", "Athens", "Narnia", "Minas Tirith", "Hyrule", "Hillys", "Haven City"                        ] },
  {'question': 'Which of these things belong to the game?',       'answers_good': ["Gold Scarabs", "Sword of Osiris", "Shield of Osiris", "Hands of Amun", "Blowpipe (and magic darts)", "Capture Beetles", "Wings of Ibis"], 'answers_bad': ["Green Rupees", "Master Sword", "Boomerang", "Ocarina", "Fairy Slingshot", "Machete of Time", "Blue Cuccos", "Morph Gun" ] },
]

class TldDiscordValidator(discord.ext.commands.Cog):
  def __init__(self, bot: discord.ext.commands.Bot, log_to_channel):
    self.bot = bot
    self.log_to_channel = log_to_channel

    print('[i] portal-god validator plug-in ready')

  @discord.ext.commands.Cog.listener()
  async def on_ready(self):
    self.channel_test = self.bot.get_channel( 470890531061366787) # Swyter test -- #general
    self.channel_door = self.bot.get_channel(1225464253415424022) # Sphinx and the Cursed Mummy -- #portal-god

    self.kick_stuck_members.start()

    # swy: there's a permanent message with a button (TldVerifyPresentation), when clicking it we
    #      create a random quiz (TldVerifyQuiz) that only the clicker can see
    class TldVerifyPresentation(discord.ui.View):
        def __init__(self):
          super().__init__(timeout=None)
          self.add_item(discord.ui.Button(label="Visit the Steam Community page", style=discord.ButtonStyle.link, url="https://steamcommunity.com/app/606710"))

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
          answers_all   = (rand_answers_good + rand_answers_bad); random.shuffle(answers_all)
          ans_options   = [discord.SelectOption(label=cur_answer)  for cur_answer in answers_all]

          class TldVerifyQuiz(discord.ui.View):
              def __init__(self):
                super().__init__(timeout=30)
                self.rand_answers_good = rand_answers_good

              @discord.ui.select(placeholder=question_text, min_values=3, max_values=3, options=ans_options)
              async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
                print("click")

                # swy: are all the options correct? even one bad one will cause it to fail
                if len(set(select.values).intersection(rand_answers_good)) != len(rand_answers_good):
                  self.is_finished=True
                  await interaction.response.send_message(f"Darn, try again!", ephemeral=True)
                  await client.log_to_channel(interaction.user, f"has **failed** validation by responding {select.values}.")
                  return

                await interaction.response.send_message(f"Awesome! I like {select.values[0]} too!\nNow you are in. Head over to {interaction.guild.rules_channel.mention}.", ephemeral=True)

                # swy: unquarantine the user by getting rid of this role
                unverified_role = discord.utils.get(interaction.guild.roles, name="Unverified")

                if unverified_role:
                  await interaction.user.remove_roles(unverified_role)

                await client.log_to_channel(interaction.user, f"has **passed** validation by responding {rand_answers_good}.")

                # swy: add a distinctive «badge» in the join log message to distinguish it from the people that get kicked out
                async for message in interaction.guild.system_channel.history(limit=30):
                  if message.is_system() and message.type == discord.MessageType.new_member and message.author == interaction.user:
                    await message.add_reaction('💯')
                    break

          await interaction.response.send_message("Respond to the following question:", view=TldVerifyQuiz(), ephemeral=True)

    # swy: make the first post's buttons persistent across bot reboots
    self.bot.add_view(TldVerifyPresentation())

    #await self.channel_door.send(
    #  "As much as the team hates to do this, we've been receiving too much spam from new accounts lately. 🐧\n" +
    #  "So we need to make sure you are a real person to let you in. Pretty easy; a one-question quiz about *the game and Egyptian stuff*!", view=TldVerifyPresentation()
    #)

  @discord.ext.commands.Cog.listener()
  async def on_member_join(self, member : discord.Member):
    print('User joined: ', pprint(member), time.strftime("%Y-%m-%d %H:%M"))
    await client.log_to_channel(member, f" has **joined**. Account created at {member.created_at}. Quarantining and adding *Unverified* role.")

    unverified_role = discord.utils.get(member.guild.roles, name="Unverified")

    if unverified_role:
      await member.add_roles(unverified_role)
      mes = await self.channel_door.send(f"{member.mention}") # swy: ping them to make the hidden channel pop up more
      await mes.delete(delay=2) # swy: phantom ping

  @discord.ext.tasks.loop(seconds=30)
  async def kick_stuck_members(self):
    guild = self.channel_door.guild
    unverified_role = discord.utils.get(guild.roles, name="Unverified")
    
    for member in unverified_role.members:
      # swy: ignore users (with more roles than just this and @everyone) that may have this role for testing or to mess around
      if len(member.roles) > 2:
        continue

      then = member.joined_at; now = datetime.datetime.now(datetime.timezone.utc)

      if (now - then) > datetime.timedelta(minutes=10):
        await client.log_to_channel(member, f"is getting **kicked** for being on quarantine for too long.")
        await member.kick(reason='bot: waited too long before passing the test')


# swy: implement our bot thingie
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
client = SphinxDiscordClient(intents=intents, command_prefix=None)
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