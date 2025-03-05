import discord
import requests
import os
from discord.ext import commands
from dotenv import load_dotenv  # type: ignore
from mcrcon import MCRcon  # ติดตั้งด้วย `pip install mcrcon`

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="n!", intents=intents)

required_role = "chack"  # ยศที่สามารถใช้คำสั่งได้

servers = {
    "Starcommunity 1": "141.98.19.62",
    "Starcommunity 2": "43.229.76.102",
    "Starcommunity 3": "141.98.19.46",
    "Starcommunity 4": "45.154.27",
    "Starcommunity 5": "43.229.151.105",
    'LAST STUDIO': '31.56.79.17',
    "WHAT TRAINING 1": "146.19.69.171",
    "WHAT TRAINING 2": "146.19.69.172",
    "Summer": "89.38.101.60",
    "Winter": "191.96.93.37",
    "Hyper": "89.38.101.50",
}

PORT = 30120

async def check_server_info(server_ip):
    """ ฟังก์ชันเช็คว่าเซิร์ฟเวอร์ออนไลน์หรือไม่ """
    try:
        url = f"http://{server_ip}:{PORT}/info.json"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

async def check_players_with_rcon(channel, server_ip, player_id):
    """ ใช้ RCON เช็คข้อมูลผู้เล่น (ต้องตั้งค่า `sv_rcon_password` ใน server.cfg) """
    try:
        with MCRcon(server_ip, RCON_PASSWORD, port=PORT) as mcr:
            response = mcr.command("status")  # คำสั่งดึงข้อมูลผู้เล่น
            await channel.send(f"🔍 RCON Response: ```{response}```")
    except Exception as e:
        await channel.send(f"⚠️ ไม่สามารถเชื่อมต่อ RCON: {str(e)}")

async def check_player(channel, server_ip: str, player_id: str):
    try:
        # เช็คว่าเซิร์ฟเวอร์ออนไลน์หรือไม่
        if not await check_server_info(server_ip):
            await channel.send(f"❌ เซิร์ฟเวอร์ `{server_ip}` ออฟไลน์ หรือไม่สามารถเข้าถึงได้!")
            return

        url = f"http://{server_ip}:{PORT}/players.json"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            try:
                players = response.json()
            except ValueError:
                await channel.send("เซิร์ฟเวอร์ส่งข้อมูลที่ไม่ใช่ JSON")
                return
            
            player_data = next((player for player in players if str(player["id"]) == player_id), None)

            if player_data:
                player_name = player_data.get("name", "ไม่พบชื่อผู้เล่น")
                discord_id = next(
                    (identifier.split(":")[1] for identifier in player_data["identifiers"] if identifier.startswith("discord")),
                    None
                )
                steam_hex = next(
                    (identifier for identifier in player_data["identifiers"] if "steam" in identifier),
                    "ไม่พบ Steam Hex"
                )
                ping = player_data.get("ping", "ไม่พบ Ping")
                online_count = len(players)

                # แปลง Steam Hex เป็น Steam ID 64
                if steam_hex and steam_hex.startswith("steam:"):
                    try:
                        steam_id64 = int(steam_hex.split(":")[1], 16)
                        steam_link = f"https://steamcommunity.com/profiles/{steam_id64}"
                    except ValueError:
                        steam_link = "ไม่สามารถแปลง Steam Hex เป็น Steam ID 64"
                else:
                    steam_link = "ไม่พบลิงก์ Steam โปรไฟล์"

                # Discord User Info
                discord_username = "ไม่พบ Discord ID"
                discord_mention = "-"
                discord_avatar = None

                if discord_id:
                    try:
                        discord_user = await bot.fetch_user(int(discord_id))
                        discord_username = discord_user.name
                        discord_mention = discord_user.mention
                        discord_avatar = discord_user.avatar.url if discord_user.avatar else None
                    except discord.NotFound:
                        discord_username = "ไม่พบ Discord ID"
                        discord_mention = "-"
                        discord_avatar = None

                # Embed ข้อมูล
                embed = discord.Embed(
                    title=f"📊 ข้อมูลเซิร์ฟเวอร์ {server_ip}",
                    description=f"**จำนวนผู้เล่นออนไลน์:** {online_count}\n\n",
                    color=discord.Color.blurple()
                )

                player_ip = next(
                    (identifier.split(":")[1] for identifier in player_data["identifiers"] if identifier.startswith("ip:")),
                    "ไม่พบ IP"
                )

                player_info = (
                    f"**🗒️ ข้อมูลผู้เล่น**\n\n"
                    f"**⛳️ ชื่อผู้เล่น:** {player_name}\n"
                    f"**🪪 ID:** {player_id}\n"
                    f"**📡 IP Address:** {player_ip}\n"
                    f"**🏓 Ping:** {ping} ms\n"
                    f"**👤 ชื่อผู้ใช้ Discord:** {discord_username}\n"
                    f"**🔗 Discord Mention:** {discord_mention}\n"
                    f"**🎮 Steam Hex:** {steam_hex}\n"
                    f"**🌐 Steam Profile:** {steam_link}"
                )

                embed.add_field(name="ข้อมูลผู้เล่น", value=player_info, inline=False)

                if discord_avatar:
                    embed.set_thumbnail(url=discord_avatar)

                gif_url = "https://media.discordapp.net/attachments/1260172651578658907/1308675428050931712/Blue_and_Pink_Neon_Thanks_for_Watching_Video_1.gif"
                embed.set_image(url=gif_url)
                embed.set_footer(text=f"ค้นหาข้อมูลโดย {channel.guild.name}", icon_url=channel.guild.icon.url)
                embed.set_author(name="FiveM Player Checker", icon_url="https://pluspng.com/logo-img/fi13fiv6efe-fivem-logo-fivem-icon-in-color-style.png")

                await channel.send(embed=embed)
            else:
                await channel.send(f"ไม่พบข้อมูลสำหรับ Player ID: {player_id}")
        else:
            await channel.send(f"ไม่สามารถดึงข้อมูลได้จากเซิร์ฟเวอร์. Status code: {response.status_code}")
    except requests.RequestException as e:
        await channel.send(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {str(e)}")

@bot.command(name="p")
@commands.has_role(required_role)
async def check(ctx, player_id: str):
    await ctx.send(f"กำลังตรวจสอบข้อมูลของผู้เล่น {player_id}")

    if not player_id.isdigit():
        await ctx.send("กรุณากรอก Player ID ที่ถูกต้อง (หมายเลข)")
        return

    class ServerSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=server_name, value=server_ip)
                for server_name, server_ip in servers.items()
            ]
            super().__init__(placeholder="เลือกเซิร์ฟเวอร์", options=options)

        async def callback(self, interaction: discord.Interaction):
            await check_player(ctx.channel, self.values[0], player_id)
            await interaction.response.defer()

    view = discord.ui.View()
    view.add_item(ServerSelect())

    await ctx.send(view=view)
    await ctx.message.delete()


if TOKEN:
    bot.run(TOKEN)
else:
    print("⚠️ กรุณาตั้งค่า DISCORD_BOT_TOKEN ใน .env")
