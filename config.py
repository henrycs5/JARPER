import discord
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from pathlib import Path
import json
# --------------------------------------------------------------------- ASSETS ---------------------------------------------------------------------
load_dotenv()
IDS = os.getenv("IDS")
file_path = Path(__file__).parent / IDS
with open(file_path) as file:
    data = json.load(file)

GUILD_IDS = data["GUILD_IDS"]
CATEGORIES = data["CATEGORIES"]
SPECIAL = data["SPECIAL"]

WRAP_CHANNELS = ["summary", "files", "media", "gifs", "art"]
ICON = data["ICON"]

history = {
    "total_messages": 0,
    "total_files": 0,
    "total_gifs": 0,
    "members": {}
}

async def make_archive():
    archive = {
        "server_stats": {
            "messages": 0,
            "active_members": {},
            "new_members": [],
            "favorite_gif": []
        },
        "channel_ids": {},
        "assets": {
            "files": [],
            "media": [], 
            "gifs": {}, 
            "art": []
        }
    }
    return archive
# ------------------------------------------------------------------ JARP_Member ------------------------------------------------------------------
class JARP_Member():
    def __init__(self, member):
        self.display_name = member.display_name
        self.user = member.name
        self.id = member.id
        self.avatar = member.display_avatar.url
        self.joined = member.joined_at
        self.total_messages = 0

    async def stats(self):
        embed = discord.Embed(
            description=
                f'- Sent {self.total_messages} messages this year!\n'
                f'- Joined <t:{int(self.joined.timestamp())}:R>',
            color=discord.Color.blue()
        )
        embed.set_author(
            name=f'@{self.display_name}',
            url=f"https://discord.com/users/{self.id}",
        )
        embed.set_thumbnail(url=self.avatar)
        return embed