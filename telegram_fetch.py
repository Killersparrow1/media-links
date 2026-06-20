#!/usr/bin/env python3
import re, json, time, os, sys, configparser, urllib.request, urllib.error, pathlib
from datetime import datetime

try:
    from telethon import TelegramClient, events, sync
    from telethon.sessions import StringSession
except ImportError:
    print("Install Telethon: pip install telethon requests")
    sys.exit(1)

CONFIG_FILE = "config.ini"
SESSION_FILE = "telegram_session.session"
LAST_ID_FILE = "last_id.txt"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Missing {CONFIG_FILE}. Copy config.ini.template and fill it.")
        sys.exit(1)
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    return cfg

def load_last_ids():
    if not os.path.exists(LAST_ID_FILE):
        return {}
    with open(LAST_ID_FILE) as f:
        return json.load(f)

def save_last_ids(ids):
    with open(LAST_ID_FILE, "w") as f:
        json.dump(ids, f, indent=2)

def get_proxy(cfg):
    section = cfg.get("proxy", {})
    ptype = section.get("type", "").strip().lower() if "proxy" in cfg else ""
    if not ptype:
        return None
    host = section.get("host", "127.0.0.1").strip()
    port = int(section.get("port", "9050").strip())
    print(f"  Using proxy: {ptype}://{host}:{port}")
    if ptype == "socks5":
        return ("socks5", host, port)
    elif ptype == "http":
        return ("http", host, port)
    elif ptype == "mtproxy":
        secret = section.get("secret", "").strip()
        return ("mtproxy", host, port, secret)
    return None

def parse_filename(name):
    res_m = re.search(r'\b(2160p|1080p|720p|576p|480p)\b', name, re.I)
    codec_m = re.search(r'\b(H\.?265|H\.?264|AV1|x265|x264|HEVC|AVC)\b', name, re.I)
    audio_m = re.search(r'\b(AAC|DDP\d*\.?\d*|AC3|EAC3|FLAC|DTS|TrueHD)\b', name, re.I)
    year_m = re.search(r'\b(19\d{2}|20\d{2})\b', name)
    hdr_m = re.search(r'\b(DV|HDR10\+?|HDR|DolbyVision|HLG)\b', name, re.I)
    atmos_m = re.search(r'\bAtmos\b', name, re.I)
    source_m = re.search(r'\b(NF|AMZN|HULU|DSNP|iT|FAND|MA|WEB-DL|WEBRip|BLURAY|BRRIP|DVDRip|HDTV|WEB)\b', name, re.I)
    group_m = re.search(r'-([\w.]+)\.(mkv|mp4|avi|mov)$', name)
    season_ep_m = re.search(r'\bS(\d+)\s*E(\d+)\b', name, re.I) or re.search(r'\bS(\d+)\.E(\d+)\b', name, re.I)
    season_m = re.search(r'\bS(\d+)\b(?!\s*E)', name, re.I) or re.search(r'\bSeason\s*(\d+)\b', name, re.I)
    ep_m = re.search(r'\bE(\d+)\b(?!\s*\d)', name, re.I) or re.search(r'\bEpisode\s*(\d+)\b', name, re.I)

    size = ""
    size_m = re.search(r'\[([\d.]+)\s*(GB|MB)\]', name, re.I)
    if size_m:
        size = f"{size_m.group(1)} {size_m.group(2)}"

    season, episode, link_type = "", "", "Movie"
    if season_ep_m:
        season, episode = season_ep_m.group(1), season_ep_m.group(2)
        link_type = "TV"
    elif season_m:
        season = season_m.group(1)
        link_type = "TV"
        if ep_m:
            episode = ep_m.group(1)
    elif ep_m and ep_m.start() < 15 and not season:
        episode = ep_m.group(1)
        link_type = "TV"

    title = name
    title = re.sub(r'\[[\d.]+\s*(GB|MB)\]\s*', '', title)
    title = re.sub(r'\b(2160p|1080p|720p|576p|480p|4K)\b', '', title, flags=re.I)
    title = re.sub(r'\b(H\.?265|H\.?264|AV1|x265|x264|HEVC|AVC)\b', '', title, flags=re.I)
    title = re.sub(r'\b(AAC|DDPA?\d*\.?\d*|AC3|EAC3|FLAC|DTS|TrueHD)\b', '', title, flags=re.I)
    title = re.sub(r'\b(NF\s*WEB\s*DL|AMZN|HULU|DSNP|iT|FAND|MA|WEB-DL|WEBRip|BLURAY|BRRIP|DVDRip|HDTV)\b', '', title, flags=re.I)
    title = re.sub(r'\b(DV|HDR10\+?|HDR|DolbyVision|HLG)\b', '', title, flags=re.I)
    title = re.sub(r'\bAtmos\b', '', title, flags=re.I)
    title = re.sub(r'\bMULTI\b', '', title, flags=re.I)
    title = re.sub(r'\bDUAL\b', '', title, flags=re.I)
    title = re.sub(r'\bAUDIO\b', '', title, flags=re.I)
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\b(19\d{2}|20\d{2})\b', '', title)
    title = re.sub(r'\bS(\d+)\s*E(\d+)\b', '', title, flags=re.I)
    title = re.sub(r'\bS(\d+)\b(?!\s*E)', '', title, flags=re.I)
    title = re.sub(r'\bSeason\s*(\d+)\b', '', title, flags=re.I)
    title = re.sub(r'\bE(\d+)\b', '', title, flags=re.I)
    title = re.sub(r'\bEpisode\s*(\d+)\b', '', title, flags=re.I)
    title = re.sub(r'\b(10bit|8bit|REPACK|PROPER|iNTERNAL)\b', '', title, flags=re.I)
    title = re.sub(r'\b(RIP|BY)\b', '', title, flags=re.I)
    title = re.sub(r'#\w+', '', title)
    title = re.sub(r'-[\w.]+\s*\.\s*(mkv|mp4|avi|mov)\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*-\s*[\w.]+\s*$', '', title)
    title = re.sub(r'\.', ' ', title)
    title = re.sub(r'[_-]+', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'\s+([,;:])', r'\1', title)
    title = re.sub(r'^\d{1,2}\s+', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'\s+', ' ', title).strip()

    hdr = hdr_m.group(1).upper().replace("DOLBYVISION", "DV") if hdr_m else ""
    atmos = "Atmos" if atmos_m else ""
    audio = audio_m.group(1).upper() if audio_m else ""
    group = group_m.group(1).replace(".", " ").strip() if group_m else ""
    codec = ""
    if codec_m:
        codec = codec_m.group(1).upper().replace("X265", "H.265").replace("X264", "H.264").replace("HEVC", "H.265").replace("AVC", "H.264")
    resolution = res_m.group(1).lower() if res_m else "1080p"
    source = source_m.group(1).upper() if source_m else ""

    group_key = f"{title} {year_m.group(1) if year_m else ''}".strip().lower()
    group_key = re.sub(r'\s+', ' ', group_key)

    return {
        "title": title or "Unknown",
        "year": year_m.group(1) if year_m else "",
        "resolution": resolution,
        "size": size,
        "codec": codec,
        "audio": audio,
        "hdr": hdr,
        "atmos": atmos,
        "source": source,
        "group": group,
        "type": link_type,
        "season": season,
        "episode": episode,
        "_groupKey": group_key
    }

