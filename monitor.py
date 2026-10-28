import os, re, json, urllib.request, urllib.parse

URL = "https://www.pockettactics.com/mobile-legends/redeem-codes"
TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT_ID"]
SEEN = "seen.json"

def send(text):
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": text}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data)

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
html = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
text = re.sub(r"<[^>]+>", " ", html)

found = {c for c in re.findall(r"\b[A-Z0-9]{6,16}\b", text)
         if re.search(r"\d", c) and re.search(r"[A-Z]", c)}

if os.path.exists(SEEN):
    old = set(json.load(open(SEEN)))
    new = found - old
    if new:
        send("🎁 كود جديد في MLBB:\n" + "\n".join(sorted(new)) + "\n" + URL)
else:
    old = set()
    send("✅ بدأت مراقبة أكواد MLBB")

json.dump(sorted(found | old), open(SEEN, "w"))
