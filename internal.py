import discord
import aiohttp
import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from bot import * 

# ------------------------------------------------------------------- Compile -------------------------------------------------------------------
async def compile(interaction, start, end, archive: dict, guild_id: int):
    DISCORD_SERVER = client.get_guild(guild_id)
    TEST_SERVER = client.get_guild(GUILD_IDS["TESTING_ID"])
    print(f'Recapping {start.month}/{start.day}/{start.year} to {end.month}/{end.day}/{end.year} from {TEST_SERVER.name}! ({TEST_SERVER.id})')

    server_stats = archive["server_stats"]
    channels = archive["channel_ids"]
    assets = archive["assets"]

    for name in WRAP_CHANNELS: # ["summary", "files", "media", "gifs", "art"]
        channels[name] = discord.utils.get(interaction.guild.text_channels,name=f'{start.year}-{name}')
    
    for member in DISCORD_SERVER.members:
        if member.bot:
            continue
        if member.joined_at and member.joined_at.date() >= start.date():
            jarpmem = JARP_Member(member)
            server_stats["active_members"][member.id] = jarpmem
            server_stats["new_members"].append((member.joined_at, jarpmem))

    server_stats["new_members"].sort(key=lambda item: item[0], reverse=True)

    for key in CATEGORIES:
        category = interaction.guild.get_channel(CATEGORIES[key])
        if(category is not None):
            for channel in category.text_channels + category.voice_channels:
                async for message in channel.history(after=start, before=end, limit=None):
                    if message.author.bot:
                        continue

                    server_stats["messages"] +=1

                    user_id = message.author.id
                    if user_id in server_stats["active_members"]:
                        server_stats["active_members"][user_id].total_messages += 1
                    else:
                        server_stats["active_members"][member.id] = JARP_Member(member)

                    forward = None
                    if message.attachments or message.message_snapshots:
                        if message.message_snapshots:
                            forward = message.message_snapshots[0]

                        attachments = await get_attachments(message, forward)
                        if attachments:
                            turple = (message.created_at, attachments, message)
                            if channel.id == SPECIAL.get("art") or channel.id == SPECIAL.get("art_dummy"):
                                assets["art"].append(turple)
                            else:
                                assets["files"].append(turple)             
                    await get_embeds(message, forward, archive)
        
    assets["files"].sort(key=lambda item: item[0])
    assets["media"].sort(key=lambda item: item[0])
    assets["gifs"] = dict(sorted(assets["gifs"].items(), key=lambda item: (item[1]["count"], item[1]["last_used"]), reverse=True))
    server_stats["favorite_gif"] = [next(iter(assets["gifs"].values()))["gif_embed"]]
    assets["art"].sort(key=lambda item: item[0])

    for _, files, message in assets["files"]:
        await channels["files"].send(embeds=files, view = MessageLinkView(message))

    for _, media, message in assets["media"]:
        await channels["media"].send(embeds=media, view = MessageLinkView(message))
    
    for _, info in assets["gifs"].items():
        await channels["gifs"].send(embed=info["gif_embed"])

    for _, art, message in assets["art"]:
        await channels["art"].send(embeds=art, view = MessageLinkView(message))

    await condenseSummary(start, archive, channels)
# ---------------------------------------------------------------- Attachments ----------------------------------------------------------------
async def get_attachments(message, forward):
    attachments = []
    content = message
    if forward:
        content = forward

    for attached in content.attachments:
        embed = await attachment_embed(message)
        if forward: 
            embed.set_footer(text="Forwarded Message")
        if attached.url:
            embed.set_image(url=attached.url)
            
        embed.title = attached.filename
        embed.url = attached.url
        attachments.append(embed)

    return attachments

