main.py import os
import logging
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ANIMENOSUB_URL = "https://animenosub.to"

def search_animenosub(query):
    try:
        url = f"{ANIMENOSUB_URL}/search?keyword={query}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".film_list-wrap .flw-item")

        results = []
        for item in items:
            title = item.select_one(".dynamic-name") or item.select_one(".film-name")
            link = ANIMENOSUB_URL + item.a["href"]
            image = item.img["data-src"]
            if title:
                results.append({
                    "title": title.text.strip(),
                    "url": link,
                    "thumbnail": image
                })
        return results
    except Exception as e:
        logging.error(f"Error searching: {e}")
        return []

@app.route("/", methods=["GET"])
def index():
    return "Animenosub Bot Running."

@app.route("/api/animenosub", methods=["POST"])
def api_search():
    data = request.json
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Query required"}), 400

    results = search_animenosub(query)
    return jsonify(results)

async def handle_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /get animenosub <query>")
        return

    source = context.args[0].lower()
    query = " ".join(context.args[1:])

    if source != "animenosub":
        await update.message.reply_text("Currently only 'animenosub' is supported.")
        return

    results = search_animenosub(query)
    if not results:
        await update.message.reply_text("No results found.")
        return

    for res in results[:5]:  # limit to 5
        message = f"📺 *{res['title']}*\n🔗 [Watch]({res['url']})"
        await update.message.reply_photo(photo=res['thumbnail'], caption=message, parse_mode='Markdown')

def run_telegram():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("get", handle_get))
    app_telegram.run_polling()

if __name__ == "__main__":
    import threading

    t = threading.Thread(target=run_telegram)
    t.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
