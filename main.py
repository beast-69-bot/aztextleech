import os
import random
import re
import sys
import time
import asyncio
import requests
import subprocess
import yt_dlp
import cloudscraper
from logs import logging
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, WEBHOOK, PORT
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from aiohttp import web

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ===== CONSTANTS =====
photologo = 'https://tinypic.host/images/2025/03/29/1000045854.th.jpg'
photoyt = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png'
photocp = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'

image_urls = [
    "https://tinypic.host/images/2025/03/29/1000045854.th.jpg",
    "https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png",
]

cookies_file_path = "youtube_cookies.txt"

# ===== HELPER FUNCTIONS =====

async def show_random_emojis(msg):
    emojis = ['🐼', '🐶', '🐅', '⚡️', '🚀', '✨', '💥', '☠️', '🥂', '🍾']
    emoji_message = await msg.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message


def clean_name(raw_name):
    """Clean a filename by removing special characters."""
    return raw_name.replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()


def get_resolution(quality_str):
    """Convert quality string to resolution."""
    res_map = {
        "144": "256x144",
        "240": "426x240",
        "360": "640x360",
        "480": "854x480",
        "720": "1280x720",
        "1080": "1920x1080"
    }
    return res_map.get(quality_str, "UN")


def get_yt_format(quality_str, url):
    """Get yt-dlp format string based on quality and URL type."""
    if "youtu" in url:
        return f"b[height<={quality_str}][ext=mp4]/bv[height<={quality_str}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
    else:
        return f"b[height<={quality_str}]/bv[height<={quality_str}]+ba/b/bv+ba"


async def process_url(url, quality_str, token=""):
    """Process URL - handle various platforms and return final URL."""
    # VisionIAS
    if "visionias" in url:
        async with ClientSession() as session:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 Chrome/107.0.0.0 Mobile Safari/537.36',
                'Referer': 'http://www.visionias.in/',
            }
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                if match:
                    url = match.group(1)

    # Classplus
    if 'classplusapp' in url:
        try:
            cp_headers = {'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}
            resp = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers=cp_headers)
            url = resp.json()['url']
        except Exception:
            pass

    # PhysicsWallah - Clean MPD URL and use PW API
    if "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
        # Extract IDs if present in the URL
        parent_id = None
        child_id = None
        if "&parentId=" in url:
            parent_id = url.split("&parentId=")[1].split("&")[0]
        if "&childId=" in url:
            child_id = url.split("&childId=")[1].split("&")[0]
            
        # Keep Original URL and Cleaned URL
        full_url = url
        clean_url = url.split("&parentId")[0].split("&childId")[0].strip()
        
        # Try PW API approach using token
        if token == "auto":
            # 1. Check Env Var (Persistent)
            token = os.environ.get("PW_TOKEN")
            # 2. Check File (Temporary/User set)
            if not token and os.path.exists("pw_token.txt"):
                with open("pw_token.txt", "r") as f:
                    token = f.read().strip()
            
            if not token:
                token = None

        if token and token not in ["", "default", "anything", "auto"]:
            pw_headers = {
                'Authorization': f'Bearer {token}',
                'x-auth-token': token,
                'Client-Type': 'WEB',
                'Organization-Id': '5eb393ee95fab7468a79d189',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Content-Type': 'application/json',
            }
            
            import urllib.parse
            
            # Endpoints to try with both clean and full URLs
            api_patterns = [
                "https://api.penpencil.co/v1/videos/get-url?url={}",
                "https://api.penpencil.co/v3/files/get-video-details?url={}",
                "https://api.penpencil.co/v3/files/get-signed-url?url={}"
            ]
            
            urls_to_test = [clean_url, full_url]
            
            for test_url in urls_to_test:
                encoded_test_url = urllib.parse.quote(test_url)
                for pattern in api_patterns:
                    api_url = pattern.format(encoded_test_url)
                    try:
                        resp = requests.get(api_url, headers=pw_headers, timeout=8)
                        if resp.status_code == 200:
                            data = resp.json()
                            playable_url = None
                            if 'data' in data:
                                if isinstance(data['data'], dict):
                                    playable_url = data['data'].get('url') or data['data'].get('videoUrl')
                            
                            if playable_url:
                                print(f"[PW API SUCCESS] Found playable URL via {api_url.split('/')[3]}")
                                return playable_url
                        else:
                            # Log only if not 404 to keep logs clean
                            if resp.status_code != 404:
                                print(f"[PW API DEBUG] {api_url.split('/')[3]} -> {resp.status_code}")
                    except Exception as e:
                        continue
            
            # Special case for parent/child IDs
            if parent_id and child_id:
                special_urls = [
                    f"https://api.penpencil.co/v3/files/{parent_id}/subject-content/{child_id}",
                    f"https://api.penpencil.co/v3/files/subject-contents/{child_id}?parentId={parent_id}"
                ]
                for s_url in special_urls:
                    try:
                        resp = requests.get(s_url, headers=pw_headers, timeout=8)
                        if resp.status_code == 200:
                            p_url = resp.json().get('data', {}).get('url')
                            if p_url: return p_url
                    except Exception: continue

            # Final Heroku Fallback
            try:
                heroku_url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={urllib.parse.quote(clean_url)}&token={token}"
                resp = requests.get(heroku_url, timeout=10)
                if resp.status_code == 200:
                    h_url = resp.json().get('url')
                    if h_url: return h_url
            except Exception: pass
        
        # Fallback to clean URL
        url = clean_url
        print(f"[PW] Returning Clean MPD URL as fallback")

    # Brightcove
    if "edge.api.brightcove.com" in url:
        bcov = 'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg'
        url = url.split("bcov_auth")[0] + bcov

    return url