async def attachment_embed(message):
    embed = discord.Embed(
        title="Insert Title",
        color=discord.Color.blue()
    )
    embed.set_author(
        name=message.author.display_name,
        url=f"https://discord.com/users/{message.author.id}",
        icon_url=message.author.display_avatar.url
    )
    embed.add_field(
        name="Date",
        value=f"<t:{int(message.created_at.timestamp())}:F>",
        inline=False
    )
    return embed
# ------------------------------------------------------------------- Embeds --------------------------------------------------------------------
async def get_embeds(message, forward, archive: dict):
    gifs_store = archive["assets"]["gifs"]
    media_store = archive["assets"]["media"]
    stuff = message
    if forward:
        stuff = forward

    index = 0
    links = re.findall(r'https?://\S+', stuff.content)
    for url in links:
        if stuff.embeds and len(stuff.embeds) > index:  # If we have an embed why not just use that to our advantage than
            embed = stuff.embeds[index]                 # requesting an HTTPs request? The condition is used to act as an 
            if "gif" in url.lower():                    # edge case for links with and without embed previews.
                if url in gifs_store:
                    gifs_store[url]["count"] += 1
                    gifs_store[url]["last_used"] = message.created_at
                    gifs_store[url]["gif_embed"].set_field_at(0, name="GIF Count", value=gifs_store[url]["count"], inline=False)
                    gifs_store[url]["gif_embed"].set_field_at(1, name="Last Used", value=f'<t:{int(message.created_at.timestamp())}:R>', inline=False)
                else:
                    gif = await frequent_gifs(embed, url, message)
                    if "klipy" in url:
                        gif.set_image(url=embed.thumbnail.url)
                    else:
                        gif.set_image(url=embed.thumbnail.proxy_url)

                    gifs_store[url] = {
                        "count": 1,
                        "last_used": message.created_at,
                        "gif_embed": gif
                    }
            else:
                media = await og_embed(url, message)                # There's a reason why I have two duplicate og_embeds
                if forward:                                         # First to deal with embeds w/o previews.
                    media.set_footer(text="Forwarded Message")
                media_store.append((message.created_at, [media], message))
        else:
            media = await og_embed(url, message)                # Then to deal with links without embeds.
            if forward:                                         # It's more of a short circuit type of thing.
                media.set_footer(text="Forwarded Message")
            media_store.append((message.created_at, [media], message))
    index += 1

async def frequent_gifs(gif_embed, link, message):
    data = await get_og_data(link)

    embed = discord.Embed(
        title=data.get("title") or f'{gif_embed.url}',
        color=discord.Color.blue(),
        url=data.get("url") or gif_embed.url,
    )
    embed.add_field(
        name="GIF Count",
        value="1",
        inline=False
    )
    embed.add_field(
        name="Last Used",
        value=f'<t:{int(message.created_at.timestamp())}:R>',
        inline=False
    )
    return embed
# ------------------------------------------------------------------- Media --------------------------------------------------------------------
async def media_embed(message):
    embed = discord.Embed(
        color=discord.Color.blue()
    )
    embed.set_author(
        name=message.author.display_name,
        url=f"https://discord.com/users/{message.author.id}",
        icon_url=message.author.display_avatar.url
    )
    embed.add_field(
        name="Description",
        value=message.content,
        inline=False
    )
    embed.add_field(
        name="Date Sent",
        value=f'<t:{int(message.created_at.timestamp())}:R>',
        inline=False
    )
    return embed

async def og_embed(link, message):
    data = await get_og_data(link)
    embed = discord.Embed(
        title=data.get("title"),
        description=data.get("description"),
        color=discord.Color.blue(),
        url=link,
    )
    embed.set_author(
        name=message.author.display_name,
        url=f"https://discord.com/users/{message.author.id}",
        icon_url=message.author.display_avatar.url
    )

    if data.get("image"):
        embed.set_image(url=data["image"])

    if data.get("video"):
        embed.add_field(
            name="Video",
            value=f"[View Video]({data['video']})",
            inline=False
        )
    embed.add_field(
        name="Date Sent",
        value=f'<t:{int(message.created_at.timestamp())}:R>',
        inline=False
    )
    return embed
