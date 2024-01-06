def getUserinfo(cookie: str):
    with open("settings.json", "r", encoding = "utf8") as f: data = json.load(f)
    url = data['global']['url']['user']
    headers = {
        "User-Agent": data['global']['user_agent'],
        "Cookie": cookie
    }

    html = requests.get(url, headers = headers).text
    user = json.loads(html)

    username = user['name']
    return user

import core, DCBOTSET
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
from discord import app_commands
import json, requests

COLOR = 0x32A431

bot = commands.Bot(command_prefix=".", help_command=None, intents = discord.Intents.all())

try: tree = app_commands.CommandTree(bot)
except: tree = bot.tree

@bot.event
async def on_ready():
    print(f"> Logged as {str(bot.user)}")
    try: 
        await bot.tree.sync()
        print("> CommandTree Synced!")
    except: print("> [!]Failed to Sync CommandTree")

# /setcookie
class setCookieModal(Modal, title = "填入您在1campus.net的Cookie"):
    answer = discord.ui.TextInput(label = "不知道怎麼設置Cookie? 使用 /help 查看", style=discord.TextStyle.short, placeholder="填入您的Cookie於此...", required=True)
    async def on_submit(self, interaction:discord.Interaction):
        try: 
            user = bot.get_user(interaction.user.id)
            if user != None:
                with open("settings.json", "r", encoding = "utf8") as f: data = json.load(f)
                cookie = str(self.answer.value)
                campusUser = getUserinfo(cookie)

                data['users'][str(user.id)] = {"id":str(user.id), "cookie":str(self.answer.value)}
                with open("settings.json", "w", encoding = "utf8") as f: json.dump(data, f, ensure_ascii=False)

                embed = discord.Embed(color = COLOR, title = "Cookie設置完成")
                embed.add_field(name = "用戶名稱", value = campusUser['name'], inline = False)
                embed.add_field(name = "帳戶", value = campusUser['account'], inline = False)
                embed.add_field(name = "單位", value = campusUser['application'][0]['name'], inline = False)
                await interaction.response.send_message(embed = embed, ephemeral=True)
            else: await interaction.response.send_message("［！］Cookie設置失敗!", ephemeral=True)
        except: await interaction.response.send_message("［！］Cookie設置失敗!", ephemeral=True)
@tree.command(name="setcookie", description="設置Cookie")
async def setCookie(interaction:discord.Interaction): await interaction.response.send_modal(setCookieModal())

# /userinfo
@tree.command(name="checkuser", description="查看用戶資訊")
async def checkuser(interaction: discord.Interaction):
    try:
        user = bot.get_user(interaction.user.id)
        with open("settings.json", "r", encoding = "utf8") as f: data = json.load(f)

        if str(user.id) in data['users']:
            cookie = data['users'][str(user.id)]['cookie']
            campusUser = getUserinfo(cookie)

            embed = discord.Embed(color = COLOR, title = "用戶資料")
            embed.add_field(name = "用戶名稱", value = campusUser['name'], inline = False)
            embed.add_field(name = "帳戶", value = campusUser['account'], inline = False)
            embed.add_field(name = "單位", value = f"{campusUser['application'][0]['name']} - {campusUser['application'][0]['ap_name']}", inline = False)

            await interaction.response.send_message(embed = embed, ephemeral=True)
        else: await interaction.response.send_message("［！］Cookie未設置!", ephemeral=True)
    except: await interaction.response.send_message("［！］獲取資料時發生錯誤!", ephemeral=True)