def build_cmd(url, name, quality_str, token=""):
    """Build yt-dlp command based on URL type."""
    ytf = get_yt_format(quality_str, url)

    if "/master.mpd" in url:
        # For PW MPD, add headers if token is available
        if token == "auto":
            # 1. Check Env Var (Persistent)
            token = os.environ.get("PW_TOKEN")
            # 2. Check File (Temporary/User set)
            if not token and os.path.exists("pw_token.txt"):
                with open("pw_token.txt", "r") as f:
                    token = f.read().strip()
            
            if not token:
                token = None

        header_str = ""
        if "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
            if token and token not in ["", "default", "anything", "auto"]:
                header_str = (
                    f'--add-header "Authorization: Bearer {token}" '
                    f'--add-header "Organization-Id:5eb393ee95fab7468a79d189" '
                    f'--add-header "Client-Type:WEB" '
                    f'--add-header "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
                    f'--add-header "Origin:https://www.pw.live" '
                    f'--add-header "Referer:https://www.pw.live/"'
                )
        
        return f'yt-dlp -k --allow-unplayable-formats -f "bestvideo[height<={quality_str}]+bestaudio/best" --fixup never --no-check-certificates {header_str} "{url}" -o "{name}.mp4"'
    elif "acecwply" in url:
        return f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={quality_str}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
    elif "jw-prod" in url:
        return f'yt-dlp -o "{name}.mp4" "{url}"'
    elif "youtube.com" in url or "youtu.be" in url:
        return f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}.mp4"'
    else:
        return f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'


# ===== BOT INITIALIZATION =====
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===== WEBHOOK / WEB SERVER =====
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"status": "running"})

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def main():
    """Main function for VPS/Heroku deployment with webhook."""
    app_runner = web.AppRunner(await web_server())
    await app_runner.setup()
    site = web.TCPSite(app_runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server started on port {PORT}")

    await bot.start()
    print("Bot is up and running")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await bot.stop()


# ===== KEYBOARDS =====
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(text="📞 Contact", url="https://t.me/Yadav_ji_admin"),
        InlineKeyboardButton(text="🛠️ Help", url="https://t.me/Yadav_ji_admin"),
    ],
])


# ================================================================
#                     COMMAND HANDLERS
# ================================================================

@bot.on_message(filters.command(["start"]))
async def start_handler(client: Client, m: Message):
    """Handle /start command - show welcome message."""
    random_image_url = random.choice(image_urls)
    caption = (
        "𝐇𝐞𝐥𝐥𝐨 𝐃𝐞𝐚𝐫 👋!\n\n"
        "➠ 𝐈 𝐚𝐦 𝐚 𝐓𝐞𝐱𝐭 𝙔𝘼𝘿𝘼𝙑 𝙅𝙄 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐫 𝐁𝐨𝐭\n\n"
        "➠ Can Extract Videos & PDFs From Your Text File and Upload to Telegram!\n\n"
        "➠ For Guide Use Command /yadav 📖\n\n"
        "➠ 𝐌𝐚𝐝𝐞 𝐁𝐲 : 𝙔𝘼𝘿𝘼𝙑 𝙅𝙄 🦁"
    )
    try:
        await m.reply_photo(
            photo=random_image_url,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception:
        await m.reply_text(caption, reply_markup=keyboard)


@bot.on_message(filters.command(["yadav"]))
async def yadav_handler(client: Client, m: Message):
    """Handle /yadav command - show help/commands list."""
    await m.reply_text(
        "<pre><code> 🎉 𝙔𝘼𝘿𝘼𝙑 𝙅𝙄 Bot Commands :</code></pre>\n┣\n"
        "┣⪼ /start - Start the Bot\n┣\n"
        "┣⪼ /yadav - Show this help\n┣\n"
        "┣⪼ /yadavji - TXT File Downloader 📥\n┣\n"
        "┣⪼ /token - PW Token Extractor 🔑\n┣\n"
        "┣⪼ /cp - ClassPlus Stream Links\n┣\n"
        "┣⪼ /y2t - YouTube Playlist to .txt\n┣\n"
        "┣⪼ /cookies - Update YT cookies\n┣\n"
        "┣⪼ /logs - View Bot Logs\n┣\n"
        "┣⪼ /stop - Stop Running Task 🚫\n┣\n"
        "┣⪼🔗 Direct Send Link For Extract (with https://)\n┣\n"
        "<pre><code>If you have any questions, feel free to ask! 💬</code></pre>"
    )


@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    """Handle /cookies command - update YouTube cookies file."""
    await m.reply_text("Please upload the cookies file (.txt format).", quote=True)
    try:
        input_message: Message = await client.listen(m.chat.id)
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return
        downloaded_path = await input_message.download()
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)
        await input_message.reply_text("✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`.")
        os.remove(downloaded_path)
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")


