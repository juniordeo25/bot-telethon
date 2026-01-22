from telethon import TelegramClient, events, errors
import asyncio, time, json, os, re, logging
from openpyxl import Workbook
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIG =================

API_ID = int(os.getenv("31791633"))
API_HASH = os.getenv("fe81844782af0bd9aa73e606c24da2c9")

GRUPO_ORIGEM = int(os.getenv("-1003228431851"))
GRUPO_DESTINO = int(os.getenv("-1003267506725"))
ADMIN_ID = int(os.getenv("1785910641"))

DRIVE_FOLDER_ID = os.getenv("1BJmSekM9aGm6n7wSnaDHsgEZlkejaB4k")

ARQ_MENSAL = "mensalidades.json"
ARQ_EXCEL = "mensalidades.xlsx"
CRED_FILE = "credentials.json"

PLANOS_VALIDOS = [1, 7, 15, 30]

logging.basicConfig(level=logging.INFO)

client = TelegramClient("userbot", API_ID, API_HASH)
mensalidades = {}

# ================= UTILS =================

def salvar_json(arq, dados):
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

def carregar_json(arq):
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def gerar_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "Mensalidades"

    ws.append(["User ID", "Username", "Vencimento"])

    for uid, d in mensalidades.items():
        ws.append([
            uid,
            d["username"],
            time.strftime("%d/%m/%Y", time.localtime(d["vencimento"]))
        ])

    wb.save(ARQ_EXCEL)

def enviar_drive():
    creds = service_account.Credentials.from_service_account_file(
        CRED_FILE,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )

    service = build("drive", "v3", credentials=creds)

    media = MediaFileUpload(
        ARQ_EXCEL,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    service.files().create(
        body={
            "name": ARQ_EXCEL,
            "parents": [DRIVE_FOLDER_ID]
        },
        media_body=media
    ).execute()

# ================= START =================

@client.on(events.NewMessage(from_users=ADMIN_ID, pattern=r"/ativar"))
async def ativar(event):
    partes = event.raw_text.split()
    if len(partes) != 3:
        return await event.reply("Use: /ativar @user dias")

    alvo = partes[1].replace("@", "")
    dias = int(partes[2])

    if dias not in PLANOS_VALIDOS:
        return await event.reply("Dias inválidos")

    user = await client.get_entity(alvo)
    agora = time.time()

    venc = agora + (dias * 86400)

    mensalidades[str(user.id)] = {
        "username": f"@{user.username}" if user.username else user.first_name,
        "vencimento": venc
    }

    salvar_json(ARQ_MENSAL, mensalidades)
    gerar_excel()
    enviar_drive()

    await event.reply(
        f"✅ Plano ativado\n"
        f"👤 {mensalidades[str(user.id)]['username']}\n"
        f"📅 Vence: {time.ctime(venc)}"
    )

async def main():
    global mensalidades
    mensalidades = carregar_json(ARQ_MENSAL)
    await client.start()
    print("✅ BOT ONLINE")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