def parse_bulk(text):
    lines = [l.strip() for l in text.split("\n") if l.strip() and not re.search(r'^AUDIO\s+TRACKS', l, re.I) and not re.search(r'^for\s+refer', l, re.I)]
    parsed = []
    context = None
    i = 0
    while i < len(lines):
        line = lines[i]
        url_m = re.search(r'https?://[^\s\[\]]+', line)
        if url_m:
            url = url_m.group(0)
            before = line[:url_m.start()].strip()
            if context:
                entry = {**context, "size": "", "url": url, "_groupKey": ""}
                gk = f"{entry.get('title','')} {entry.get('year','')}".strip().lower()
                entry["_groupKey"] = re.sub(r'\s+', ' ', gk)
                parsed.append(entry)
                context = None
            else:
                info = parse_filename(before or "Unknown")
                info["url"] = url
                parsed.append(info)
            i += 1
        elif i + 1 < len(lines) and re.match(r'^https?://', lines[i + 1]):
            next_url = lines[i + 1]
            info = parse_filename(line)
            info["url"] = next_url
            parsed.append(info)
            i += 2
        elif re.search(r'\bS(\d+)\b', line, re.I) and i + 1 < len(lines) and re.match(r'^https?://', lines[i + 1]):
            season = re.search(r'\bS(\d+)\b', line, re.I).group(1)
            size_m = re.search(r'\[([\d.]+)\s*(GB|MB)\]', line, re.I)
            size = f"{size_m.group(1)} {size_m.group(2)}" if size_m else ""
            ctx = context or {"title": "Unknown", "year": "", "resolution": "1080p", "codec": "", "audio": "", "source": "", "hdr": "", "atmos": "", "group": ""}
            entry = {**ctx, "type": "TV", "season": season, "episode": "", "size": size, "url": lines[i + 1]}
            gk = f"{entry.get('title','')} {entry.get('year','')}".strip().lower()
            entry["_groupKey"] = re.sub(r'\s+', ' ', gk)
            parsed.append(entry)
            i += 2
        elif not line.lower().endswith(('.mkv', '.mp4', '.avi', '.mov')) and (re.search(r'(2160p|1080p|720p|#\w+|S\d+|CODEC|AV1)', line, re.I) or re.search(r'#\w+', line)):
            info = parse_filename(line)
            context = {"title": info["title"], "year": info["year"], "resolution": info["resolution"],
                       "codec": info["codec"], "audio": info["audio"], "source": info["source"],
                       "hdr": info["hdr"], "atmos": info["atmos"], "group": info["group"], "type": "TV"}
            i += 1
        else:
            i += 1
    return parsed

