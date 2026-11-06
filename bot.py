import os
import time
import sqlite3

import discord
from discord.ext import tasks

# Лог илгээх суваг (өөрийн сервер дэх суваг)
LOG_CHANNEL_ID = 1568181663702327417

# Аль серверүүдийг хянахыг хязгаарлах бол Railway Variables-д ALLOWED_GUILDS=id1,id2 гэж өг.
# Хоосон бол bot орсон БҮХ серверийг хянана.
ALLOWED_GUILDS = {
    int(x) for x in os.getenv("ALLOWED_GUILDS", "").replace(" ", "").split(",") if x
}

DATA_DIR = os.getenv("DATA_DIR", "data")
KEEP_DAYS = 7
MAX_SIZE = 9 * 1024 * 1024  # 9MB-аас том файлыг алгасна

os.makedirs(f"{DATA_DIR}/files", exist_ok=True)
db = sqlite3.connect(f"{DATA_DIR}/log.db")
db.execute(
    """CREATE TABLE IF NOT EXISTS att2(
    msg_id INTEGER, author_id INTEGER, author TEXT, avatar TEXT,
    guild_id INTEGER, guild_name TEXT, channel_id INTEGER,
    filename TEXT, path TEXT, ts REAL)"""
)
db.commit()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    if not cleanup.is_running():
        cleanup.start()
    print(f"Logged in as {client.user}; servers: {[g.name for g in client.guilds]}")


@client.event
async def on_message(msg: discord.Message):
    if msg.guild is None or msg.author.bot or not msg.attachments:
        return
    if ALLOWED_GUILDS and msg.guild.id not in ALLOWED_GUILDS:
        return
    if msg.channel.id == LOG_CHANNEL_ID:
        return
    for i, a in enumerate(msg.attachments):
        if a.size > MAX_SIZE:
            continue
        name = os.path.basename(a.filename)
        path = f"{DATA_DIR}/files/{msg.id}_{i}_{name}"
        try:
            with open(path, "wb") as f:
                f.write(await a.read())
        except Exception as e:
            print("download failed:", e)
            continue
        db.execute(
            "INSERT INTO att2 VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                msg.id,
                msg.author.id,
                str(msg.author),
                msg.author.display_avatar.url,
                msg.guild.id,
                msg.guild.name,
                msg.channel.id,
                name,
                path,
                time.time(),
            ),
        )
    db.commit()


@client.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    rows = db.execute(
        "SELECT author_id, author, avatar, guild_name, channel_id, filename, path "
        "FROM att2 WHERE msg_id=?",
        (payload.message_id,),
    ).fetchall()
    if not rows:
        return
    author_id, author, avatar, guild_name, channel_id, _, _ = rows[0]

    embed = discord.Embed(title="Attachment Deleted", color=0xE67E22)
    embed.set_author(name=author, icon_url=avatar)
    embed.add_field(name="Message author", value=f"<@{author_id}> ({author})", inline=False)
    embed.add_field(name="Server", value=guild_name, inline=False)
    embed.add_field(name="Channel", value=f"<#{channel_id}>", inline=False)
    embed.set_footer(text=f"ID: {payload.message_id}")

    files = []
    for *_, filename, path in rows:
        if os.path.exists(path):
            files.append(discord.File(path, filename=filename))

    log = client.get_channel(LOG_CHANNEL_ID)
    if log and files:
        await log.send(embed=embed, files=files[:10])

    for *_, path in rows:
        if os.path.exists(path):
            os.remove(path)
    db.execute("DELETE FROM att2 WHERE msg_id=?", (payload.message_id,))
    db.commit()


@tasks.loop(hours=1)
async def cleanup():
    cutoff = time.time() - KEEP_DAYS * 86400
    for (path,) in db.execute("SELECT path FROM att2 WHERE ts<?", (cutoff,)).fetchall():
        if os.path.exists(path):
            os.remove(path)
    db.execute("DELETE FROM att2 WHERE ts<?", (cutoff,))
    db.commit()


token = os.getenv("DISCORD_TOKEN")
if not token:
    raise SystemExit("DISCORD_TOKEN тохируулаагүй байна")
client.run(token)