# /msglist
@tree.command(name="msglist", description="查看訊息")
@app_commands.describe(page = "要顯示第幾頁", count = "每頁顯示多少訊息(每頁顯示訊息數)")
async def msglist(interaction: discord.Interaction, page:int, count:int):
    await interaction.response.defer(ephemeral=True, thinking=False)
    try:
        user = bot.get_user(interaction.user.id)
        with open("settings.json", "r", encoding = "utf8") as f: data = json.load(f)

        if str(user.id) in data['users']:
            token = core.getToken(str(user.id))
            if token != None:
                msg = core.MsgAccess(token)

                count = int(count)
                page = int(page)
                dataMsg = msg.listall(page, count)
                unreads = msg.unreadCount()

                texts = ""
                unreadCount = 0
                for d in dataMsg:
                    if d['read_time'] == None:
                        texts += "**[未讀]**"
                        unreadCount+=1
                    texts += f"[ID {d['message_id']}] ``{d['content']['title']}``\n來自: ``{d['content']['sender']}`` | 單位: ``{d['content']['dsns']}``\n\n"
                if texts == "": texts = "[未獲取任何訊息]"

                if len(texts) <= 1024:
                    embed = discord.Embed(color=COLOR, title = "訊息列表請求", description=f"每頁訊息量: {count} | 頁碼: {page} | 頁內未讀數: {unreadCount} / 總未讀數: {unreads}\n本次訊息顯示範圍: 最近第 {(page-1)*count+1} ~ {page*count} 條訊息")
                    embed.add_field(name = "獲取到的訊息", value=texts, inline=False)
                    embed.set_footer(text = "如要查看訊息內容，請至1campus app")
                    await interaction.followup.send(embed = embed, ephemeral=True)
                else: await interaction.followup.send(content="［！］獲取的訊息太多，DC的API不給我寄訊息，請降低每頁顯示訊息數", ephemeral=True)
            else: await interaction.followup.send(content="［！］Token獲取失敗!", ephemeral=True)
        else: await interaction.followup.send(content="［！］Cookie未設置!", ephemeral=True)
    except: await interaction.followup.send(content="［！］獲取資料時發生錯誤!", ephemeral=True)

# /fakeread
@tree.command(name="fakeread", description="假裝你好像已讀訊息")
@app_commands.describe(count = "訊息範圍(已讀到最近第x條訊息)")
async def fakeread(interaction: discord.Interaction, count:int):
    await interaction.response.defer(ephemeral=True, thinking=False)
    try:
        user = bot.get_user(interaction.user.id)
        with open("settings.json", "r", encoding = "utf8") as f: data = json.load(f)

        if str(user.id) in data['users']:
            token = core.getToken(str(user.id))
            if token != None:
                msg = core.MsgAccess(token)
                unreads = msg.unreadCount()

                count = int(count)
                dataMsg = msg.listall(1, count)
                unreadCount = 0
                for d in dataMsg: 
                    if d['read_time'] == None:
                        try: 
                            final = msg.fakeAlreadyRead(int(d['message_id']))
                            unreadCount+=1
                        except: pass
                
                unreadsAfter = msg.unreadCount()
                
                embed = discord.Embed(color=COLOR, title = "批量已讀訊息完成", description=f"請求訊息量: {count} / 實處理訊息量: {int(len(dataMsg))}\n本次偽造已讀: {unreadCount} / 處理前未讀量: {unreads} / 處理後未讀量: {unreadsAfter}")
                embed.set_footer(text = "看教官跟校安還抓不抓的到我")
                await interaction.followup.send(embed = embed, ephemeral=True)
            else: await interaction.followup.send(content="［！］Token獲取失敗!", ephemeral=True)
        else: await interaction.followup.send(content="［！］Cookie未設置!", ephemeral=True)
    except: await interaction.followup.send(content="［！］獲取資料時發生錯誤!", ephemeral=True)

# /help
@tree.command(name="help", description="使用指南")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title = "1Campus自動已讀訊息系統", description="之學務處100%抓不到我沒看訊息", color=COLOR)
    text = """```
/help - 顯示此指南
/setcookie - 設置Cookie，用於以您的身分存取系統
/checkuser - 用設置的Cookie查看您在1campus.net的個人資訊

/msglist <page> <count> - 查看訊息列表
<page> 要顯示第幾頁 <count> 每頁顯示多少訊息(每頁顯示訊息數)

/fakeread <count> - 批量已讀訊息
<count> 訊息範圍(已讀到最近第x條訊息)```"""
    embed.add_field(name = "📖 指令列表", value=text, inline=False)
    embed.add_field(name = "❓ 不知道如何設置Cookie?", value="點擊以下連結查看教學", inline = False)
    embed.add_field(name = "🦊 她是白上吹雪", value="一隻超可愛的狐狸~", inline = False)
    embed.set_image(url = "https://c.tenor.com/wm_jigc51u8AAAAC/tenor.gif")
    
    await interaction.response.send_message(embed = embed)

bot.run(DCBOTSET.TOKEN())