def get_sheet_data(api_url):
    try:
        r = urllib.request.urlopen(f"{api_url}?action=getAll", timeout=30)
        data = json.loads(r.read().decode())
        if isinstance(data, dict) and data.get("success") and data.get("data"):
            return data["data"]
        return []
    except Exception as e:
        print(f"  ⚠ Sheet fetch failed: {e}")
        return None

def dedup_key(entry):
    return f"{entry.get('title','').lower().strip()}|{entry.get('year','')}|{entry.get('size','')}"

def push_to_sheet(api_url, entry):
    entry["id"] = str(int(time.time() * 1000)) + os.urandom(2).hex()
    entry["dateAdded"] = datetime.utcnow().isoformat() + "Z"
    entry["watched"] = "No"
    entry["notes"] = ""
    data = json.dumps(entry).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(api_url, data=data, headers={"Content-Type": "text/plain"}), timeout=30)
        resp = json.loads(r.read().decode())
        return resp.get("success") is not False
    except Exception as e:
        print(f"    ⚠ Push failed: {e}")
        return False

def extract_messages(messages):
    buffer = []
    for msg in messages:
        t = msg.text or ""
        if not t.strip():
            continue
        t = re.sub(r'https?://\S+\s*', lambda m: m.group(0) + "\n", t)
        t = re.sub(r'\n{3,}', '\n\n', t)
        buffer.append(t.strip())
    return parse_bulk("\n".join(buffer))

async def main():
    cfg = load_config()
    section = cfg["telegram"]
    api_id = int(section.get("api_id", "0"))
    api_hash = section.get("api_hash", "").strip()
    phone = section.get("phone", "").strip()
    api_url = cfg["sheet"]["api_url"].strip()

    channels = []
    if "channels" in cfg:
        for k, v in cfg["channels"].items():
            if v.strip():
                channels.append(v.strip())

    if not api_id or not api_hash:
        print("Set api_id and api_hash in config.ini (from my.telegram.org)")
        return
    if not channels:
        print("Add at least one channel under [channels]")
        return

    proxy = get_proxy(cfg)

    print("Connecting to Telegram...")
    client = TelegramClient(SESSION_FILE, api_id, api_hash, proxy=proxy) if proxy else TelegramClient(SESSION_FILE, api_id, api_hash)

    await client.start(phone=phone if phone else None)
    print(f"  Logged in as: {(await client.get_me()).username or (await client.get_me()).first_name}")

    last_ids = load_last_ids()
    all_parsed = []
    is_first_run = not last_ids

    for ch in channels:
        try:
            entity = await client.get_input_entity(ch)
            display = ch if len(ch) < 30 else ch[:27] + "..."
        except Exception:
            print(f"  ⚠ Cannot access: {ch}")
            continue

        try:
            offset_id = last_ids.get(ch, 0)
            if offset_id:
                print(f"  📡 {display}: fetching new messages (since id {offset_id})...")
            else:
                print(f"  📡 {display}: fetching all history...")

            msgs = []
            async for msg in client.iter_messages(entity, offset_id=offset_id, reverse=False):
                if msg.text and msg.text.strip():
                    msgs.append(msg)
                if msg.id > offset_id:
                    offset_id = msg.id

            if msgs:
                last_ids[ch] = offset_id
                parsed = extract_messages(msgs)
                all_parsed.extend(parsed)
                print(f"    → {len(msgs)} messages, {len(parsed)} links parsed")
            else:
                print(f"    → No new messages")

        except Exception as e:
            print(f"  ⚠ Error fetching {display}: {e}")

    if not all_parsed:
        print("\n✅ No new links found.")
        return

    print(f"\n🔄 Checking {len(all_parsed)} parsed links against sheet...")
    sheet_data = get_sheet_data(api_url)
    existing_keys = set()
    if sheet_data is not None:
        for item in sheet_data:
            key = dedup_key(item)
            if key:
                existing_keys.add(key)
        print(f"  Sheet has {len(sheet_data)} entries")

    new_links = []
    dupes = 0
    for entry in all_parsed:
        key = dedup_key(entry)
        if key in existing_keys:
            dupes += 1
        else:
            new_links.append(entry)
            existing_keys.add(key)

    print(f"  {len(new_links)} new, {dupes} duplicates skipped")

    if not new_links:
        print("\n✅ All links already in sheet.")
        save_last_ids(last_ids)
        return

    print(f"\n📤 Pushing {len(new_links)} links to sheet...")
    pushed = 0
    for i, entry in enumerate(new_links, 1):
        ok = push_to_sheet(api_url, entry)
        if ok:
            pushed += 1
        if i % 5 == 0 or i == len(new_links):
            print(f"  {i}/{len(new_links)} ({pushed} OK)")
        time.sleep(0.3)

    save_last_ids(last_ids)
    print(f"\n✅ Done — {pushed} links pushed, {len(new_links) - pushed} failed, {dupes} duplicates skipped")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
