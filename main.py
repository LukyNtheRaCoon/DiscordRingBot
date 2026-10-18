import os
import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from whatsapp_api_client_python import API

# Načtení souboru .env
load_dotenv()

# Načtení proměnných z prostředí
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ID_INSTANCE = os.getenv('ID_INSTANCE')
API_TOKEN = os.getenv('API_TOKEN')
WA_GROUP_ID = os.getenv('WA_GROUP_ID')

# Watchdog konfigurace pro upozornění
MOD_CHANNEL_ID = os.getenv('MOD_CHANNEL_ID')
ALERT_USER_ID = os.getenv('ALERT_USER_ID')
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))

# Inicializace WhatsApp API
greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN)

# Inicializace Discord Bota
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Sledování posledního známého stavu (zamezí opakovanému spamu při každém cyklu)
last_known_state = None


async def send_status_alert(state: str, is_error: bool = True):
    """Odešle upozornění na stav GREEN-API instance do moderátorského kanálu."""
    if not MOD_CHANNEL_ID:
        print(f"[Watchdog] Varování: MOD_CHANNEL_ID není nastaven v .env! Stav: {state}")
        return

    try:
        channel_id = int(MOD_CHANNEL_ID)
        channel = client.get_channel(channel_id)
        if channel is None:
            channel = await client.fetch_channel(channel_id)

        if not channel:
            print(f"[Watchdog] Kanál s ID {channel_id} nebyl nalezen.")
            return

        user_mention = f"<@{ALERT_USER_ID}>" if ALERT_USER_ID else "@moderátor"

        if is_error:
            msg = (
                "🚨 **VÝSTRAHA: GREEN-API (WHATSAPP) ODPOJENO** 🚨\n"
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"{user_mention} Pozor, na GREEN-API došlo k **odpojení autorizace bota**!\n\n"
                f"📌 **Aktuální stav instance:** `{state}`\n"
                "⚠️ Notifikace z Discordu se teď **nebudou doručovat** na WhatsApp.\n"
                "👉 Prosím přihlaste se do konzole GREEN-API a obnovte autorizaci (naskenujte znovu QR kód).\n"
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
            )
        else:
            msg = (
                "✅ **GREEN-API: SPOJENÍ OBNOVENO**\n"
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"WhatsApp instance je opět v pořádku autorizována (`{state}`).\n"
                "Přeposílání notifikací z Discordu je znovu plně funkční.\n"
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
            )

        await channel.send(msg)
    except Exception as err:
        print(f"[Watchdog] Chyba při odesílání upozornění na Discord: {err}")


@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_whatsapp_status():
    """Periodicky dotazuje stav instance na GREEN-API."""
    global last_known_state

    try:
        response = await asyncio.to_thread(greenAPI.account.getStateInstance)
        if response and response.code == 200 and isinstance(response.data, dict):
            current_state = response.data.get('stateInstance', 'unknown')
        else:
            error_detail = getattr(response, 'error', None) or getattr(response, 'code', 'neznámý kód')
            current_state = f"Chyba API ({error_detail})"
    except Exception as e:
        current_state = f"Chyba spojení ({e})"

    print(f"[Watchdog] Kontrola stavu Green-API: {current_state}")

    # Reakce na změnu stavu
    if current_state != last_known_state:
        if current_state != 'authorized':
            await send_status_alert(current_state, is_error=True)
        elif last_known_state is not None and current_state == 'authorized':
            await send_status_alert(current_state, is_error=False)

        last_known_state = current_state


@check_whatsapp_status.before_loop
async def before_check_whatsapp_status():
    await client.wait_until_ready()


@client.event
async def on_ready():
    print(f'Bot běží! Přihlášen jako {client.user}')
    print('Hlídám zmínky...')
    if not check_whatsapp_status.is_running():
        check_whatsapp_status.start()
        print(f'Watchdog WhatsAppu spuštěn (interval kontroly: {CHECK_INTERVAL_MINUTES} minut).')


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

        try:
            await asyncio.to_thread(greenAPI.sending.sendMessage, WA_GROUP_ID, wa_text)
        except Exception as e:
            print(f"Chyba při odesílání zprávy do WhatsApp: {e}")


client.run(DISCORD_TOKEN)