import discord
from datetime import datetime, timezone
from internal import *

async def wrap(interaction: discord.Interaction, year: int, guild_id: int, defer: bool):
    if defer:
        await interaction.response.defer(ephemeral=True)

    if guild_id is None:
        guild_id = GUILD_IDS["TESTING_ID"]
    elif client.get_guild(guild_id) is None:
        await interaction.edit_original_response(content='Invalid Guild ID')
        raise ValueError("Invalid Guild ID")
    
    DISCORD_SERVER = client.get_guild(guild_id)
    WRAP_NAME = DISCORD_SERVER.name
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime.now(timezone.utc)
    created =  DISCORD_SERVER.created_at
    wrap_year = f'{start.year} {WRAP_NAME}' # Category with the following name

    if(created.year <= start.year and start.year <= end.year):
        category =  discord.utils.get(interaction.guild.categories,name=wrap_year)
        
        if(category is None):
            archive = await make_archive()

            if(start.year == end.year): # If start is the same as end, wrap in that year's timeframe.
                if(start.date() < created.date()):
                    start = created              
            elif(start.year < end.year): # If start is before end, wrap the year from start to new years.  
                end = datetime(start.year + 1, 1, 1, tzinfo=timezone.utc)

            await create_wrap_year(interaction, start, wrap_year)   
            await compile(interaction, start, end, archive, guild_id)
            await interaction.followup.send(f'{wrap_year} Wrapped!', ephemeral=True)
            # all_wraps[wrap_year] = archive
        else:
            await interaction.edit_original_response(content=f'Bro you already have {wrap_year} are you stupid?')
    else:
        await interaction.edit_original_response(content=f'{wrap_year} predicts the dinosaurs')

# unwrap
async def unwrap(interaction: discord.Interaction, year: int, guild_id: int, defer: bool):
    if defer:
        await interaction.response.defer(ephemeral=True)

    if guild_id is None:
        guild_id = GUILD_IDS["TESTING_ID"]
    elif client.get_guild(guild_id) is None:
        await interaction.edit_original_response(content='Invalid Guild ID')
        raise ValueError("Invalid Guild ID")

    DISCORD_SERVER = client.get_guild(guild_id)
    WRAP_NAME = DISCORD_SERVER.name
    wrap_year = f'{year} {WRAP_NAME}' # Category with the following name to be deleted.
    category =  discord.utils.get(interaction.guild.categories,name=wrap_year)
    if(category is not None):
        for channels in interaction.guild.text_channels:
            if channels.category == category:
                await channels.delete()
        await category.delete()
        await interaction.edit_original_response(content=f'{wrap_year} was found and deleted!')
    else: 
        await interaction.edit_original_response(content=f'{wrap_year} was not found')