# ================================================================
#              PW TOKEN EXTRACTOR (/token)
# ================================================================

@bot.on_message(filters.command(["token"]) & filters.private)
async def token_handler(client: Client, m: Message):
    """Handle /token command - extract PW auth token via phone + OTP."""
    
    editable = await m.reply_text(
        "🔑 **PW Token Extractor**\n\n"
        "📱 Enter your **PhysicsWallah registered phone number**\n"
        "(with country code, e.g., `918539926190`)\n\n"
        "⚠️ OTP will be sent to this number"
    )
    
    # Step 1: Get phone number
    input_phone: Message = await client.listen(m.chat.id)
    phone = input_phone.text.strip()
    await input_phone.delete(True)
    
    # Remove + if present
    phone = phone.replace("+", "").replace(" ", "")
    
    # Step 2: Send OTP via PW API
    await editable.edit("📲 **Sending OTP...**")
    
    try:
        otp_response = requests.post(
            "https://api.penpencil.co/v3/login/send-otp",
            json={
                "countryCode": "+91",
                "mobile": phone[-10:],  # Last 10 digits
                "organizationId": "5eb393ee95fab7468a79d189"
            },
            headers={
                'Content-Type': 'application/json',
                'Client-Type': 'WEB',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            },
            timeout=15
        )
        
        otp_data = otp_response.json()
        print(f"[TOKEN] OTP API Response: {otp_response.status_code} - {otp_data}")
        
        if otp_response.status_code != 200 or not otp_data.get('success', False):
            await editable.edit(
                f"❌ **OTP Send Failed**\n\n"
                f"Status: {otp_response.status_code}\n"
                f"Response: `{otp_data.get('message', 'Unknown error')}`\n\n"
                f"Make sure the phone number is registered with PhysicsWallah."
            )
            return
            
    except Exception as e:
        await editable.edit(f"❌ **Error sending OTP:** `{str(e)}`")
        return
    
    # Step 3: Get OTP from user
    await editable.edit(
        "✅ **OTP Sent Successfully!**\n\n"
        f"📱 Check your phone: `{phone[-10:]}`\n\n"
        "🔢 Enter the **4-digit OTP** received:"
    )
    
    input_otp: Message = await client.listen(m.chat.id)
    otp = input_otp.text.strip()
    await input_otp.delete(True)
    
    # Step 4: Verify OTP and get token
    await editable.edit("🔄 **Verifying OTP...**")
    
    try:
        verify_response = requests.post(
            "https://api.penpencil.co/v3/login/verify-otp",
            json={
                "countryCode": "+91",
                "mobile": phone[-10:],
                "otp": otp,
                "organizationId": "5eb393ee95fab7468a79d189"
            },
            headers={
                'Content-Type': 'application/json',
                'Client-Type': 'WEB',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            },
            timeout=15
        )
        
        verify_data = verify_response.json()
        print(f"[TOKEN] Verify OTP Response: {verify_response.status_code}")
        
        if verify_response.status_code == 200 and verify_data.get('success', False):
            token = verify_data.get('data', {}).get('token', '')
            
            if token:
                # Save token to file
                with open("pw_token.txt", "w") as f:
                    f.write(token)
                
                # Show success with masked token
                masked = token[:20] + "..." + token[-10:]
                await editable.edit(
                    "✅ **Token Extracted Successfully!** 🎉\n\n"
                    f"🔑 Token: `{masked}`\n\n"
                    "📁 Saved to: `pw_token.txt`\n\n"
                    "**Now use /yadavji and when bot asks for PW Token,**\n"
                    "**send `auto` to use this saved token!**"
                )
                
                # Also send full token as copyable message
                await m.reply_text(
                    f"📋 **Full Token (copy this):**\n\n`{token}`"
                )
            else:
                await editable.edit(
                    "❌ **Token not found in response**\n\n"
                    f"Response: `{str(verify_data)[:300]}`"
                )
        else:
            await editable.edit(
                f"❌ **OTP Verification Failed**\n\n"
                f"Response: `{verify_data.get('message', 'Invalid OTP')}`\n\n"
                "Try again with /token"
            )
            
    except Exception as e:
        await editable.edit(f"❌ **Error verifying OTP:** `{str(e)}`")


@bot.on_message(filters.command(["logs"]))
async def send_logs(client: Client, m: Message):
    """Handle /logs command - send log file."""
    try:
        if os.path.exists("logs.txt"):
            await m.reply_document(document="logs.txt", caption="📤 Bot Logs")
        else:
            await m.reply_text("No logs file found.")
    except Exception as e:
        await m.reply_text(f"Error sending logs: {e}")


