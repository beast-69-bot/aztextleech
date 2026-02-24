from pyrogram import Client, filters

API_ID = 34894897
API_HASH = "c17393d2c160bf3305b366747bcdb7e3"
BOT_TOKEN = "8572066127:AAE5HemuYGuqkNFHpk1elO4B6DT1l7xi9vo"

app = Client("mybot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    print(f">>> /start received from user: {message.from_user.id}")
    await message.reply_text("✅ Bot is working! Hello!")

@app.on_message(filters.command("yadav"))
async def yadav(client, message):
    print(f">>> /yadav received from user: {message.from_user.id}")
    await message.reply_text("✅ Yadav Ji Bot is working!")

@app.on_message(filters.text)
async def echo(client, message):
    print(f">>> Text received: {message.text}")
    await message.reply_text(f"Got: {message.text}")

print("Bot starting...")
app.run()
