import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
from mcrcon import MCRcon  # Install with `pip install mcrcon`

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
PORT = 30120

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="n!", intents=intents)

required_role = "chack"

# Server IPs mapping
servers = {
    "Starcommunity 1": "141.98.19.62",
    "Starcommunity 2": "43.229.76.102",
    "Starcommunity 3": "141.98.19.46",
    "Starcommunity 4": "45.154.27",
    "Starcommunity 5": "43.229.151.105",
    "LAST STUDIO": "31.56.79.17",
    "WHAT TRAINING 1": "146.19.69.171",
    "WHAT TRAINING 2": "146.19.69.172",
    "Summer": "89.38.101.60",
    "Winter": "191.96.93.37",
    "Hyper": "89.38.101.50",
}




# Check if the server is online
async def check_server_info(server_ip):
    try:
        url = f"http://{server_ip}:{PORT}/info.json"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


# Check player details using RCON
async def check_players_with_rcon(channel, server_ip, player_id):
    try:
        with MCRcon(server_ip, RCON_PASSWORD, port=PORT) as mcr:
            response = mcr.command("status")
            await channel.send(f"🔍 RCON Response: ```{response}```")
    except Exception as e:
        await channel.send(f"⚠️ RCON connection error: {str(e)}")


# Main function to check player details
async def check_player(channel, server_ip: str, player_id: str):
    if not await check_server_info(server_ip):
        await channel.send(f"❌ Server `{server_ip}` is offline or unreachable."
                           )
        return

    url = f"http://{server_ip}:{PORT}/players.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            try:
                players = response.json()
            except ValueError:
                await channel.send("Server returned non-JSON data.")
                return

            player_data = next(
                (player
                 for player in players if str(player["id"]) == player_id),
                None)

            if player_data:
                await send_player_info(channel, server_ip, player_data,
                                       players)
            else:
                await channel.send(f"Player ID {player_id} not found.")
        else:
            await channel.send(
                f"Failed to fetch data from server. Status code: {response.status_code}"
            )
    except requests.RequestException as e:
        await channel.send(f"Connection error: {str(e)}")


# Send player details in an embed
async def send_player_info(channel, server_ip, player_data, players):
    player_name = player_data.get("name", "ไม่สามารถตรวจสอบได้e")
    discord_id = next((identifier.split(":")[1]
                       for identifier in player_data["identifiers"]
                       if identifier.startswith("discord")), None)
    steam_hex = next((identifier for identifier in player_data["identifiers"]
                      if "steam" in identifier), "ไม่สามารถตรวจสอบได้")
    ping = player_data.get("ping", "ไม่สามารถตรวจสอบได้")
    online_count = len(players)

    steam_link = generate_steam_link(steam_hex)
    discord_username, discord_mention, discord_avatar = await get_discord_info(
        discord_id)

    embed = discord.Embed(
        title=f"IP เซิฟเวอร์ที่ตรวจหาผู้เล่น {server_ip}",
        description=f"**ผู้เล่นที่ออนไลน์ทั้งหมด:** {online_count}",
        color=discord.Color.blurple())

    player_ip = next((identifier.split(":")[1]
                      for identifier in player_data["identifiers"]
                      if identifier.startswith("ip:")), "ไม่สามารถตรวจสอบได้")

    player_info = (f"**📖 ชื่อสตีมผู้เล่น:** {player_name}\n"
                   f"**🗞️ ID:** {player_data['id']}\n"
                   f"**💻 IP:** {player_ip}\n"
                   f"**💥 Ping:** {ping} ms\n"
                   f"**👤 ชื่อ Discord:** {discord_username}\n"
                   f"**🧬 Discord ID :** {discord_mention}\n"
                   f"**📜 Steam Hex:** {steam_hex}\n"
                   f"**🤖 Steam Profile:** {steam_link}")

    embed.add_field(name="ข้อมูลผู้เล่นที่ตรวจสอบ",
                    value=player_info,
                    inline=False)

    if discord_avatar:
        embed.set_thumbnail(url=discord_avatar)

    embed.set_footer(text=f"Search by {channel.guild.name}",
                     icon_url=channel.guild.icon.url)
    embed.set_author(
        name="JUTI FIVEM CHECKER",
        icon_url=
        "https://media.discordapp.net/attachments/1309517132161351782/1345355054865055785/giphy-downsized-large.gif?ex=67c43f08&is=67c2ed88&hm=c053257757f3a904c57d5bd2a2c462847fdb7b7388f074dc8a1c07255c72e5dd&="
    )

    await channel.send(embed=embed)


# Generate Steam profile link
def generate_steam_link(steam_hex):
    if steam_hex and steam_hex.startswith("steam:"):
        try:
            steam_id64 = int(steam_hex.split(":")[1], 16)
            return f"https://steamcommunity.com/profiles/{steam_id64}"
        except ValueError:
            return "Unable to convert Steam Hex to Steam ID 64"
    return "ไม่สามารถตรวจสอบได้"


# Get Discord user details
async def get_discord_info(discord_id):
    discord_username = "ไม่สามารถตรวจสอบได้"
    discord_mention = "-"
    discord_avatar = None

    if discord_id:
        try:
            discord_user = await bot.fetch_user(int(discord_id))
            discord_username = discord_user.name
            discord_mention = discord_user.mention
            discord_avatar = discord_user.avatar.url if discord_user.avatar else None
        except discord.NotFound:
            pass  # If Discord user not found, return default values

    return discord_username, discord_mention, discord_avatar


# Command to check player
@bot.command(name="p")
@commands.has_role(required_role)
async def check(ctx, player_id: str):
    if not player_id.isdigit():
        await ctx.send("Please enter a valid Player ID (numeric).")
        return

    await ctx.send(f"กำลังตรวจสอบหาข้อมูลผู้เล่น ID {player_id}...")

    class ServerSelect(discord.ui.Select):

        def __init__(self):
            options = [
                discord.SelectOption(label=server_name, value=server_ip)
                for server_name, server_ip in servers.items()
            ]
            super().__init__(placeholder="Select a server", options=options)

        async def callback(self, interaction: discord.Interaction):
            await check_player(ctx.channel, self.values[0], player_id)
            await interaction.response.defer()

    view = discord.ui.View()
    view.add_item(ServerSelect())

    await ctx.send(view=view)
    await ctx.message.delete()


# Run bot if TOKEN exists
if TOKEN:
    bot.run(TOKEN)
else:
    print("⚠️ Please set DISCORD_BOT_TOKEN in .env")
