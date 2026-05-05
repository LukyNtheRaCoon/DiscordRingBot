import discord
import os
from dotenv import load_dotenv
from whatsapp_api_client_python import API

# Načtení souboru .env
load_dotenv()

# Načtení proměnných z prostředí
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ID_INSTANCE = os.getenv('ID_INSTANCE')
API_TOKEN = os.getenv('API_TOKEN')
WA_GROUP_ID = os.getenv('WA_GROUP_ID')

# Inicializace WhatsApp API
greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN)

# Inicializace Discord Bota
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot běží! Přihlášen jako {client.user}')
    print('Hlídám zmínky...')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if client.user.mentioned_in(message):
        wa_text = (
            "🚨 *POZOR – DISCORD ZMÍNKA* 🚨\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"👤 *KDO:* {message.author.display_name}\n"
            f"💬 *TEXT:* {message.clean_content}\n\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"🔗 *ODKAZ NA ZPRÁVU:*\n"
            f"{message.jump_url}\n\n"
            "📢 *@všichni prosím čtěte!*"
        )
        
        greenAPI.sending.sendMessage(WA_GROUP_ID, wa_text)

client.run(DISCORD_TOKEN)