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
    # Ignoruj zprávy od botů
    if message.author.bot:
        return

    # Kontrola, zda byl bot nebo ty (pokud běží na tvém účtu) zmíněn
    if client.user.mentioned_in(message):
        print(f"Detekována zmínka od {message.author}!")
        
        # Sestavení zprávy pro WhatsApp
        wa_text = (
            f"🔔 *Nová zmínka na Discordu*\n"
            f"👤 Od: {message.author.display_name}\n"
            f"💬 Zpráva: {message.clean_content}\n"
            f"📍 Kanál: #{message.channel.name}"
        )

        # Odeslání na WhatsApp
        try:
            response = greenAPI.sending.sendMessage(WA_GROUP_ID, wa_text)
            if response.code == 200:
                print("Oznámení úspěšně odesláno na WhatsApp.")
            else:
                print(f"Chyba při odesílání: {response.error}")
        except Exception as e:
            print(f"Nastala neočekávaná chyba: {e}")

client.run(DISCORD_TOKEN)