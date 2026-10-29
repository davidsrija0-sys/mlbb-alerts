import os, re, json, urllib.request, urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
SOURCES = [
    "https://www.pocketgamer.com/mobile-legends-bang-bang/redeem-codes/",
    "https://www.pockettactics.com/mobile-legends/redeem-codes",
    "https://www.pcgamesn.com/mlbb/codes",
    "https://www.dexerto.com/gaming/mobile-legends-bang-bang-codes-ml-diamonds-magic-dust-1740586/",
    "https://theclutch.com.br/codigos/mobile-legends/",
]
TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT_ID"]
SEEN = "seen.json"
CODE_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]{6,20}(?![A-Za-z0-9])")
EXPIRED_RE = re.compile(
    r"(?im)^[^\n]{0,60}(full list of expired|expired codes|expired code|past codes|"
    r"kode kadaluarsa|c[oó]digos expirados)[^\n]{0,40}$"
)
STOP = {"148APPS", "ANDROID", "IPHONE", "WINDOWS", "CHROME", "FIREFOX", "SAFARI", "UTF8", "HTML5"}

def ok(code):
    letters = sum(c.isalpha() for c in code)
    digits = sum(c.isdigit() for c in code)
    return letters >= 2 and digits >= 1 and code.upper() not in STOP and len(set(code.lower())) > 2

def send(text):
    data = urllib.parse.urlencode({
        "chat_id": CHAT,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    with urllib.request.urlopen(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", data, timeout=30
    ) as r:
        r.read()

def page_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,id;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        html = r.read().decode("utf-8", "ignore")
    html = re.sub(r"(?s)<(script|style|noscript).*?</\1>", " ", html)
    html = re.sub(r"(?i)</(p|li|h[1-6]|tr|div|td)>", "\n", html)
    html = re.sub(r"(?i)<(br|p|li|h[1-6]|tr|div|td)[^>]*>", "\n", html)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace(chr(38) + "nbsp;", " ").replace(chr(38) + "amp;", chr(38)).replace("\xa0", " ")
    html = re.sub(r"[ \t]+", " ", html)
    return re.sub(r" *\n+", "\n", html)

def split_expired(text):
    for m in reversed(list(EXPIRED_RE.finditer(text))):
        if any(ok(c) for c in CODE_RE.findall(text[m.start():])):
            return text[:m.start()], text[m.start():]
    return text, ""

def extract(text):
    out = {}
    for m in CODE_RE.finditer(text):
        c = m.group()
        key = c.upper()
        if not ok(c) or key in out:
            continue
        nxt = CODE_RE.search(text, m.end())
        end = m.end() + 90
        if nxt and nxt.start() < end:
            end = nxt.start()
        ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 20):end]).strip()[:160]
        out[key] = (c, ctx)
    return out

def notify(alert):
    blocks = []
    for key in sorted(alert):
        code, ctx, urls = alert[key]
        blocks.append(f"{code}\n📝 {ctx}\n" + "\n".join(urls))
    buf = "🎁 كود جديد في MLBB:\n\n"
    for block in blocks:
        extra = block + "\n\n"
        if len(buf) > 40 and len(buf) + len(extra) > 3500:
            send(buf.rstrip())
            buf = "🎁 كود جديد في MLBB:\n\n"
        buf += extra
    send(buf.rstrip())

active, expired = {}, {}
for url in SOURCES:
    try:
        live, old_part = split_expired(page_text(url))
    except Exception as e:
        print("failed:", url, e)
        continue
    for key, (code, ctx) in extract(live).items():
        rec = active.setdefault(key, [code, ctx, []])
        if url not in rec[2]:
            rec[2].append(url)
    for key, (code, _) in extract(old_part).items():
        expired.setdefault(key, code)

if os.path.exists(SEEN):
    with open(SEEN, encoding="utf-8") as f:
        old = {c.upper(): c for c in json.load(f)}
    fresh = False
else:
    old, fresh = {}, True

new = {k: v for k, v in active.items() if k not in old}
if fresh:
    send("✅ بدأت مراقبة أكواد MLBB")
elif new:
    notify(new)
    for key, (code, _, _) in new.items():
        old[key] = code

for key, code in expired.items():
    old.setdefault(key, code)
for key, (code, _, _) in active.items():
    old.setdefault(key, code)

with open(SEEN, "w", encoding="utf-8") as f:
    json.dump(sorted(old.values(), key=str.upper), f, ensure_ascii=False)
    f.write("\n")