# -------------------------------------------------------------------- SUMMARY --------------------------------------------------------------------
async def condenseSummary(start, archive, channels):
    summaries = [
        await summary_stats(start, archive),
        await divider("Chronically Online JARP Member!"),
        await summary_active(archive),
        await divider("New Members!"),
        await summary_new(archive),
        await divider("JARP's Favorite GIF!"),
        archive["server_stats"]["favorite_gif"]
    ]
    for recap in summaries:
        for i in range(0, len(recap), 10):
            await channels["summary"].send(embeds=recap[i:i + 10])

async def summary_stats(start: datetime, archive: dict):
    embeds = []

    server_stats = archive["server_stats"]
    assets = archive["assets"]

    stats = discord.Embed(
        title=f'{start.year} Summary', 
        description="What's up my JARPERs?",
        color=discord.Color.blue()
    )
    stats.add_field(
        name="Server Stats",
        value=
        f'- {server_stats["messages"]} total messages!\n'
        f'- {await tuple_total(assets["files"])} total files!\n'
        f'- {await gif_total(assets["gifs"])} total gifs!\n'
        f'- {await tuple_total(assets["media"])} total media!\n'
        f'- {await tuple_total(assets["art"])} total artings!\n',
        inline=False
    )
    stats.add_field(
        name="New!",
        value=
        f'- {len(server_stats["new_members"])} new member(s)!',
        inline=False
    )
    stats.set_thumbnail(url=ICON)
    embeds.append(stats)

    return embeds

async def summary_active(archive: dict):
    archive["server_stats"]["active_members"] = dict(sorted(archive["server_stats"]["active_members"].items(), key=lambda member: member[1].total_messages, reverse=True))
    active_members = archive["server_stats"]["active_members"]
    embeds = []
    
    count = 1
    for _, member in list(active_members.items())[:5]:
        embed = await member.stats()
        embed.title = f'#{count} Chronically Online JARP Members'
        count += 1
        embeds.append(embed)
    return embeds

async def summary_new(archive: dict):
    archive["server_stats"]["new_members"].sort(key=lambda item: item[0])
    new_members = archive["server_stats"]["new_members"]
    embeds = []

    count = 1
    for _, member in new_members:
        embed = await member.stats()
        embed.title = f'NEW MEMBER #{count}!'
        count+=1
        embeds.append(embed)
    
    return embeds
# -------------------------------------------------------------------- HELPERS --------------------------------------------------------------------
async def create_wrap_year(interaction, start, wrap_year: str):
    category = await interaction.guild.create_category(wrap_year)
    for name in WRAP_CHANNELS:
        await interaction.guild.create_text_channel(f'{start.year}-{name}', category=category)

    await interaction.followup.send(f'{start.year} Wrap Categories Created!', ephemeral=True)

async def store_category(category, archive: dict):
    for channels in category.channels:
        archive[channels.name] = channels.id

async def tuple_total(assets: dict):
    total = 0
    for _, asset, _ in assets:
        total += len(asset)
    return total

async def gif_total(gifs: dict):
    total = 0

    for link in gifs:
        total += gifs[link]["count"]

    return total
async def divider(name: str):
    embed = discord.Embed(
        title=name,
        color=discord.Color.red()
    )
    return [embed]

async def get_og_data(url):
    url = normalize_url(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    data = {}

    for tag in soup.find_all("meta"):
        prop = tag.get("property")

        if prop and prop.startswith("og:"):
            data[prop[3:]] = tag.get("content")

    return data

def normalize_url(url):
    parsed = urlparse(url)

    if parsed.hostname and parsed.hostname.endswith("oginstagram.com"):
        parsed = parsed._replace(
            netloc="www.instagram.com",
            query="",
            fragment=""
        )

    return urlunparse(parsed)