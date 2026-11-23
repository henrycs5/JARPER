import discord
from discord.ext import commands
from config import *

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        for guild in client.guilds:
            try:
                synced = await self.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to {guild.name} ({guild.id})')
            except Exception as e:
                print(f'Error syncing commands: {e}')
            
    async def on_message(self, message):
        if message.author == self.user: 
            return
        
        if message.content.startswith(data["YNC"]):
            await message.channel.send(data["BEPT"])
            
    async def on_reaction_add(self, reaction, user):
        await reaction.message.channel.send('💀')

class MessageLinkView(discord.ui.View):
    def __init__(self, message):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="Jump to Original Message",
                url=message.jump_url,
                style=discord.ButtonStyle.link
            )
        )

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = Client(command_prefix="!", intents=intents)
DEV_GUILD = discord.Object(id=GUILD_IDS["TESTING_ID"])
# COMMUNITY_GUILD = discord.Object(id=GUILD_IDS["TARGET_ID"])