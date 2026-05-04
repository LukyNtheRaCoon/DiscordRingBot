import discord
import os
from dotenv import load_dotenv
from whatsapp_api_client_python import API
from flask import Flask
from threading import Thread

# --- MINI WEB SERVER PRO RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ID_INSTANCE = os.getenv('ID_INSTANCE')
API_TOKEN = os.getenv('API_TOKEN')
WA_GROUP_ID = os.getenv('WA_GROUP_ID')

greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # Nastaví aktivitu (např. Sleduje WhatsApp)
    await client.change_presence(
        status=discord.Status.online, 
        activity=discord.Activity(type=discord.ActivityType.watching, name="WhatsApp")
    )
    print(f'Bot jede jako {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if client.user.mentioned_in(message):
        wa_text = f"🔔 *Discord zmínka*\n👤: {message.author.display_name}\n💬: {message.clean_content}"
        greenAPI.sending.sendMessage(WA_GROUP_ID, wa_text)

# Spuštění webu a bota
keep_alive()
client.run(DISCORD_TOKEN)