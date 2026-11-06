# Discord Attachment Log Bot

Серверт илгээгдсэн зургийг хадгалж, мессеж устгагдахад лог суваг руу буцааж илгээдэг bot.
Хадгалсан файлыг 7 хоногийн дараа автоматаар устгана.

## Тохиргоо
- `bot.py` дахь `GUILD_ID`, `LOG_CHANNEL_ID`-г өөрийнхөөрөө солих.
- Developer Portal -> Bot -> **Message Content Intent**-ийг асаах.
- Лог сувгийг private байлгах.

## Локал дээр ажиллуулах
```bash
pip install -r requirements.txt
export DISCORD_TOKEN=your_token   # Windows: set DISCORD_TOKEN=your_token
python bot.py
```

## Fly.io deploy
```bash
fly launch --no-deploy --copy-config
fly volumes create data --size 1
fly secrets set DISCORD_TOKEN=your_token
fly deploy
```

**Token-оо хэзээ ч GitHub руу оруулж болохгүй.**
