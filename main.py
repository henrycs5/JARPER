import discord
import os
from dotenv import load_dotenv
from bot import * 
from cmds import *

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# --------------------------------------------------------------- GLOBAL COMMANDS ---------------------------------------------------------------
#wrap method
@client.tree.command(name="april-fools", description="I'VE PLAYED THESE GAMES BEFORE!", guild=DEV_GUILD)
async def printer(interaction: discord.Interaction):
    embed = discord.Embed(title="april fools", url="https://youtu.be/dQw4w9WgXcQ", description="Happy April Fools!", color=discord.Color.red())
    embed.set_thumbnail(url="https://media.tenor.com/bkl4kbX9g8EAAAAe/speedddd.png")
    await interaction.response.send_message(embed=embed)
# ----------------------------------------------------------------- TEST SERVER ------------------------------------------------------------------
@client.tree.command(name="wrap", description="Creates a new JARP year category.", guild=DEV_GUILD)
async def command_wrap(interaction: discord.Interaction, year: int, guild_id: int = None):
    await wrap(interaction, year, guild_id, True)

# unwrap method
@client.tree.command(name="unwrap", description="Deletes a specifc JARP year category and all associated channels.", guild=DEV_GUILD)
async def command_unwrap(interaction: discord.Interaction, year: int, guild_id: int = None):
    await unwrap(interaction, year, guild_id, True)

# rewrap method
@client.tree.command(name="rewrap", description="Reloads a JARP year category (deletes and creates)", guild=DEV_GUILD)
async def rewrap(interaction: discord.Interaction, year: int, guild_id: int = None):
    await interaction.response.defer(ephemeral=True)
    await unwrap(interaction, year, guild_id, False)
    await wrap(interaction, year, guild_id, False)
# ---------------------------------------------------------------------------------------------------------------------------------------------
client.run(TOKEN) # "You really think I would upload my Discord token like that?"