@bot.on_message(filters.command(["stop"]))
async def stop_handler(_, m):
    """Handle /stop command - restart bot."""
    await m.reply_text("🫰 𝗦𝗧𝗢𝗣𝗘𝗗 🫰", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


# ================================================================
#              YOUTUBE PLAYLIST TO TXT (/y2t)
# ================================================================

@bot.on_message(filters.command(["y2t"]))
async def youtube_to_txt(client: Client, m: Message):
    """Handle /y2t command - convert YouTube playlist to .txt file."""
    await m.reply_text(
        "<pre><code>Welcome to YouTube to .txt🗃️ Converter!</code></pre>\n"
        "<pre><code>Please Send YouTube Playlist link.</code></pre>\n"
    )

    input_msg: Message = await client.listen(m.chat.id)
    youtube_link = input_msg.text.strip()
    await input_msg.delete(True)

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'forcejson': True,
        'cookies': cookies_file_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(youtube_link, download=False)
            title = result.get('title', 'youtube_playlist')
        except yt_dlp.utils.DownloadError as e:
            await m.reply_text(f"<pre><code>🚨 Error: {str(e)}</code></pre>")
            return

    # Ask for file name
    ask_msg = await m.reply_text(
        f"<pre><code>🔤 Send file name (without extension)</code></pre>\n"
        f"**✨ Send `1` for Default**\n"
        f"<pre><code>{title}</code></pre>\n"
    )
    input_name: Message = await client.listen(m.chat.id)
    raw_name = input_name.text.strip()
    await ask_msg.delete(True)
    await input_name.delete(True)

    custom_file_name = title if raw_name == '1' else raw_name

    # Extract links
    videos = []
    if 'entries' in result:
        for entry in result['entries']:
            video_title = entry.get('title', 'No title')
            url = entry.get('url', '')
            videos.append(f"{video_title}:{url}")
    else:
        video_title = result.get('title', 'No title')
        url = result.get('url', youtube_link)
        videos.append(f"{video_title}:{url}")

    # Save and send
    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)
    with open(txt_file, 'w') as f:
        f.write('\n'.join(videos))

    await m.reply_document(
        document=txt_file,
        caption=f'<a href="{youtube_link}">__**Click Here to open Playlist**__</a>\n'
                f'<pre><code>{custom_file_name}.txt</code></pre>\n'
    )
    os.remove(txt_file)


# ================================================================
#           MAIN TXT DOWNLOADER (/yadavji)
# ================================================================

