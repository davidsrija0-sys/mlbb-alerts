import os, re, json, urllib.request, urllib.parse

URLS = [
    "https://www.pockettactics.com/mobile-legends/redeem-codes",
    "https://www.pocketgamer.com/mobile-legends-bang-bang/redeem-codes/",
]
TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT_ID"]
SEEN = "seen.json"

def send(text):
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": text}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    html = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    out = {}
    for m in re.finditer(r"\b[A-Z0-9]{6,16}\b", text):
        c = m.group()
        if re.search(r"\d", c) and re.search(r"[A-Z]", c):
            ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 70): m.end() + 70]).strip()
            out.setdefault(c, ctx)
    return out

found = {}
for url in URLS:
    try:
        for c, ctx in fetch(url).items():
            found.setdefault(c, (url, ctx))
    except Exception as e:
        print("failed:", url, e)

if os.path.exists(SEEN):
    old = set(json.load(open(SEEN)))
    new = {c: v for c, v in found.items() if c not in old}
    if new:
        send("🎁 كود جديد في MLBB:\n\n" + "\n\n".join(
            f"{c}\n📝 {new[c][1]}\n{new[c][0]}" for c in sorted(new)))
else:
    old = set()
    send("✅ بدأت مراقبة أكواد MLBB")

json.dump(sorted(set(found) | old), open(SEEN, "w"))
