import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
liste_ouverte = True
presentes = []

def get_text():
    header = "✅ القائمة مفتوحة" if liste_ouverte else "🔒 القائمة مغلقة\nأُغلق التسجيل"
    if not presentes:
        corps = "\n\nلا توجد حاضرات بعد."
    else:
        corps = "\n\nقائمة الحاضرات:\n"
        for i, (_, name) in enumerate(presentes, 1):
            corps += f"- {name}\n"
    corps += f"\nعدد الحاضرات: {len(presentes)}"
    return f"{header}{corps}"

def get_keyboard(user_id, is_admin=False):
    buttons = []
    if liste_ouverte:
        buttons.append([InlineKeyboardButton("أنا حاضرة ✅", callback_data="je_suis_la")])
    else:
        buttons.append([InlineKeyboardButton("مغلقة ⛔", callback_data="ferme")])
    if is_admin:
        if liste_ouverte:
            buttons.append([InlineKeyboardButton("🔒 غلق القائمة", callback_data="fermer")])
        else:
            buttons.append([InlineKeyboardButton("🔓 فتح القائمة", callback_data="ouvrir")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "admin_id" not in context.bot_data:
        context.bot_data["admin_id"] = update.effective_user.id
    is_admin = update.effective_user.id == context.bot_data["admin_id"]
    await update.message.reply_text(get_text(), reply_markup=get_keyboard(update.effective_user.id, is_admin))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global liste_ouverte
    q = update.callback_query
    await q.answer()
    user = q.from_user
    is_admin = user.id == context.bot_data.get("admin_id")
    data = q.data
    if data == "je_suis_la":
        if not liste_ouverte:
            await q.answer("أُغلق التسجيل", show_alert=True)
            return
        if any(uid == user.id for uid, _ in presentes):
            await q.answer("أنت مسجلة بالفعل", show_alert=True)
            return
        presentes.append((user.id, user.first_name))
    elif data == "fermer" and is_admin:
        liste_ouverte = False
    elif data == "ouvrir" and is_admin:
        liste_ouverte = True
    elif data == "ferme":
        await q.answer("أُغلق التسجيل", show_alert=True)
        return
    await q.edit_message_text(get_text(), reply_markup=get_keyboard(user.id, is_admin))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