@bot.on_message(filters.command(["yadavji"]))
async def batch_downloader(client: Client, m: Message):
    """Handle /yadavji command - batch download from TXT file."""
    editable = await m.reply_text(
        "<pre><code>🔹Hi I am Powerful TXT Downloader📥 Bot.\n"
        "🔹Send me the TXT file and wait.</code></pre>"
    )

    # Step 1: Get TXT file
    input_msg: Message = await client.listen(m.chat.id)

    # Check if user sent a document
    if not input_msg.document:
        await m.reply_text(
            "<pre><code>❌ Please send a .txt FILE, not a text message.\n"
            "Use /yadavji again and send the TXT file as document.</code></pre>"
        )
        return

    x = await input_msg.download()
    await input_msg.delete(True)
    file_name, _ = os.path.splitext(os.path.basename(x))

    try:
        # Try multiple encodings for compatibility
        content = None
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(x, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            await m.reply_text("<pre><code>❌ Cannot read file - unsupported encoding.</code></pre>")
            if os.path.exists(x):
                os.remove(x)
            return

        content = content.strip().split("\n")
        links = []
        for line in content:
            line = line.strip()
            if "://" in line:
                links.append(line.split("://", 1))
        os.remove(x)
    except Exception as e:
        await m.reply_text(f"<pre><code>Invalid file input.\nError: {str(e)}</code></pre>")
        if os.path.exists(x):
            os.remove(x)
        return

    if not links:
        await m.reply_text("<pre><code>No valid links found in file.</code></pre>")
        return

    # Step 2: Start index
    await editable.edit(f"<pre><code>Total 🔗 links found: {len(links)}\nSend From where to start (number)</code></pre>")
    input0: Message = await client.listen(m.chat.id)
    try:
        arg = int(input0.text.strip())
    except Exception:
        arg = 1
    await input0.delete(True)

    # Step 3: Batch name
    await editable.edit("<pre><code>Enter Your Batch Name\nSend 1 for default.</code></pre>")
    input1: Message = await client.listen(m.chat.id)
    b_name = file_name if input1.text.strip() == '1' else input1.text.strip()
    await input1.delete(True)

    # Step 4: Resolution
    await editable.edit(
        "╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣\n"
        "┣━━⪼ send `144`  for 144p\n"
        "┣━━⪼ send `240`  for 240p\n"
        "┣━━⪼ send `360`  for 360p\n"
        "┣━━⪼ send `480`  for 480p\n"
        "┣━━⪼ send `720`  for 720p\n"
        "┣━━⪼ send `1080` for 1080p\n\n"
        "╰━━⌈⚡[`🆈🅰🅳🅰🆅🅹➥🅹🅸`]⚡⌋━━➣"
    )
    input2: Message = await client.listen(m.chat.id)
    raw_text2 = input2.text.strip()
    quality = f"{raw_text2}p"
    res = get_resolution(raw_text2)
    await input2.delete(True)

    # Step 5: Credit name
    await editable.edit("<pre><code>Enter Your Name\nSend 1 for default</code></pre>")
    input3: Message = await client.listen(m.chat.id)
    raw_text3 = input3.text.strip()
    CR = '𝙔𝘼𝘿𝘼𝙑 𝙅𝙄 🕊️' if raw_text3 == '1' else (raw_text3 if raw_text3 else '𝙔𝘼𝘿𝘼𝙑 𝙅𝙄 🕊️')
    await input3.delete(True)

    # Step 6: PW Token
    await editable.edit(
        "<pre><code>Enter Your PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋</code></pre>\n"
        "┣⪼ Send `auto` to use saved token (from /token)\n"
        "┣⪼ Paste your token directly\n"
        "┣⪼ Or send anything to skip"
    )
    input4: Message = await client.listen(m.chat.id)
    raw_text4 = input4.text.strip()
    await input4.delete(True)
    
    # Handle auto token
    if raw_text4.lower() == 'auto':
        if os.path.exists("pw_token.txt"):
            with open("pw_token.txt", "r") as f:
                raw_text4 = f.read().strip()
            await m.reply_text("✅ Using saved PW token from `/token` command")
        else:
            await m.reply_text("⚠️ No saved token found. Use /token first to extract token.\nContinuing without token...")
            raw_text4 = "anything"

    # Step 7: Thumbnail
    await editable.edit(
        "01. 🌅Send ☞ Direct **Thumb Photo**\n\n"
        "02. 🔗Send ☞ `Thumb URL` for **Thumbnail**\n\n"
        "03. 🎞️Send ☞ `no` for **video** format\n\n"
        "04. 📁Send ☞ `No` for **Document** format"
    )
    input6: Message = await client.listen(m.chat.id)
    raw_text6 = input6.text if input6.text else "no"
    await input6.delete(True)
    await editable.delete()

    # Process thumbnail
    if input6.photo:
        thumb = await input6.download()
    elif raw_text6.startswith("http://") or raw_text6.startswith("https://"):
        getstatusoutput(f"wget '{raw_text6}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    await m.reply_text(f"🎯𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗘 - {b_name}")

    # ===== DOWNLOAD LOOP =====
    failed_count = 0
    count = arg

    for i in range(arg - 1, len(links)):
        try:
            Vxy = links[i][1].replace("file/d/", "uc?export=download&id=") \
                .replace("www.youtube-nocookie.com/embed", "youtu.be") \
                .replace("?modestbranding=1", "") \
                .replace("/view?usp=sharing", "")

            url = "https://" + Vxy
            link0 = url
            name1 = clean_name(links[i][0])
            name = name1[:60]

            # Process URL for special platforms
            url = await process_url(url, raw_text2, raw_text4)

            # Build download command
            cmd = build_cmd(url, name, raw_text2, raw_text4)

            # Build captions
            cc = (f'➥◆━╾━╾━ᐯɪᴅɪ𝗢 𝗜ᗪ ➫ [{str(count).zfill(3)}]({link0})◇━━╾━━\n\n'
                  f'📃𝐓ɪᴛʟ𝐄 ➠ {name1}\n\n'
                  f'🎬Ҩᴜᴀʟɪᴛㄚ ✎ **[{res}]**𝐘ᴀᴅᴀᴠ 𝐉𝐈.mp4\n\n'
                  f'❖ 𝗕𝗮𝘁𝗰𝗵✑ {b_name}\n\n'
                  f'✰╾────╼──╼───╼───╼──✰\n'
                  f'🧿 ☏ 𝔇ᴏᴡɴʟᴏᴀ𝔇 ᗷY ♤ {CR}\n'
                  f'✰╾────╼──╼───╼───╼──✰\n')

            cc1 = cc  # Same caption for documents

            # ===== HANDLE DIFFERENT FILE TYPES =====

            if "drive" in url:
                try:
                    ka = await helper.download(url, name)
                    await client.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                    count += 1
                    if os.path.exists(ka):
                        os.remove(ka)
                    await asyncio.sleep(1)
                except FloodWait as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(e.value)
                    count += 1
                    continue

            elif ".pdf*" in url:
                try:
                    url_part, key_part = url.split("*")
                    pdf_url = f"https://dragoapi.vercel.app/pdf/{url_part}*{key_part}"
                    download_cmd = f'yt-dlp -o "{name}.pdf" "{pdf_url}" -R 25 --fragment-retries 25'
                    os.system(download_cmd)
                    await client.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                    count += 1
                    if os.path.exists(f'{name}.pdf'):
                        os.remove(f'{name}.pdf')
                except FloodWait as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(e.value)
                    count += 1
                    continue

            elif ".pdf" in url:
                try:
                    await asyncio.sleep(2)
                    pdf_url = url.replace(" ", "%20")
                    scraper = cloudscraper.create_scraper()
                    response = scraper.get(pdf_url)
                    if response.status_code == 200:
                        with open(f'{name}.pdf', 'wb') as file:
                            file.write(response.content)
                        await asyncio.sleep(2)
                        await client.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    else:
                        await m.reply_text(f"Failed to download PDF: {response.status_code}")
                        count += 1
                except FloodWait as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(e.value)
                    count += 1
                    continue

            elif ".zip" in url:
                try:
                    download_cmd = f'yt-dlp -o "{name}.zip" "{url}" -R 25 --fragment-retries 25'
                    os.system(download_cmd)
                    await client.send_document(chat_id=m.chat.id, document=f'{name}.zip', caption=cc1)
                    count += 1
                    if os.path.exists(f'{name}.zip'):
                        os.remove(f'{name}.zip')
                except FloodWait as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(e.value)
                    count += 1
                    continue

            elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                try:
                    file_ext = url.split('.')[-1].split("?")[0]
                    download_cmd = f'yt-dlp -o "{name}.{file_ext}" "{url}" -R 25 --fragment-retries 25'
                    os.system(download_cmd)
                    await client.send_photo(chat_id=m.chat.id, photo=f'{name}.{file_ext}', caption=cc1)
                    count += 1
                    if os.path.exists(f'{name}.{file_ext}'):
                        os.remove(f'{name}.{file_ext}')
                except FloodWait as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(e.value)
                    count += 1
                    continue

            elif "cpvod.testbook.com" in url:
                try:
                    urlcpvod = "https://dragoapi.vercel.app/video/" + url
                    cccpvod = (f'🎞️𝐓𝐢𝐭𝐥𝐞 ➥ `{name1}` .mp4\n\n'
                               f'<a href="{urlcpvod}">__**Click Here to Watch Stream**__</a>\n'
                               f'📚 Course : {b_name}\n\n'
                               f'𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 `{CR}`\n')
                    await client.send_photo(chat_id=m.chat.id, photo=photologo, caption=cccpvod)
                    count += 1
                except Exception as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(1)
                    continue

            elif "youtu" in url:
                try:
                    ccyt = (f'🎞️𝐓𝐢𝐭𝐥𝐞 ➥ `{name1}` .mp4\n\n'
                            f'<a href="{url}">__**Click Here to Watch Stream**__</a>\n\n'
                            f'📚 Course : {b_name}\n\n'
                            f'𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 `{CR}`\n')
                    await client.send_photo(chat_id=m.chat.id, photo=photoyt, caption=ccyt)
                    count += 1
                except Exception as e:
                    await m.reply_text(str(e))
                    await asyncio.sleep(1)
                    continue

            else:
                # Download and upload video
                remaining = len(links) - count
                progress = (count / len(links)) * 100
                emoji_message = await show_random_emojis(m)

                Show = (f"🚀 𝗣𝗿𝗼𝗴𝗿𝗲𝗦𝗦 ✰ {progress:.2f}%\n┃\n"
                        f"┣🔗𝗜𝗡𝗗𝗘𝗫 ✰ {count}/{len(links)}\n┃\n"
                        f"╰━🖇️𝗥𝗘𝗠𝗔𝗜𝗡𝗜𝗡𝗚 ✵ {remaining}\n\n"
                        f"**⚡Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ...⏳**\n\n"
                        f"📚𝗧𝗶𝘁𝗹𝗲 » `{name}`\n┃\n"
                        f"┣🍁𝗤𝘂𝗮𝗹𝗶𝘁𝗒 » {raw_text2}p\n┃\n"
                        f'┣━🔗𝗟𝗶𝗻𝗞 » <a href="{link0}">__**Click Here**__</a>\n\n'
                        f"✦ 𝗕𝗢𝗧 𝗔𝗗𝗠𝗜𝗡 ✦ (@Yadav_ji_admin)")

                prog = await m.reply_text(Show, disable_web_page_preview=True)
                res_file = await helper.download_video(url, cmd, name)
                filename = res_file

                # Check if file was actually downloaded
                if not os.path.exists(filename):
                    await prog.delete(True)
                    await emoji_message.delete()
                    await m.reply_text(
                        f'⚠️ Download failed for: `{name}`\n'
                        f'🔗 <a href="{link0}">Check Link</a>\n\n'
                        f'File not found after download attempt.'
                    )
                    count += 1
                    failed_count += 1
                    continue

                await prog.delete(True)
                await emoji_message.delete()
                await helper.send_vid(client, m, cc, filename, thumb, name, prog)
                count += 1
                await asyncio.sleep(1)

        except Exception as e:
            await m.reply_text(
                f'◆━╾◇━━╾━━◆━ [{str(count).zfill(3)}]({link0}) ◆━╾◇━━╾━━◆━\n\n'
                f'📔𝐓𝐢𝐭𝐥𝐞 » `{name}`\n'
                f'🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">__**Check manually**__</a>\n\n'
                f'✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ `𝙔𝙖𝙙𝙖𝙫 𝙟𝙞🐦`'
            )
            count += 1
            failed_count += 1
            continue

    await m.reply_text(f"⌈🐼𝗧𝗼𝘁𝗮𝗟 𝗙𝗮𝗶𝗹𝗗 𝗟𝗶𝗻𝗸𝗦 『{failed_count}』💨⌋")
    await m.reply_text("🦅𝗔𝗹𝗹 𝗟𝗲𝗰𝘁𝘂𝗿𝗲𝗦 𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝗬 ⌈🧸『✰(@𝗬𝗮𝗱𝗮𝘃_𝗷𝗶_𝗮𝗱𝗺𝗶𝗻)』🏆⌋")


# ================================================================
#              CLASSPLUS STREAM LINKS (/cp)
# ================================================================

@bot.on_message(filters.command(["cp"]))
async def cp_handler(client: Client, m: Message):
    """Handle /cp command - process ClassPlus stream links."""
    editable = await m.reply_text(
        "<pre><code>🔹Hi I am Powerful CP Stream📥 Bot.\n"
        "🔹Send me the TXT file and wait.</code></pre>"
    )

    input_msg: Message = await client.listen(m.chat.id)

    if not input_msg.document:
        await m.reply_text(
            "<pre><code>❌ Please send a .txt FILE, not a text message.\n"
            "Use /cp again and send the TXT file as document.</code></pre>"
        )
        return

    x = await input_msg.download()
    await input_msg.delete(True)
    file_name, _ = os.path.splitext(os.path.basename(x))

    try:
        content = None
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(x, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        if content is None:
            await m.reply_text("<pre><code>❌ Cannot read file.</code></pre>")
            if os.path.exists(x):
                os.remove(x)
            return
        content = content.strip().split("\n")
        links = []
        for line in content:
            line = line.strip()
            if "://" in line:
                links.append(line.split("://", 1))
        os.remove(x)
    except Exception as e:
        await m.reply_text(f"<pre><code>Invalid file input.\nError: {str(e)}</code></pre>")
        if os.path.exists(x):
            os.remove(x)
        return

    await editable.delete(True)
    b_name = file_name
    await m.reply_text(f"<pre><code>🎯Target Batch : {b_name}</code></pre>")

    count = 1
    for i in range(len(links)):
        try:
            Vxy = links[i][1].replace("file/d/", "uc?export=download&id=") \
                .replace("www.youtube-nocookie.com/embed", "youtu.be") \
                .replace("?modestbranding=1", "") \
                .replace("/view?usp=sharing", "")

            url = "https://" + Vxy
            link0 = url
            urlcp = "https://dragoapi.vercel.app/video/" + url
            name1 = clean_name(links[i][0])
            name = name1[:60]

            cccp = (f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n'
                    f'📔𝐓𝐢𝐭𝐥𝐞 » `{name1}.mp4`\n\n'
                    f'<a href="{urlcp}">__**Click Here to Watch Stream**__</a>\n\n'
                    f'<pre><code>📚 Course : {b_name}</code></pre>\n')

            cc1 = (f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n'
                   f'📔𝐓𝐢𝐭𝐥𝐞 » `{name1}.pdf`\n\n'
                   f'<a href="{link0}">__**Click Here to Download**__</a>\n\n'
                   f'<pre><code>📚 Course : {b_name}</code></pre>\n')

            if ".pdf" in url or "drive" in url:
                await client.send_photo(chat_id=m.chat.id, photo=photocp, caption=cc1)
                count += 1
            elif "classplusapp.com" in url or "youtu" in url:
                await client.send_photo(chat_id=m.chat.id, photo=photocp, caption=cccp)
                count += 1
            else:
                await client.send_photo(chat_id=m.chat.id, photo=photocp, caption=cccp)
                count += 1

        except Exception as e:
            await m.reply_text(
                f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n'
                f'📔𝐓𝐢𝐭𝐥𝐞 » `{name}`\n'
                f'🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">__**Check manually**__</a>\n\n'
                f'✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ `𝙔𝘼𝘿𝘼𝙑 𝙅𝙄🐦`'
            )
            count += 1
            continue

    await m.reply_text("<pre><code>Converted By ⌈✨『𝙔𝘼𝘿𝘼𝙑 𝙅𝙄』✨⌋</code></pre>")


# ================================================================
#             DIRECT LINK HANDLER (text messages)
# ================================================================

@bot.on_message(filters.text & filters.private)
async def direct_link_handler(client: Client, m: Message):
    """Handle direct link messages - download and upload single video."""
    if m.from_user.is_bot:
        return
    # Ignore commands (even misspelled ones like /styart)
    if m.text.startswith("/"):
        return

    text = m.text
    match = re.search(r'https?://\S+', text)
    if not match:
        await m.reply_text("<pre><code>Invalid link format. Send a valid URL.</code></pre>")
        return

    link = match.group(0)

    editable = await m.reply_text(
        "<pre><code>**🔹Processing your link...\n🔁Please wait...⏳**</code></pre>"
    )

    # Step 1: Resolution
    await editable.edit(
        "<pre><code>╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣</code></pre>\n"
        "┣━━⪼ send `144`  for 144p\n"
        "┣━━⪼ send `240`  for 240p\n"
        "┣━━⪼ send `360`  for 360p\n"
        "┣━━⪼ send `480`  for 480p\n"
        "┣━━⪼ send `720`  for 720p\n"
        "┣━━⪼ send `1080` for 1080p\n"
        "<pre><code>╰━━⌈⚡[`𝙔𝘼𝘿𝘼𝙑 𝙅𝙄`]⚡⌋━━➣</code></pre>"
    )
    input2: Message = await client.listen(m.chat.id, filters=filters.text & filters.user(m.from_user.id))
    raw_text2 = input2.text.strip()
    res = get_resolution(raw_text2)
    await input2.delete(True)

    # Step 2: PW Token
    pw_token = "default"
    await editable.edit(
        "<pre><code>**Enter Your PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋**</code></pre>\n"
        "<pre><code>Send `0` for use default</code></pre>"
    )
    input4: Message = await client.listen(m.chat.id, filters=filters.text & filters.user(m.from_user.id))
    PW = pw_token if input4.text.strip() == '0' else input4.text.strip()
    await input4.delete(True)

    # Step 3: Thumbnail
    await editable.edit(
        "🌅Send ☞ `Thumb URL` for **Thumbnail**\n\n"
        "🎞️Send ☞ `no` for **video** format\n\n"
        "📁Send ☞ `No` for **Document** format"
    )
    input6: Message = await client.listen(m.chat.id, filters=filters.text & filters.user(m.from_user.id))
    raw_text6 = input6.text.strip()
    await input6.delete(True)
    await editable.delete()

    if raw_text6.startswith("http://") or raw_text6.startswith("https://"):
        getstatusoutput(f"wget '{raw_text6}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    # Process the URL
    url = link.replace("file/d/", "uc?export=download&id=") \
        .replace("www.youtube-nocookie.com/embed", "youtu.be") \
        .replace("?modestbranding=1", "") \
        .replace("/view?usp=sharing", "")

    url = await process_url(url, raw_text2, PW)

    # Clean name from the link text
    name1 = clean_name(text)
    name = name1[:20] if name1 else "download"

    # Build command
    cmd = build_cmd(url, name, raw_text2, PW)

    try:
        cc = (f'🎞️𝐓𝐢𝐭𝐥𝐞 » `{name}` [{res}].mp4\n'
              f'🔗𝐋𝐢𝐧𝐤 » <a href="{link}">__**CLICK HERE**__</a>\n\n'
              f'🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » `𝙔𝘼𝘿𝘼𝙑 𝙅𝙄`')

        cc1 = (f'📕𝐓𝐢𝐭𝐥𝐞 » `{name}`\n'
               f'🔗𝐋𝐢𝐧𝐤 » <a href="{link}">__**CLICK HERE**__</a>\n\n'
               f'🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » `𝙔𝘼𝘿𝘼𝙑 𝙅𝙄`')

        if "drive" in url:
            ka = await helper.download(url, name)
            await client.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
            if os.path.exists(ka):
                os.remove(ka)

        elif ".pdf" in url:
            await asyncio.sleep(2)
            pdf_url = url.replace(" ", "%20")
            scraper = cloudscraper.create_scraper()
            response = scraper.get(pdf_url)
            if response.status_code == 200:
                with open(f'{name}.pdf', 'wb') as file:
                    file.write(response.content)
                await client.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                os.remove(f'{name}.pdf')

        elif ".zip" in url:
            download_cmd = f'yt-dlp -o "{name}.zip" "{url}" -R 25 --fragment-retries 25'
            os.system(download_cmd)
            await client.send_document(chat_id=m.chat.id, document=f'{name}.zip', caption=cc1)
            if os.path.exists(f'{name}.zip'):
                os.remove(f'{name}.zip')

        elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
            file_ext = url.split('.')[-1].split("?")[0]
            download_cmd = f'yt-dlp -x --audio-format {file_ext} -o "{name}.{file_ext}" "{url}" -R 25 --fragment-retries 25'
            os.system(download_cmd)
            await client.send_document(chat_id=m.chat.id, document=f'{name}.{file_ext}', caption=cc1)
            if os.path.exists(f'{name}.{file_ext}'):
                os.remove(f'{name}.{file_ext}')

        elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
            file_ext = url.split('.')[-1].split("?")[0]
            download_cmd = f'yt-dlp -o "{name}.{file_ext}" "{url}" -R 25 --fragment-retries 25'
            os.system(download_cmd)
            await client.send_photo(chat_id=m.chat.id, photo=f'{name}.{file_ext}', caption=cc1)
            if os.path.exists(f'{name}.{file_ext}'):
                os.remove(f'{name}.{file_ext}')

        else:
            emoji_message = await show_random_emojis(m)
            Show = (f"<pre><code>**⚡Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ...⏳**</code></pre>\n"
                    f"🔗𝐋𝐢𝐧𝐤 » `{link}`\n"
                    f"<pre><code>✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ `𝙔𝘼𝘿𝘼𝙑 𝙅𝙄🐦`</code></pre>")
            prog = await m.reply_text(Show)
            res_file = await helper.download_video(url, cmd, name)
            filename = res_file

            if not os.path.exists(filename):
                await prog.delete(True)
                await emoji_message.delete()
                await m.reply_text(f"⚠️ Download failed. File not found.")
                return

            await prog.delete(True)
            await emoji_message.delete()
            await helper.send_vid(client, m, cc, filename, thumb, name, prog)

    except Exception as e:
        Error = (f"<pre><code>⚠️𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝</code></pre>\n"
                 f"📚𝐓𝐢𝐭𝐥𝐞 » `{name}`\n\n"
                 f"🔗𝐋𝐢𝐧𝐤 » `{link}`\n"
                 f"<pre><code>✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ `𝙔𝘼𝘿𝘼𝙑 𝙅𝙄🐦`</code></pre>")
        await m.reply_text(Error)


# ================================================================
#                    STARTUP
# ================================================================

if __name__ == "__main__":
    if WEBHOOK:
        asyncio.run(main())
    else:
        print("Bot starting locally...")
        bot.run()
