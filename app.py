# ============================================================
#  YouTube Downloader Bot — Render edition (Webhook)
#  اجرا روی Render.com (رایگان). دانلود با نت Render، ارسال به تلگرام.
#  توکن از Environment Variable خونده می‌شه.
# ============================================================
import os
import threading
import telebot
from telebot import types
import yt_dlp
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN رو توی Environment تنظیم کن!")

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")
if not WEBHOOK_URL:
    raise SystemExit("WEBHOOK_URL رو تنظیم کن (آدرس render.com خودت)")

bot = telebot.TeleBot(BOT_TOKEN)

_YDL_BASE = {
    "quiet": True,
    "no_warnings": True,
    "remote_components": "ejs:github",
    "js_runtimes": {"deno": {}},
}
if os.path.exists("cookies.txt"):
    _YDL_BASE["cookiefile"] = "cookies.txt"
    print("cookies.txt پیدا شد")


def download(url, mode="video"):
    out = "/tmp/%(title).40s.%(ext)s"
    opts = dict(_YDL_BASE)
    opts["outtmpl"] = out
    if mode == "audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
    else:
        opts["format"] = "best[ext=mp4]/best"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


@bot.message_handler(commands=["start", "help"])
def start(m):
    bot.reply_to(m, "لینک یوتیوب بفرست تا دانلود کنم.\n/audio برای صدا، /video برای ویدیو")


mode = {"audio": False}


@bot.message_handler(commands=["audio"])
def audio_mode(m):
    mode["audio"] = True
    bot.reply_to(m, "حالت صدا. لینک بفرست.")


@bot.message_handler(commands=["video"])
def video_mode(m):
    mode["audio"] = False
    bot.reply_to(m, "حالت ویدیو. لینک بفرست.")


@bot.message_handler(func=lambda m: m.text and "youtu" in m.text)
def handle(m):
    url = m.text.strip()
    bot.reply_to(m, "در حال دانلود... ⏳")
    try:
        path = download(url, "audio" if mode["audio"] else "video")
        with open(path, "rb") as f:
            if mode["audio"]:
                bot.send_audio(m.chat.id, f)
            else:
                bot.send_video(m.chat.id, f)
        os.remove(path)
    except Exception as e:
        bot.reply_to(m, f"خطا: {e}")


app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running."


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_data = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "", 200
    return "نوع درخواست نامعتبر", 403


def set_webhook():
    print("تنظیم webhook...")
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")


if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
