import os
import time
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import subprocess
import concurrent.futures

from utils import progress_bar
from pyrogram import Client
from pyrogram.types import Message

# Global counter for visionias retries
failed_counter = 0


def duration(filename):
    """Get video duration using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout)
    except Exception:
        return 0


def exec(cmd):
    """Execute a shell command and return output."""
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.stdout.decode()
    return output


def pull_run(work, cmds):
    """Run multiple commands in parallel using ThreadPoolExecutor."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        fut = executor.map(exec, cmds)


async def aio(url, name):
    """Download a file asynchronously."""
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k


async def download(url, name):
    """Download a file (PDF) asynchronously."""
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka


def human_readable_size(size, decimal_places=2):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    """Generate a filename based on current date/time."""
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


async def download_video(url, cmd, name):
    """Download video using yt-dlp with aria2c external downloader."""
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    global failed_counter
    print(f"[DOWNLOAD] {download_cmd}")
    logging.info(download_cmd)
    k = subprocess.run(download_cmd, shell=True)

    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        return await download_video(url, cmd, name)

    failed_counter = 0

    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"

        name_base = name.split(".")[0]
        if os.path.isfile(f"{name_base}.mkv"):
            return f"{name_base}.mkv"
        elif os.path.isfile(f"{name_base}.mp4"):
            return f"{name_base}.mp4"
        elif os.path.isfile(f"{name_base}.mp4.webm"):
            return f"{name_base}.mp4.webm"

        return name
    except Exception:
        return name


async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name):
    """Send a document to the user."""
    reply = await m.reply_text(f"<pre><code>Uploading » `{name}`</code></pre>")
    await asyncio.sleep(1)
    start_time = time.time()
    await m.reply_document(ka, caption=cc1)
    count += 1
    await reply.delete(True)
    await asyncio.sleep(1)
    if os.path.exists(ka):
        os.remove(ka)
    await asyncio.sleep(3)


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    """Send a video to the user with thumbnail and progress bar."""
    thumb_path = f"{filename}.jpg"

    # Generate thumbnail from video at 5 seconds (not 1 min - short videos won't have 1 min)
    subprocess.run(
        f'ffmpeg -y -i "{filename}" -ss 00:00:05 -vframes 1 "{thumb_path}"',
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        await prog.delete(True)
    except Exception:
        pass

    reply = await m.reply_text(
        f"**★彡 ᵘᵖˡᵒᵃᵈⁱⁿᵍ 彡★ ...⏳**\n\n"
        f"📚𝐓𝐢𝐭𝐥𝐞 » `{name}`\n\n"
        f"✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ ➥𝙔𝘼𝘿𝘼𝙑 𝙅𝙄🦁"
    )

    # Determine thumbnail
    if thumb and thumb != "no" and os.path.exists(thumb):
        thumbnail = thumb
    elif os.path.exists(thumb_path):
        thumbnail = thumb_path
    else:
        thumbnail = None  # No thumbnail - send without it

    dur = int(duration(filename))
    start_time = time.time()

    try:
        await m.reply_video(
            filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
    except Exception as e:
        print(f"[VIDEO UPLOAD FAILED] {e}")
        print(f"[FALLING BACK TO DOCUMENT] {filename}")
        try:
            await m.reply_document(
                filename,
                caption=cc,
                thumb=thumbnail,
                progress=progress_bar,
                progress_args=(reply, start_time)
            )
        except Exception as e2:
            print(f"[DOCUMENT UPLOAD ALSO FAILED] {e2}")
            await m.reply_text(f"❌ Upload failed: {str(e)}")

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    try:
        await reply.delete(True)
    except Exception:
        pass
