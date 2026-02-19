# bot.py - Lógica principal del bot de Telegram

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
from groq_client import obtener_respuesta

load_dotenv()

# Estados de la conversación
ELIGIENDO_NIVEL = 1
CONVERSANDO = 2

# Historial por usuario (en memoria)
historiales = {}

# ── Servidor HTTP mínimo para Render ────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def iniciar_servidor():
    servidor = HTTPServer(("0.0.0.0", 10000), Handler)
    servidor.serve_forever()

# ── Comando /start ──────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [["🟢 Beginner", "🟡 Medium", "🔴 Advanced"]]
    markup = ReplyKeyboardMarkup(teclado, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "👋 Welcome to *English Practice Bot*!\n\n"
        "I'm here to help you practice English.\n"
        "First, choose your level:",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return ELIGIENDO_NIVEL

# ── El usuario elige nivel ───────────────────────────────
async def elegir_nivel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    user_id = update.effective_user.id

    mapa = {
        "🟢 Beginner": "beginner",
        "🟡 Medium": "medium",
        "🔴 Advanced": "advanced"
    }

    if texto not in mapa:
        await update.message.reply_text("Please choose one of the 3 buttons 👆")
        return ELIGIENDO_NIVEL

    nivel = mapa[texto]
    context.user_data["nivel"] = nivel
    historiales[user_id] = []

    mensajes_bienvenida = {
        "beginner": "🟢 Great! Let's start slow and simple.\nHello! How are you today? 😊",
        "medium":   "🟡 Good choice! Let's have a real conversation.\nSo, what have you been up to lately?",
        "advanced": "🔴 Excellent! Let's dive deep.\nWhat topic would you like to explore today?"
    }

    await update.message.reply_text(
        f"✅ Level set: *{texto}*\n\n{mensajes_bienvenida[nivel]}\n\n"
        "_(Type /change to switch level, /stop to end)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return CONVERSANDO

# ── Conversación principal ───────────────────────────────
async def conversar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mensaje = update.message.text
    nivel = context.user_data.get("nivel", "beginner")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    historial = historiales.get(user_id, [])
    respuesta = obtener_respuesta(mensaje, nivel, historial)
    historiales[user_id] = historial

    await update.message.reply_text(respuesta)
    return CONVERSANDO

# ── Cambiar nivel ────────────────────────────────────────
async def cambiar_nivel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [["🟢 Beginner", "🟡 Medium", "🔴 Advanced"]]
    markup = ReplyKeyboardMarkup(teclado, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Choose your new level:", reply_markup=markup)
    return ELIGIENDO_NIVEL

# ── Terminar conversación ────────────────────────────────
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Great practice today! See you next time!\n"
        "Type /start whenever you want to practice again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ── Main ─────────────────────────────────────────────────
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ELIGIENDO_NIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, elegir_nivel)],
            CONVERSANDO:     [MessageHandler(filters.TEXT & ~filters.COMMAND, conversar)],
        },
        fallbacks=[
            CommandHandler("change", cambiar_nivel),
            CommandHandler("stop", stop)
        ]
    )

    app.add_handler(conv_handler)

    # Inicia servidor HTTP para Render
    threading.Thread(target=iniciar_servidor, daemon=True).start()

    print("🤖 Bot running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()