"""
╔══════════════════════════════════════════════════════════════════════╗
║   ⚡ ULTIMATE TELEGRAM REPORTER v15.0 — CYBER JUSTICE NUCLEAR ⚡     ║
║──────────────────────────────────────────────────────────────────────║
║   ✅ ULTRA-FAST /report (parallel firing, no slow waits)             ║
║   ✅ Private channels reported properly (smart entity resolve)       ║
║   ✅ Random device fingerprinting per client (iOS/Android combos)    ║
║   ✅ Multi-message flow: "send link → aur bhejo ya skip"             ║
║   ✅ Round-robin: acc1→all msgs, acc2→all msgs, acc3→all msgs        ║
║   ✅ /groupreport — group 3-dot menu style report (with msg select)  ║
║   ✅ Powerful multi-paragraph contextual report messages             ║
║   ✅ /addaccount → Phone+OTP OR Pyrogram/Telethon session string     ║
║   ✅ /logs sends actual log FILE, /restart preserves sessions        ║
║   ✅ Auto-reconnect on every report, 6 PFP methods, full TG tree     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import json
import random
import smtplib
import socket
import sys
import time
import os
import re
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

try:
    import socks  # pip install PySocks
except ImportError:
    socks = None

from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl import types as tl_types

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes,
)

# ══════════════════════════════════════════════════════════════════════
# 🔐 CORE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
BOT_TOKEN = "8561124015:AAGpEGpWyOjvsIwCPtGC2bHAuRZvhWpPRqE"
API_ID    = 33628258
API_HASH  = "0850762925b9c1715b9b122f7b753128"
OWNER_ID  = 6980326908

MAX_REPORTS_PER_ACCOUNT = 100
BOT_VERSION             = "15.0"

PROXY_ENABLED = False

# ══════════════════════════════════════════════════════════════════════
# 📱 RANDOM DEVICE FINGERPRINTING POOL (Realistic iOS/Android combos)
# ══════════════════════════════════════════════════════════════════════
DEVICE_FINGERPRINTS = [
    # iOS devices
    {"device_model": "iPhone 15 Pro Max",  "system_version": "iOS 17.5.1", "app_version": "10.13.3", "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "iPhone 15 Pro",      "system_version": "iOS 17.4.1", "app_version": "10.12.0", "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "iPhone 14 Pro Max",  "system_version": "iOS 17.3.1", "app_version": "10.11.2", "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "iPhone 14 Pro",      "system_version": "iOS 16.7.2", "app_version": "10.10.0", "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "iPhone 14",          "system_version": "iOS 16.6.1", "app_version": "10.9.1",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "iPhone 13 Pro",      "system_version": "iOS 16.5.0", "app_version": "10.8.2",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "iPhone 13",          "system_version": "iOS 16.4.1", "app_version": "10.7.1",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "iPhone 12 Pro",      "system_version": "iOS 16.3.0", "app_version": "10.6.0",  "lang_code": "en", "system_lang_code": "en-GB"},
    {"device_model": "iPhone 12",          "system_version": "iOS 15.7.8", "app_version": "10.5.3",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "iPhone SE (3rd gen)","system_version": "iOS 16.2.0", "app_version": "10.4.0",  "lang_code": "en", "system_lang_code": "en-IN"},
    # Android devices
    {"device_model": "Samsung SM-S928B",   "system_version": "Android 14", "app_version": "10.13.3",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "Samsung SM-S918B",   "system_version": "Android 14", "app_version": "10.12.0",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "Samsung SM-G998B",   "system_version": "Android 13", "app_version": "10.11.2",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "Samsung SM-A546B",   "system_version": "Android 13", "app_version": "10.10.0",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "Google Pixel 8 Pro", "system_version": "Android 14", "app_version": "10.13.3",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "Google Pixel 8",     "system_version": "Android 14", "app_version": "10.12.0",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "Google Pixel 7 Pro", "system_version": "Android 13", "app_version": "10.11.0",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "OnePlus 12",         "system_version": "Android 14", "app_version": "10.13.0",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "OnePlus 11",         "system_version": "Android 13", "app_version": "10.10.1",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "Xiaomi 14 Pro",      "system_version": "Android 14", "app_version": "10.12.2",  "lang_code": "en", "system_lang_code": "en-US"},
    {"device_model": "Xiaomi 13",          "system_version": "Android 13", "app_version": "10.11.1",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "Realme GT 5 Pro",    "system_version": "Android 14", "app_version": "10.12.0",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "Vivo X100 Pro",      "system_version": "Android 14", "app_version": "10.11.0",  "lang_code": "en", "system_lang_code": "en-IN"},
    {"device_model": "OPPO Find X7 Ultra", "system_version": "Android 14", "app_version": "10.12.1",  "lang_code": "en", "system_lang_code": "en-IN"},
]

def random_device() -> dict:
    """Pick a fresh random device fingerprint each call."""
    return random.choice(DEVICE_FINGERPRINTS).copy()

# ══════════════════════════════════════════════════════════════════════
# 🌐 PROXY POOL
# ══════════════════════════════════════════════════════════════════════
PROXY_LIST: List[dict] = []
FREE_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
]

def quick_proxy_test(addr: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((addr, port), timeout=timeout):
            return True
    except Exception:
        return False

def load_free_proxies(max_proxies: int = 15, test: bool = True):
    global PROXY_LIST
    PROXY_LIST = []
    seen = set()
    candidates = []
    for url in FREE_PROXY_SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                text = r.read().decode("utf-8", errors="ignore")
            for line in text.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                try:
                    addr, port = line.split(":", 1)
                    port = int(port.strip())
                    key = f"{addr}:{port}"
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append((addr.strip(), port))
                except Exception:
                    continue
        except Exception:
            continue

    random.shuffle(candidates)
    for addr, port in candidates:
        if len(PROXY_LIST) >= max_proxies:
            break
        if test and not quick_proxy_test(addr, port, timeout=2.5):
            continue
        PROXY_LIST.append({
            "type": "socks5",
            "addr": addr,
            "port": port,
            "username": None,
            "password": None,
        })

# ══════════════════════════════════════════════════════════════════════
# 📧 GMAIL ACCOUNTS POOL
# ══════════════════════════════════════════════════════════════════════
GMAIL_ACCOUNTS = [
    {"email": "deviramrani489@gmail.com",      "password": "eprrbxhaibzwwhqv", "name": "Devi Ramrani"},
    {"email": "fearlessaditya322@gmail.com",   "password": "kmbpigpqrmlgyala", "name": "Aditya Mishra"},
    {"email": "moderatorhelper.org@gmail.com", "password": "loanhgpmocqmwbka", "name": "Moderator Helper"},
    {"email": "helpingpeople.or@gmail.com",    "password": "qpgoyrpuyesdxfnj", "name": "Community Support"},
]

# ══════════════════════════════════════════════════════════════════════
# 📁 FILE PATHS
# ══════════════════════════════════════════════════════════════════════
ACCOUNTS_FILE = Path("accounts.json")
SUDO_FILE     = Path("sudo_users.json")
PROXY_HEALTH  = Path("proxy_health.json")
LOGS_DIR      = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# 🎨 ANSI COLORS
# ══════════════════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; MAGENTA = "\033[95m"; CYAN = "\033[96m"; WHITE = "\033[97m"
    BG_RED = "\033[41m"; BG_GRN = "\033[42m"

def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{C.CYAN}{C.BOLD}")
    print(f"  ⚡ Ultimate Reporter v{BOT_VERSION} — running...{C.RESET}")
    print(f"{C.DIM}  Proxy mode: {'ON' if PROXY_ENABLED else 'OFF (direct)'}{C.RESET}\n")

# ══════════════════════════════════════════════════════════════════════
# 📊 LOGGING
# ══════════════════════════════════════════════════════════════════════
class ColorFormatter(logging.Formatter):
    COLORS = {"DEBUG": C.DIM + C.WHITE, "INFO": C.CYAN, "WARNING": C.YELLOW,
              "ERROR": C.RED, "CRITICAL": C.BG_RED + C.WHITE}
    def format(self, record):
        col = self.COLORS.get(record.levelname, C.WHITE)
        ts  = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        lvl = f"{col}{record.levelname:<8}{C.RESET}"
        return f"{C.DIM}{ts}{C.RESET} {lvl} {record.getMessage()}"

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger("UltimateReporter")
logger.setLevel(logging.INFO)
_h = logging.StreamHandler()
_h.setFormatter(ColorFormatter())
logger.addHandler(_h)

# ══════════════════════════════════════════════════════════════════════
# 🗂  GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════
accounts: Dict[str, TelegramClient] = {}
account_proxy_map: Dict[str, dict]  = {}
account_device_map: Dict[str, dict] = {}  # phone -> device fingerprint
proxy_health: Dict[str, dict]       = {}
proxy_cursor                        = 0
sudo_users: set                     = set()
sudo_info: Dict[int, dict]          = {}
live_logs: List[str]                = []
report_stats = {"total": 0, "success": 0, "failed": 0, "start_time": None}

# Conversation states
(PHONE, CODE, PASSWORD,
 GRP_LINK, MSG_LINK, MSG_LINK_MORE, REASON_CAT, REASON_SUB, CUSTOM_MSG, COUNT,
 MAIL_SUBJECT, MAIL_BODY, MAIL_EVIDENCE, MAIL_RECIPIENT, MAIL_BLAST_COUNT, MAIL_RESEND,
 RM_PHONE,
 AR_USER, AR_REASON, AR_OTHER_MSG, AR_COUNT,
 BR_USER, BR_CAT, BR_SUB, BR_MSG, BR_COUNT,
 GR_GRP_LINK, GR_MSG_LINK, GR_MSG_LINK_MORE, GR_CAT, GR_SUB, GR_CUSTOM_MSG, GR_COUNT
) = range(33)

# ══════════════════════════════════════════════════════════════════════
# 🧠 FULL TELEGRAM REPORT CATEGORIES (matches official 3-dot menu tree)
# ══════════════════════════════════════════════════════════════════════
FULL_REPORT_CATEGORIES: Dict[str, dict] = {
    "spam": {
        "emoji": "🚫", "label": "Spam",
        "api": types.InputReportReasonSpam(),
        "subs": [
            ("spam_bulk",    "📨 Bulk / mass messaging"),
            ("spam_promo",   "📢 Unsolicited promotion / ads"),
            ("spam_scam",    "💸 Scam / phishing"),
            ("spam_repost",  "🔁 Repetitive content"),
            ("spam_other",   "❓ Other spam"),
        ],
    },
    "violence": {
        "emoji": "🔪", "label": "Violence",
        "api": types.InputReportReasonViolence(),
        "subs": [
            ("vio_threat",   "⚠️ Direct threats"),
            ("vio_graphic",  "🩸 Graphic violence"),
            ("vio_incite",   "🔥 Incitement to violence"),
            ("vio_terror",   "💣 Terrorism / extremism"),
            ("vio_weapon",   "🔫 Weapons / dangerous goods"),
        ],
    },
    "porn": {
        "emoji": "🔞", "label": "Pornography",
        "api": types.InputReportReasonPornography(),
        "subs": [
            ("porn_explicit", "🔞 Explicit sexual content"),
            ("porn_nonconsent","⛔ Non-consensual content"),
            ("porn_revenge",  "💔 Revenge porn"),
            ("porn_solicit",  "💋 Solicitation"),
        ],
    },
    "child": {
        "emoji": "👶", "label": "Child Abuse",
        "api": types.InputReportReasonChildAbuse(),
        "subs": [
            ("child_csam",   "🚨 CSAM (child sexual abuse material)"),
            ("child_groom",  "⚠️ Grooming"),
            ("child_explo",  "💀 Child exploitation"),
            ("child_endang", "🛑 Endangering a minor"),
        ],
    },
    "drugs": {
        "emoji": "💊", "label": "Illegal Drugs",
        "api": types.InputReportReasonIllegalDrugs(),
        "subs": [
            ("drug_sell",  "💉 Selling drugs"),
            ("drug_promo", "📢 Promoting drug use"),
            ("drug_traffic","🚚 Drug trafficking"),
        ],
    },
    "personal": {
        "emoji": "🆔", "label": "Personal Details",
        "api": types.InputReportReasonPersonalDetails(),
        "subs": [
            ("pd_doxx",    "📍 Doxxing / leaked address"),
            ("pd_id",      "🪪 ID / passport leak"),
            ("pd_finance", "💳 Financial info leak"),
            ("pd_private", "🔒 Other private info"),
        ],
    },
    "fake": {
        "emoji": "🎭", "label": "Fake Account",
        "api": types.InputReportReasonFake(),
        "subs": [
            ("fake_imperson", "🎭 Impersonating someone"),
            ("fake_celeb",    "⭐ Pretending to be a celebrity"),
            ("fake_official", "🏛️ Pretending to be official"),
            ("fake_scam",     "💰 Scam profile"),
        ],
    },
    "copyright": {
        "emoji": "©️", "label": "Copyright",
        "api": types.InputReportReasonCopyright(),
        "subs": [
            ("cr_video", "🎬 Stolen video"),
            ("cr_audio", "🎵 Stolen audio / music"),
            ("cr_image", "🖼️ Stolen image / artwork"),
            ("cr_text",  "📝 Stolen text / article"),
        ],
    },
    "geoirre": {
        "emoji": "🌍", "label": "Geographically Irrelevant",
        "api": types.InputReportReasonGeoIrrelevant(),
        "subs": [
            ("geo_loc",   "📍 Wrong location"),
            ("geo_lang",  "🗣️ Wrong language community"),
        ],
    },
    "other": {
        "emoji": "❓", "label": "Other",
        "api": types.InputReportReasonOther(),
        "subs": [
            ("oth_harass", "😡 Harassment / bullying"),
            ("oth_hate",   "💢 Hate speech"),
            ("oth_misinfo","📰 Misinformation"),
            ("oth_self",   "💔 Self-harm content"),
            ("oth_other",  "❓ Other"),
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════
# 💬 POWERFUL REPORT MESSAGE BUILDER
# ══════════════════════════════════════════════════════════════════════
REALISTIC_REPORT_MSGS = [
    "This content clearly violates Telegram's Terms of Service and Community Guidelines. The material is harmful, distressing, and should be removed immediately to protect other users.",
    "I am reporting this account for repeatedly distributing harmful content that puts users at risk. This is not a one-off — it is a pattern of abuse that demands urgent moderator action.",
    "The reported entity is engaged in activity that is illegal under multiple jurisdictions and is causing real-world harm to vulnerable users. Please escalate this to your Trust & Safety team.",
    "This account/channel is being used to spread targeted abuse and is creating an unsafe environment for the wider Telegram community. Immediate suspension is requested.",
    "The content shown is deeply disturbing, exploitative, and clearly designed to harm or deceive users. I am filing this report on behalf of affected community members.",
    "This is a coordinated abuse pattern that bypasses normal moderation. I urge Telegram's safety team to review the full history of this account and take permanent action.",
    "The reported material directly violates platform rules concerning user safety, dignity, and protection from harm. Continued presence of this account undermines trust in the platform.",
    "Multiple users in our community have flagged this account. The behavior is sustained, deliberate, and harmful. We respectfully request a permanent ban.",
]

REPORT_PREFIXES = [
    "Hello Telegram Safety Team,",
    "Dear Trust & Safety Moderators,",
    "To the Telegram Abuse Review Team:",
    "Reporting on behalf of affected users —",
    "Urgent moderation request:",
    "Filing this report after careful review:",
]

CONTEXT_PHRASES = [
    "I have personally witnessed multiple instances of this behavior.",
    "Several members of our community have independently confirmed this pattern.",
    "Screenshots and evidence are available on request.",
    "This is an ongoing situation that has escalated over time.",
    "The harm caused is concrete and measurable.",
    "Other users have already left the platform due to this account.",
]

REPORT_CLOSINGS = [
    "Please act swiftly. Thank you for protecting the community.",
    "Your prompt action will prevent further harm.",
    "I trust your team will take this matter seriously.",
    "Looking forward to your decisive response.",
    "Thank you for keeping Telegram safe.",
    "We are counting on Telegram's commitment to user safety.",
]

def craft_report_message(base_msg: str, sub_label: str = "") -> str:
    """Build a powerful, multi-paragraph contextual report message."""
    prefix   = random.choice(REPORT_PREFIXES)
    pool_msg = random.choice(REALISTIC_REPORT_MSGS)
    context  = random.choice(CONTEXT_PHRASES)
    closing  = random.choice(REPORT_CLOSINGS)

    parts = [prefix]

    if sub_label and sub_label not in ("N/A", ""):
        parts.append(f"Reported category: {sub_label}.")

    # Main body
    if base_msg and base_msg.strip() and base_msg.strip().lower() not in ("skip", "default", ""):
        roll = random.random()
        if roll < 0.5:
            parts.append(base_msg.strip())
            parts.append(context)
        else:
            parts.append(pool_msg)
            parts.append(base_msg.strip())
    else:
        parts.append(pool_msg)
        parts.append(context)

    parts.append(closing)

    final = " ".join(parts)
    # Telegram report message limit ~ 500 chars
    if len(final) > 480:
        final = final[:477] + "..."
    return final

# ══════════════════════════════════════════════════════════════════════
# 💾 ATOMIC JSON
# ══════════════════════════════════════════════════════════════════════
def atomic_save_json(path: Path, data) -> bool:
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            try: os.fsync(f.fileno())
            except: pass
        tmp.replace(path)
        return True
    except Exception as e:
        logger.error(f"Atomic save failed for {path}: {e}")
        return False

def safe_load_json(path: Path, default):
    if not path.exists(): return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"JSON load fail {path}: {e}")
        try: path.rename(path.with_suffix(path.suffix + f".corrupt.{int(time.time())}"))
        except: pass
        return default

# ══════════════════════════════════════════════════════════════════════
# 🔐 SUDO
# ══════════════════════════════════════════════════════════════════════
def load_sudo():
    global sudo_users, sudo_info
    data = safe_load_json(SUDO_FILE, {"ids": [], "info": {}})
    try:
        sudo_users = set(int(x) for x in data.get("ids", []))
        sudo_info  = {}
        for k, v in data.get("info", {}).items():
            try: sudo_info[int(k)] = v if isinstance(v, dict) else {"name": str(v), "username": ""}
            except: continue
        add_log(f"🔐 Sudo loaded: {len(sudo_users)} user(s)")
    except Exception as e:
        logger.error(f"Sudo parse error: {e}")
        sudo_users = set(); sudo_info = {}

def save_sudo():
    payload = {"ids":  sorted(list(sudo_users)),
               "info": {str(k): v for k, v in sudo_info.items()}}
    if atomic_save_json(SUDO_FILE, payload):
        add_log(f"💾 Sudo saved: {len(sudo_users)} user(s)")

def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in sudo_users

# ══════════════════════════════════════════════════════════════════════
# 🌐 PROXY HEALTH
# ══════════════════════════════════════════════════════════════════════
def _proxy_key(p: dict) -> str:
    return f"{p.get('type','?')}://{p.get('addr','?')}:{p.get('port','?')}"

def load_proxy_health():
    global proxy_health
    proxy_health = safe_load_json(PROXY_HEALTH, {})

def save_proxy_health():
    atomic_save_json(PROXY_HEALTH, proxy_health)

def mark_proxy_result(proxy: Optional[dict], success: bool):
    if not proxy: return
    k = _proxy_key(proxy)
    h = proxy_health.setdefault(k, {"ok": 0, "fail": 0, "bad": False})
    if success: h["ok"] += 1
    else:       h["fail"] += 1
    total = h["ok"] + h["fail"]
    if total >= 3 and h["fail"] / total > 0.7:
        h["bad"] = True
    save_proxy_health()

def healthy_proxies() -> List[dict]:
    if not PROXY_LIST: return []
    out = []
    for p in PROXY_LIST:
        h = proxy_health.get(_proxy_key(p), {})
        if not h.get("bad", False):
            out.append(p)
    return out

def next_proxy() -> Optional[dict]:
    global proxy_cursor
    if not PROXY_ENABLED:
        return None
    pool = healthy_proxies()
    if not pool: return None
    p = pool[proxy_cursor % len(pool)]
    proxy_cursor += 1
    return p

def assign_proxies():
    account_proxy_map.clear()
    if not PROXY_ENABLED: return
    pool = healthy_proxies()
    if not pool: return
    for i, phone in enumerate(accounts.keys()):
        account_proxy_map[phone] = pool[i % len(pool)]

# ══════════════════════════════════════════════════════════════════════
# 📊 LOGS + STATS
# ══════════════════════════════════════════════════════════════════════
def add_log(msg: str):
    ts    = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    live_logs.append(entry)
    logger.info(msg)
    if len(live_logs) > 1500:
        live_logs.pop(0)
    try:
        log_file = LOGS_DIR / f"activity_{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass

def get_logs(limit: int = 80) -> str:
    return "\n".join(live_logs[-limit:]) if live_logs else "No logs yet."

def clear_logs():
    global live_logs
    live_logs = []

def update_stats(success: bool):
    if success: report_stats["success"] += 1
    else:       report_stats["failed"]  += 1

def reset_stats():
    global report_stats
    report_stats = {"total": 0, "success": 0, "failed": 0, "start_time": None}

def get_stats() -> str:
    elapsed = ""
    if report_stats["start_time"]:
        s = (datetime.now() - report_stats["start_time"]).seconds
        elapsed = f" | ⏱ {s//60}m {s%60}s"
    tot = report_stats["success"] + report_stats["failed"]
    return (f"📊 {tot}/{report_stats['total']} | "
            f"✅ {report_stats['success']} | "
            f"❌ {report_stats['failed']}{elapsed}")

def log_report_file(phone, target_id, reason, status, detail=""):
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = LOGS_DIR / f"reports_{datetime.now().strftime('%Y-%m-%d')}.log"
    line     = f"[{ts}] {phone} | TGT:{target_id} | {reason} | {status}"
    if detail: line += f" | {detail}"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except: pass

# ══════════════════════════════════════════════════════════════════════
# 🔧 TELETHON CLIENT BUILDER + CONNECT (with RANDOM DEVICE FINGERPRINTING)
# ══════════════════════════════════════════════════════════════════════
def build_client(session, proxy_cfg: Optional[dict], device: Optional[dict] = None) -> TelegramClient:
    if device is None:
        device = random_device()
    kwargs = dict(
        device_model=device["device_model"],
        system_version=device["system_version"],
        app_version=device["app_version"],
        lang_code=device.get("lang_code", "en"),
        system_lang_code=device.get("system_lang_code", "en-US"),
        connection_retries=3, retry_delay=2, timeout=20,
        auto_reconnect=True,
    )
    if PROXY_ENABLED and proxy_cfg and socks is not None:
        p_type = socks.SOCKS5 if proxy_cfg.get("type", "").lower() == "socks5" else socks.HTTP
        kwargs["proxy"] = (
            p_type, proxy_cfg["addr"], int(proxy_cfg["port"]), True,
            proxy_cfg.get("username"), proxy_cfg.get("password"),
        )
    return TelegramClient(session, API_ID, API_HASH, **kwargs)

async def safe_connect(client: TelegramClient, phone: str = "") -> bool:
    try:
        if client.is_connected():
            return True
        await asyncio.wait_for(client.connect(), timeout=12)
        return True
    except Exception as e:
        if PROXY_ENABLED and phone:
            add_log(f"⚠️ Proxy failed for {phone[-4:]} ({type(e).__name__}) — fallback to direct")
            try:
                try: await client.disconnect()
                except: pass
                px = account_proxy_map.get(phone)
                if px:
                    mark_proxy_result(px, False)
                    account_proxy_map.pop(phone, None)
                sess = client.session
                dev = account_device_map.get(phone) or random_device()
                new_client = build_client(sess, None, dev)
                await asyncio.wait_for(new_client.connect(), timeout=12)
                accounts[phone] = new_client
                add_log(f"✅ Direct connect OK: {phone[-4:]}")
                return True
            except Exception as e2:
                add_log(f"❌ Direct connect also failed for {phone[-4:]}: {type(e2).__name__}")
                return False
        else:
            add_log(f"❌ Connect failed: {type(e).__name__}: {str(e)[:60]}")
            return False

async def ensure_connected(phone: str) -> Optional[TelegramClient]:
    client = accounts.get(phone)
    if not client:
        return None
    try:
        if not client.is_connected():
            ok = await safe_connect(client, phone)
            if not ok:
                return None
            client = accounts.get(phone)
        try:
            if not await client.is_user_authorized():
                add_log(f"⚠️ Not authorized: {phone[-4:]}")
                return None
        except (ConnectionError, OSError):
            try: await client.disconnect()
            except: pass
            ok = await safe_connect(client, phone)
            if not ok:
                return None
            client = accounts.get(phone)
            if not await client.is_user_authorized():
                return None
        return client
    except Exception as e:
        add_log(f"⚠️ ensure_connected fail {phone[-4:]}: {type(e).__name__}")
        return None

def load_accounts():
    data = safe_load_json(ACCOUNTS_FILE, {})
    if not data: return
    proxies = healthy_proxies() if PROXY_ENABLED else []
    for i, (phone, sess) in enumerate(data.items()):
        try:
            proxy = proxies[i % len(proxies)] if proxies else None
            # 🔥 random device per account — every load = fresh fingerprint
            device = random_device()
            account_device_map[phone] = device
            client = build_client(StringSession(sess), proxy, device)
            accounts[phone] = client
            if proxy: account_proxy_map[phone] = proxy
            add_log(f"✅ Loaded: {phone} [{device['device_model']}]" + (f" [proxy: {proxy['addr']}]" if proxy else ""))
        except Exception as e:
            logger.error(f"Load error {phone}: {e}")

def save_accounts():
    try:
        data = {}
        for p, c in accounts.items():
            try:
                if c.session:
                    data[p] = StringSession.save(c.session)
            except Exception:
                continue
        if atomic_save_json(ACCOUNTS_FILE, data):
            add_log(f"💾 Saved {len(data)} accounts")
    except Exception as e:
        logger.error(f"Save error: {e}")

async def count_active() -> int:
    n = 0
    for phone, c in list(accounts.items()):
        try:
            if not c.is_connected():
                try: await asyncio.wait_for(c.connect(), timeout=8)
                except: continue
            if await c.is_user_authorized():
                n += 1
        except Exception:
            pass
    return n

async def get_any_active_client() -> Optional[TelegramClient]:
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c:
            return c
    return None

async def resolve_user_via_telethon(identifier: str) -> Tuple[Optional[int], Optional[str], str]:
    client = await get_any_active_client()
    if not client:
        if identifier.lstrip("@").lstrip("+").isdigit():
            uid = int(identifier.lstrip("@").lstrip("+"))
            return (uid, str(uid), "")
        return (None, None, "No active Telegram accounts to resolve username.")
    try:
        uname = identifier.lstrip("@")
        entity = await client.get_entity(uname if not uname.isdigit() else int(uname))
        uid    = entity.id
        name   = getattr(entity, "first_name", "") or ""
        lname  = getattr(entity, "last_name", "")  or ""
        display= f"{name} {lname}".strip() or getattr(entity, "username", "") or str(uid)
        return (uid, display, "")
    except errors.UsernameNotOccupiedError:
        return (None, None, "Username not found on Telegram.")
    except Exception as e:
        return (None, None, f"Resolve error: {str(e)[:60]}")

# ══════════════════════════════════════════════════════════════════════
# 🔍 SESSION STRING DETECTION
# ══════════════════════════════════════════════════════════════════════
def looks_like_session_string(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    cleaned = t.replace("+", "").replace(" ", "").replace("-", "")
    if cleaned.isdigit() and len(cleaned) <= 16:
        return False
    if len(t) >= 100 and re.match(r"^[A-Za-z0-9+/=_\-]+$", t):
        return True
    return False

def convert_pyrogram_to_telethon(pyro_string: str) -> Optional[str]:
    try:
        import base64
        import struct
        from telethon.crypto import AuthKey

        padded = pyro_string + "=" * (-len(pyro_string) % 4)
        try:
            decoded = base64.urlsafe_b64decode(padded)
        except Exception:
            decoded = base64.b64decode(padded)

        dc_id = None
        auth_key = None

        if len(decoded) == struct.calcsize(">BI?256sQ?"):
            dc_id, _api_id, _test, auth_key_bytes, _uid, _bot = struct.unpack(">BI?256sQ?", decoded)
            auth_key = auth_key_bytes
        elif len(decoded) == struct.calcsize(">B?256sI?"):
            dc_id, _test, auth_key_bytes, _uid, _bot = struct.unpack(">B?256sI?", decoded)
            auth_key = auth_key_bytes
        elif len(decoded) == struct.calcsize(">BI?256sQ?B"):
            dc_id, _api_id, _test, auth_key_bytes, _uid, _bot, _ = struct.unpack(">BI?256sQ?B", decoded)
            auth_key = auth_key_bytes
        else:
            return None

        dc_ips = {
            1: ("149.154.175.53", 443),
            2: ("149.154.167.51", 443),
            3: ("149.154.175.100", 443),
            4: ("149.154.167.91", 443),
            5: ("91.108.56.130", 443),
        }
        server, port = dc_ips.get(dc_id, ("149.154.167.51", 443))

        session = StringSession()
        session.set_dc(dc_id, server, port)
        session.auth_key = AuthKey(data=auth_key)
        return StringSession.save(session)
    except Exception as e:
        logger.error(f"Pyrogram→Telethon convert fail: {e}")
        return None

async def try_load_session_string(session_str: str) -> Tuple[Optional[TelegramClient], Optional[str], str]:
    proxy = next_proxy()
    device = random_device()

    # Attempt 1: Telethon native
    try:
        client = build_client(StringSession(session_str), proxy, device)
        await asyncio.wait_for(client.connect(), timeout=15)
        if await client.is_user_authorized():
            me = await client.get_me()
            phone = me.phone if me.phone else None
            ident = f"+{phone}" if phone else f"id{me.id}"
            return (client, ident, "")
        else:
            try: await client.disconnect()
            except: pass
    except Exception as e:
        logger.info(f"Telethon native parse failed: {type(e).__name__}: {str(e)[:50]}")

    # Attempt 2: Pyrogram → Telethon convert
    try:
        telethon_str = convert_pyrogram_to_telethon(session_str)
        if telethon_str:
            device2 = random_device()
            client = build_client(StringSession(telethon_str), proxy, device2)
            await asyncio.wait_for(client.connect(), timeout=15)
            if await client.is_user_authorized():
                me = await client.get_me()
                phone = me.phone if me.phone else None
                ident = f"+{phone}" if phone else f"id{me.id}"
                return (client, ident, "")
            else:
                try: await client.disconnect()
                except: pass
                return (None, None, "Session not authorized")
    except Exception as e:
        logger.error(f"Pyrogram convert failed: {type(e).__name__}: {str(e)[:80]}")
        return (None, None, f"Pyrogram convert error: {str(e)[:60]}")

    return (None, None, "Invalid session string (not Telethon or Pyrogram format)")

# ══════════════════════════════════════════════════════════════════════
# 🔗 LINK PARSERS
# ══════════════════════════════════════════════════════════════════════
def parse_group_link(link: str) -> Tuple[Optional[str], Optional[str], str]:
    try:
        link = link.strip().rstrip("/")
        if "/+" in link or "/joinchat/" in link:
            return (link.split("/")[-1].replace("+", ""), "invite", "")
        elif "/c/" in link:
            parts = link.split("/")
            uname = parts[-2] if parts[-1].isdigit() else parts[-1]
            return (uname, "private_channel", "")
        elif "t.me/" in link:
            parts = link.split("/")
            uname = parts[-1] if not parts[-1].isdigit() else parts[-2]
            return (uname.replace("@", ""), "username", "")
        return (None, None, "Invalid group link format")
    except Exception as e:
        return (None, None, f"Parse error: {e}")

def parse_message_link(link: str) -> Tuple[Optional[str], Optional[int], str]:
    try:
        link = link.strip().rstrip("/")
        if "/c/" in link:
            parts = link.split("/")
            return (str(int(parts[-2])), int(parts[-1]), "")
        elif "t.me/" in link:
            parts = link.split("/")
            return (parts[-2].replace("@", ""), int(parts[-1]), "")
        return (None, None, "Invalid message link format")
    except Exception as e:
        return (None, None, f"Parse error: {e}")

# ══════════════════════════════════════════════════════════════════════
# 🔄 GROUP JOIN (parallel)
# ══════════════════════════════════════════════════════════════════════
async def _join_one(phone: str, identifier: str, link_type: str) -> Tuple[bool, str]:
    client = await ensure_connected(phone)
    if not client:
        return (False, "no-conn")
    try:
        if link_type == "invite":
            try:
                await client(ImportChatInviteRequest(identifier))
                return (True, "joined")
            except errors.UserAlreadyParticipantError:
                return (True, "already")
            except errors.InviteHashExpiredError:
                return (False, "expired")
            except errors.InviteHashInvalidError:
                return (False, "invalid")
            except Exception as e:
                return (False, type(e).__name__)
        elif link_type == "private_channel":
            try:
                await client(JoinChannelRequest(identifier))
                return (True, "joined")
            except errors.UserAlreadyParticipantError:
                return (True, "already")
            except Exception as e:
                return (False, type(e).__name__)
        return (True, "skip-public")
    except Exception as e:
        return (False, type(e).__name__)

async def join_group_all(identifier, link_type) -> Tuple[int, int]:
    if link_type == "username":
        add_log(f"ℹ️ Public group '{identifier}' — skipping join.")
        return (len(accounts), 0)
    # parallel join with small jitter
    async def _wrap(phone):
        await asyncio.sleep(random.uniform(0, 1.0))
        return await _join_one(phone, identifier, link_type)
    results = await asyncio.gather(*[_wrap(p) for p in list(accounts.keys())], return_exceptions=True)
    ok = fail = 0
    for r in results:
        if isinstance(r, tuple) and r[0]:
            ok += 1
        else:
            fail += 1
    add_log(f"🔄 Join done: ✅{ok} ❌{fail}")
    return (ok, fail)

# ══════════════════════════════════════════════════════════════════════
# 🎯 ENTITY RESOLVER (private channel friendly)
# ══════════════════════════════════════════════════════════════════════
async def resolve_chat_entity(client, identifier: str, link_type: str):
    # Numeric private channel id → try multiple forms
    if str(identifier).lstrip("-").isdigit():
        raw = str(identifier).lstrip("-")
        for candidate in (int(f"-100{raw}"), int(raw), -int(raw)):
            try:
                return await client.get_input_entity(candidate)
            except Exception:
                continue
        # last resort - PeerChannel
        try:
            return await client.get_input_entity(tl_types.PeerChannel(int(raw)))
        except Exception:
            pass
    try:
        return await client.get_input_entity(identifier)
    except Exception:
        pass
    try:
        ent = await client.get_entity(identifier)
        return await client.get_input_entity(ent)
    except Exception as e:
        raise e

# ══════════════════════════════════════════════════════════════════════
# 🚀 CORE MESSAGE REPORT ENGINE (fast, auto-reconnect, private-friendly)
# ══════════════════════════════════════════════════════════════════════
async def send_report(phone, channel_id, msg_id, reason_api, custom_msg,
                      link_type="username", sub_label="") -> Tuple[bool, str]:
    client = await ensure_connected(phone)
    if not client:
        return (False, "Account disconnected / unauthorized")

    proxy = account_proxy_map.get(phone)
    try:
        try:
            entity = await resolve_chat_entity(client, channel_id, link_type)
        except Exception as e:
            mark_proxy_result(proxy, False)
            return (False, f"Entity error: {str(e)[:50]}")

        msg_id_int = int(msg_id)
        # 🔥 ultra-tight delay (fast mode)
        await asyncio.sleep(random.uniform(0.05, 0.25))

        # M1: standard messages.report
        try:
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=[msg_id_int],
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                return (True, "M1:messages.report")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except errors.MessageIdInvalidError:
            return (False, "Invalid Message ID")
        except errors.ChannelPrivateError:
            # try re-resolve via username/id fallbacks
            pass
        except errors.UserBannedInChannelError:
            return (False, "Account banned in channel")
        except (ConnectionError, OSError):
            client = await ensure_connected(phone)
            if not client:
                return (False, "Reconnect failed")
        except Exception:
            pass

        # M2: prefetch + report (helps private channels)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        try:
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
            entity = await resolve_chat_entity(client, channel_id, link_type)
            msgs = await client.get_messages(entity, ids=msg_id_int)
            if msgs:
                result = await client(functions.messages.ReportRequest(
                    peer=entity, id=[msg_id_int],
                    reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
                if result:
                    mark_proxy_result(proxy, True)
                    return (True, "M2:prefetch+report")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except Exception:
            pass

        # M3: account.reportPeer (channel-level, useful for private)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        try:
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
            entity = await resolve_chat_entity(client, channel_id, link_type)
            result = await client(functions.account.ReportPeerRequest(
                peer=entity, reason=reason_api,
                message=f"Re: Msg ID {msg_id} — {craft_report_message(custom_msg, sub_label)}"))
            if result:
                mark_proxy_result(proxy, True)
                return (True, "M3:account.reportPeer")
        except Exception:
            pass

        # M4: re-resolve + report
        await asyncio.sleep(random.uniform(0.05, 0.2))
        try:
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
            entity = await resolve_chat_entity(client, channel_id, link_type)
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=[msg_id_int],
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                return (True, "M4:re-resolve+report")
        except Exception:
            pass

        mark_proxy_result(proxy, False)
        return (False, "All methods failed")
    except errors.ChannelPrivateError:
        return (False, "Private channel — no access")
    except errors.UserBannedInChannelError:
        return (False, "Account banned in channel")
    except Exception as e:
        mark_proxy_result(proxy, False)
        return (False, f"{type(e).__name__}: {str(e)[:40]}")

# ══════════════════════════════════════════════════════════════════════
# 🎯 GROUP REPORT ENGINE (3-dot menu style — select msg in group)
# Uses messages.Report with sub-category context, simulating
# "tap msg → 3-dot → Report → category → sub → reason → submit"
# ══════════════════════════════════════════════════════════════════════
async def send_group_report(phone, channel_id, msg_id, reason_api, custom_msg,
                            link_type="username", cat_label="", sub_label="") -> Tuple[bool, str]:
    """
    Group-style report: simulates Telegram in-group 3-dot menu flow.
    For each message link, the selected message is reported via the
    in-group 'Report Message' API path (messages.Report) which is what
    happens when you tap the message → 3-dot → Report.
    """
    client = await ensure_connected(phone)
    if not client:
        return (False, "Account disconnected")

    proxy = account_proxy_map.get(phone)
    try:
        try:
            entity = await resolve_chat_entity(client, channel_id, link_type)
        except Exception as e:
            return (False, f"Entity error: {str(e)[:50]}")

        msg_id_int = int(msg_id)
        # Build group-style contextual message
        ctx_msg = f"[Group Report — {cat_label} / {sub_label}] " + craft_report_message(custom_msg, sub_label)
        if len(ctx_msg) > 480:
            ctx_msg = ctx_msg[:477] + "..."

        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Step 1: ensure msg is visible (mimics tapping the message)
        try:
            await client.get_messages(entity, ids=msg_id_int)
        except Exception:
            pass

        # Step 2: file the messages.Report (3-dot menu → Report path)
        try:
            r = await client(functions.messages.ReportRequest(
                peer=entity, id=[msg_id_int],
                reason=reason_api, message=ctx_msg))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "GR-M1:msg-report")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except errors.MessageIdInvalidError:
            return (False, "Invalid Message ID")
        except errors.UserBannedInChannelError:
            return (False, "Account banned")
        except Exception:
            pass

        # Step 3: peer-level reinforcement
        await asyncio.sleep(random.uniform(0.05, 0.2))
        try:
            client = await ensure_connected(phone)
            if client:
                r = await client(functions.account.ReportPeerRequest(
                    peer=entity, reason=reason_api, message=ctx_msg))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "GR-M2:peer-report")
        except Exception:
            pass

        # Step 4: retry msg report after re-resolve
        await asyncio.sleep(random.uniform(0.05, 0.2))
        try:
            client = await ensure_connected(phone)
            if client:
                entity = await resolve_chat_entity(client, channel_id, link_type)
                r = await client(functions.messages.ReportRequest(
                    peer=entity, id=[msg_id_int],
                    reason=reason_api, message=ctx_msg))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "GR-M3:retry")
        except Exception:
            pass

        mark_proxy_result(proxy, False)
        return (False, "All group-report methods failed")
    except Exception as e:
        return (False, f"{type(e).__name__}: {str(e)[:40]}")

# ══════════════════════════════════════════════════════════════════════
# 📸 NUCLEAR PFP REPORT
# ══════════════════════════════════════════════════════════════════════
PFP_REPORT_REASONS = {
    "pfp_porn":     ("🔞 Pornographic",        types.InputReportReasonPornography()),
    "pfp_child":    ("👶 Child Abuse",         types.InputReportReasonChildAbuse()),
    "pfp_violen":   ("🔪 Violence",            types.InputReportReasonViolence()),
    "pfp_fake":     ("🎭 Fake / Impersonation",types.InputReportReasonFake()),
    "pfp_personal": ("🆔 Personal Details",    types.InputReportReasonPersonalDetails()),
    "pfp_other":    ("❓ Other",               types.InputReportReasonOther()),
}

async def report_profile_photo_nuclear(phone, user_entity, photos, reason_api, custom_msg) -> Tuple[bool, str]:
    client = await ensure_connected(phone)
    if not client:
        return (False, "Account disconnected")
    proxy = account_proxy_map.get(phone)
    methods_tried = []

    if photos:
        try:
            photo = photos[0]
            input_photo = tl_types.InputPhoto(
                id=photo.id, access_hash=photo.access_hash,
                file_reference=photo.file_reference)
            await asyncio.sleep(random.uniform(0.1, 0.4))
            result = await client(functions.account.ReportProfilePhotoRequest(
                peer=user_entity, photo_id=input_photo,
                reason=reason_api, message=craft_report_message(custom_msg)))
            if result:
                mark_proxy_result(proxy, True)
                return (True, "Success (M1: ReportProfilePhoto)")
            methods_tried.append("M1")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except Exception as e:
            methods_tried.append(f"M1-fail({type(e).__name__})")

    if photos and len(photos) > 1:
        for idx, ph in enumerate(photos[1:6], start=2):
            try:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                client = await ensure_connected(phone)
                if not client: break
                ip = tl_types.InputPhoto(id=ph.id, access_hash=ph.access_hash, file_reference=ph.file_reference)
                r = await client(functions.account.ReportProfilePhotoRequest(
                    peer=user_entity, photo_id=ip,
                    reason=reason_api, message=craft_report_message(custom_msg)))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, f"Success (M2: older photo #{idx})")
            except errors.FloodWaitError as e:
                return (False, f"FloodWait {e.seconds}s")
            except Exception:
                continue
        methods_tried.append("M2")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            r = await client(functions.account.ReportPeerRequest(
                peer=user_entity, reason=reason_api,
                message=f"Profile photo violation. {craft_report_message(custom_msg)}"))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "Success (M3: ReportPeer)")
            methods_tried.append("M3")
    except Exception as e:
        methods_tried.append(f"M3-fail({type(e).__name__})")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            refreshed = await client.get_entity(user_entity)
            fresh_photos = await client.get_profile_photos(refreshed)
            if fresh_photos:
                fp = fresh_photos[0]
                ip = tl_types.InputPhoto(id=fp.id, access_hash=fp.access_hash, file_reference=fp.file_reference)
                r = await client(functions.account.ReportProfilePhotoRequest(
                    peer=refreshed, photo_id=ip,
                    reason=reason_api, message=craft_report_message(custom_msg)))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "Success (M4: refresh+retry)")
            methods_tried.append("M4")
    except Exception as e:
        methods_tried.append(f"M4-fail({type(e).__name__})")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            r = await client(functions.messages.ReportRequest(
                peer=user_entity, id=[0], reason=reason_api,
                message=craft_report_message(custom_msg)))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "Success (M5: messages.report)")
            methods_tried.append("M5")
    except Exception:
        methods_tried.append("M5")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            r = await client(functions.messages.ReportSpamRequest(peer=user_entity))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "Success (M6: ReportSpam fallback)")
            methods_tried.append("M6")
    except Exception:
        methods_tried.append("M6")

    mark_proxy_result(proxy, False)
    return (False, f"All 6 methods failed ({','.join(methods_tried)})")

# ══════════════════════════════════════════════════════════════════════
# 📧 GMAIL
# ══════════════════════════════════════════════════════════════════════
async def _send_single_gmail(acc: dict, subject: str, body: str,
                              recipient: str, evidence: Optional[bytes],
                              ev_name: str, attempt: int) -> Tuple[bool, str]:
    try:
        subj = subject if attempt == 1 else f"{subject} [Ref #{random.randint(1000,9999)}]"
        msg_obj = MIMEMultipart()
        msg_obj["From"]    = f"{acc['name']} <{acc['email']}>"
        msg_obj["To"]      = recipient
        msg_obj["Subject"] = subj
        msg_obj.attach(MIMEText(body, "plain"))
        if evidence:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(evidence)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{ev_name}"')
            msg_obj.attach(part)
        loop = asyncio.get_event_loop()
        def _smtp_send():
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
                srv.login(acc["email"], acc["password"])
                srv.sendmail(acc["email"], recipient, msg_obj.as_string())
        await loop.run_in_executor(None, _smtp_send)
        add_log(f"✅ Gmail #{attempt}: {acc['email']}")
        return (True, f"✅ {acc['name']} ({acc['email']})")
    except Exception as e:
        add_log(f"❌ Gmail fail #{attempt} {acc['email']}: {e}")
        return (False, f"❌ {acc['name']} → {str(e)[:50]}")

async def do_gmail_blast_round(context, round_num: int) -> Tuple[int, int, str]:
    subject   = context.user_data.get("mail_subject",  "Report Submission")
    body      = context.user_data.get("mail_body",     "")
    recipient = context.user_data.get("mail_recipient","")
    evidence  = context.user_data.get("mail_evidence", None)
    ev_name   = context.user_data.get("mail_ev_name",  "evidence.jpg")
    tasks = [_send_single_gmail(acc, subject, body, recipient, evidence, ev_name, round_num) for acc in GMAIL_ACCOUNTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    lines = []; ok = 0
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            lines.append(f"❌ {GMAIL_ACCOUNTS[i]['name']} → Exception")
        else:
            success, text = res
            if success: ok += 1
            lines.append(text)
    return (ok, len(GMAIL_ACCOUNTS) - ok, "\n".join(lines))

async def do_gmail_blast_n_times(context, count: int, update_msg=None):
    total_ok = 0; total_fail = 0; details_all = []
    for r in range(1, count + 1):
        ok, fail, details = await do_gmail_blast_round(context, r)
        total_ok += ok; total_fail += fail
        details_all.append(f"━━ Round {r}/{count} ━━\n{details}")
        if update_msg:
            try:
                await update_msg.reply_text(
                    f"📨 Round {r}/{count} done — ✅ {ok}/{len(GMAIL_ACCOUNTS)}",
                    parse_mode="HTML")
            except: pass
        if r < count:
            await asyncio.sleep(random.uniform(1.0, 2.5))
    return (total_ok, total_fail, "\n\n".join(details_all))

# ══════════════════════════════════════════════════════════════════════
# 🎬 ANIMATED START
# ══════════════════════════════════════════════════════════════════════
async def animated_start(message):
    frames = [
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n<code>▱▱▱▱▱▱▱▱▱▱</code>  0%",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n<code>▰▰▱▱▱▱▱▱▱▱</code>  20%\n\n🔧 Loading core modules...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n<code>▰▰▰▰▱▱▱▱▱▱</code>  40%\n\n🌐 Verifying network...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n<code>▰▰▰▰▰▰▱▱▱▱</code>  60%\n\n📸 Arming PFP nuclear engine...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n<code>▰▰▰▰▰▰▰▰▱▱</code>  80%\n\n🛡️ Engaging stealth mode...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n<code>▰▰▰▰▰▰▰▰▰▰</code>  100%\n\n🚀 <b>ONLINE</b> — ready to strike 😎",
    ]
    msg = await message.reply_text(frames[0], parse_mode="HTML")
    for f in frames[1:]:
        await asyncio.sleep(0.35)
        try:
            await msg.edit_text(f, parse_mode="HTML")
        except Exception:
            pass
    await asyncio.sleep(0.2)
    return msg

def _main_menu_keyboard(is_owner: bool):
    rows = [
        [InlineKeyboardButton("📩 Message Report", callback_data="MENU|report"),
         InlineKeyboardButton("👥 Group Report",   callback_data="MENU|groupreport")],
        [InlineKeyboardButton("👤 Account Report", callback_data="MENU|accountreport"),
         InlineKeyboardButton("🤖 Bot Report",     callback_data="MENU|botreport")],
        [InlineKeyboardButton("📧 Mass Gmail",     callback_data="MENU|massgmail"),
         InlineKeyboardButton("➕ Add Account",    callback_data="MENU|addaccount")],
        [InlineKeyboardButton("📋 All Accounts",   callback_data="MENU|allaccounts"),
         InlineKeyboardButton("🗑️ Remove Account",callback_data="MENU|rmaccount")],
        [InlineKeyboardButton("📊 Logs",           callback_data="MENU|logs"),
         InlineKeyboardButton("🧹 Clear Logs",     callback_data="MENU|clearlogs")],
        [InlineKeyboardButton("🌐 Proxy Status",   callback_data="MENU|proxystatus"),
         InlineKeyboardButton("🔄 Reload Proxies", callback_data="MENU|reloadproxies")],
        [InlineKeyboardButton("ℹ️ Help",           callback_data="MENU|help"),
         InlineKeyboardButton("♻️ Restart Bot",    callback_data="MENU|restart")],
    ]
    if is_owner:
        rows.append([InlineKeyboardButton("🔑 Sudo List", callback_data="MENU|sudolist"),
                     InlineKeyboardButton("⚙️ Toggle Proxy", callback_data="MENU|toggleproxy")])
    return InlineKeyboardMarkup(rows)

# ══════════════════════════════════════════════════════════════════════
# 🤖 COMMANDS
# ══════════════════════════════════════════════════════════════════════
async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized.\nContact owner for access.")
        return
    is_owner = (update.effective_user.id == OWNER_ID)
    owner_tag = "👑 Owner" if is_owner else "🔑 Sudo"

    anim_msg = await animated_start(update.message)
    await asyncio.sleep(0.3)

    proxy_status = "🟢 ON" if PROXY_ENABLED else "⚡ OFF (direct)"
    welcome = (
        f"⚡ <b>ULTIMATE REPORTER v{BOT_VERSION}</b>\n"
        f"<i>CYBER JUSTICE NUCLEAR</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ Access  : <b>{owner_tag}</b>\n"
        f"🌐 Proxy   : {proxy_status}\n"
        f"📱 Accounts: <b>{len(accounts)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 Choose an action below:"
    )
    try:
        await anim_msg.edit_text(welcome, parse_mode="HTML",
                                 reply_markup=_main_menu_keyboard(is_owner))
    except Exception:
        await update.message.reply_text(welcome, parse_mode="HTML",
                                        reply_markup=_main_menu_keyboard(is_owner))

async def menu_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_authorized(update.effective_user.id):
        await query.edit_message_text("❌ Unauthorized."); return
    action = query.data.split("|", 1)[1]

    if action == "restart":
        await query.edit_message_text(
            "♻️ <b>Restart triggered!</b>\n\n"
            "💾 Sessions saved → bot will reload in a moment...\n"
            "Use /start once it's back online.",
            parse_mode="HTML")
        await _do_restart()
        return

    info_map = {
        "report":        ("📩 <b>Message Report</b>\n\nUse /report — multi-message support + round-robin.", "/report"),
        "groupreport":   ("👥 <b>Group Report</b>\n\nUse /groupreport — 3-dot menu style with msg selection.", "/groupreport"),
        "accountreport": ("👤 <b>Account / PFP Report</b>\n\nUse /accountreport — 6-method nuclear PFP.", "/accountreport"),
        "botreport":     ("🤖 <b>Bot Report</b>\n\nUse /botreport — full Telegram report categories.", "/botreport"),
        "massgmail":     ("📧 <b>Mass Gmail Blast</b>\n\nUse /massgmail — fires all Gmail accounts × N rounds.", "/massgmail"),
        "addaccount":    ("➕ <b>Add Telegram Account</b>\n\nUse /addaccount — supports phone+OTP OR session string.", "/addaccount"),
        "rmaccount":     ("🗑️ <b>Remove Account</b>\n\nUse /rmaccount.", "/rmaccount"),
        "allaccounts":   ("📋 Use /allaccounts.", "/allaccounts"),
        "logs":          ("📊 Use /logs — sends actual log FILE.", "/logs"),
        "clearlogs":     ("🧹 Use /clearlogs.", "/clearlogs"),
        "proxystatus":   ("🌐 Use /proxystatus.", "/proxystatus"),
        "reloadproxies": ("🔄 Use /reloadproxies.", "/reloadproxies"),
        "help":          ("ℹ️ Use /help for full command list.", "/help"),
        "sudolist":      ("🔑 Use /sudolist (owner only).", "/sudolist"),
        "toggleproxy":   ("⚙️ Use /proxyon to enable, /proxyoff to disable.", "/proxyon /proxyoff"),
        "back":          ("Main menu", "/start"),
    }
    text, hint = info_map.get(action, ("Unknown action.", "/start"))
    is_owner = (update.effective_user.id == OWNER_ID)
    if action == "back":
        proxy_status = "🟢 ON" if PROXY_ENABLED else "⚡ OFF (direct)"
        welcome = (
            f"⚡ <b>ULTIMATE REPORTER v{BOT_VERSION}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 Proxy: {proxy_status} | 📱 Accounts: <b>{len(accounts)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 Choose an action:")
        try:
            await query.edit_message_text(welcome, parse_mode="HTML",
                                          reply_markup=_main_menu_keyboard(is_owner))
        except Exception:
            pass
        return
    try:
        await query.edit_message_text(
            text + f"\n\n👉 Type: <code>{hint}</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="MENU|back")
            ]]))
    except Exception:
        pass

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    await update.message.reply_text(
        f"📖 <b>HELP — v{BOT_VERSION}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 /report — Fast multi-msg report (round-robin)\n"
        "👥 /groupreport — Group 3-dot menu style report\n"
        "📸 /accountreport — Nuclear PFP report\n"
        "🤖 /botreport — Report a bot\n"
        "📧 /massgmail — Gmail blast × N\n"
        "➕ /addaccount — Phone+OTP OR Session String\n"
        "🗑️ /rmaccount — Remove account\n"
        "📋 /allaccounts — List accounts\n"
        "🌐 /proxystatus — Proxy health\n"
        "🔄 /reloadproxies — Refresh proxy pool\n"
        "⚙️ /proxyon /proxyoff — Toggle proxy (owner)\n"
        "📊 /logs — Send log FILE\n"
        "🧹 /clearlogs — Clear logs & stats\n"
        "♻️ /restart — Restart (sessions preserved)\n"
        "❌ /cancel — Cancel current flow\n\n"
        "👑 <b>Owner:</b> /sudo /rmsudo /sudolist\n\n"
        "💡 <b>Add Account modes:</b>\n"
        "  • Phone: <code>+91XXXXXXXXXX</code> → OTP flow\n"
        "  • Session: paste long Telethon/Pyrogram string\n\n"
        "🔥 <b>v15 highlights:</b>\n"
        "  • Random device fingerprint per client (iOS/Android)\n"
        "  • Multi-msg flow: send link → 'aur bhejo ya skip'\n"
        "  • Round-robin: acc1 → all msgs → acc2 → all msgs ...\n"
        "  • Private channels properly reported\n"
        "  • Group-style report (with msg selection)\n",
        parse_mode="HTML"
    )

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    add_log("❌ User cancelled flow")
    await update.message.reply_text("❌ Cancelled.\nUse /start to open the menu again.")
    return ConversationHandler.END

async def logs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    txt = f"📊 <b>ACTIVITY STATS</b>\n\n{get_stats()}\n\n<b>Recent logs:</b>\n<code>{get_logs(30)}</code>"
    if len(txt) > 4000: txt = txt[:3990] + "\n...(truncated)"
    await update.message.reply_text(txt, parse_mode="HTML")

    today = datetime.now().strftime("%Y-%m-%d")
    activity_file = LOGS_DIR / f"activity_{today}.log"
    reports_file  = LOGS_DIR / f"reports_{today}.log"
    sent_any = False
    if activity_file.exists() and activity_file.stat().st_size > 0:
        try:
            with open(activity_file, "rb") as f:
                await update.message.reply_document(
                    document=f, filename=activity_file.name,
                    caption=f"📋 Activity log — {today}\nSize: {activity_file.stat().st_size} bytes")
            sent_any = True
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not send activity log: {e}")
    if reports_file.exists() and reports_file.stat().st_size > 0:
        try:
            with open(reports_file, "rb") as f:
                await update.message.reply_document(
                    document=f, filename=reports_file.name,
                    caption=f"🎯 Reports log — {today}\nSize: {reports_file.stat().st_size} bytes")
            sent_any = True
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not send reports log: {e}")
    if not sent_any:
        await update.message.reply_text("📭 No log files yet for today.")

async def clearlogs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    clear_logs(); reset_stats()
    await update.message.reply_text("🗑️ Logs cleared & stats reset!")

async def allaccounts_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    if not accounts:
        await update.message.reply_text("📭 No accounts. Use /addaccount"); return
    txt = "📱 <b>ALL ACCOUNTS</b>\n\n"; active = 0
    for i, (phone, client) in enumerate(accounts.items(), 1):
        try:
            if not client.is_connected():
                try: await asyncio.wait_for(client.connect(), timeout=6)
                except: pass
            auth   = await client.is_user_authorized() if client.is_connected() else False
            status = "🟢 Active" if auth else "🔴 Inactive"
            if auth: active += 1
            dev = account_device_map.get(phone, {})
            dev_txt = f" [{dev.get('device_model','?')[:18]}]" if dev else ""
            proxy  = account_proxy_map.get(phone)
            p_txt  = f" [🌐 {proxy['addr']}]" if proxy else ""
        except:
            status = "🔴 Inactive"; p_txt = ""; dev_txt = ""
        txt += f"{i}. <code>{phone}</code> — {status}{dev_txt}{p_txt}\n"
    txt += f"\n📊 Total: <b>{len(accounts)}</b> | 🟢 {active} | 🔴 {len(accounts)-active}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def proxystatus_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    mode = "🟢 ENABLED" if PROXY_ENABLED else "⚡ DISABLED (direct mode)"
    if not PROXY_LIST:
        await update.message.reply_text(
            f"🌐 <b>Proxy Mode:</b> {mode}\n\n"
            f"📭 No proxies in pool.\n"
            f"Use /reloadproxies to fetch.",
            parse_mode="HTML"); return
    txt = f"🌐 <b>Proxy Mode:</b> {mode}\n"
    txt += f"Pool: <b>{len(PROXY_LIST)}</b> total\n\n"
    shown = 0
    for p in PROXY_LIST:
        if shown >= 20:
            txt += f"\n…and {len(PROXY_LIST) - shown} more"
            break
        k = _proxy_key(p)
        h = proxy_health.get(k, {"ok": 0, "fail": 0, "bad": False})
        flag = "🚫 BAD" if h.get("bad") else "🟢 OK"
        txt += f"{flag} <code>{k}</code>\n   ✅ {h.get('ok',0)} | ❌ {h.get('fail',0)}\n"
        shown += 1
    await update.message.reply_text(txt, parse_mode="HTML")

async def reloadproxies_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    msg = await update.message.reply_text("🔄 Reloading & TCP-testing free proxies...\n(takes ~20-40s)")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: load_free_proxies(15, True))
    assign_proxies()
    await msg.edit_text(f"✅ Loaded <b>{len(PROXY_LIST)}</b> working proxies\n"
                        f"Mode: {'🟢 ON' if PROXY_ENABLED else '⚡ OFF (direct)'}",
                        parse_mode="HTML")

async def proxyon_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    global PROXY_ENABLED
    PROXY_ENABLED = True
    await update.message.reply_text(
        "🟢 <b>Proxy mode: ENABLED</b>\n\n"
        "⚠️ Free proxies are often dead — if you see connection errors, run /proxyoff.",
        parse_mode="HTML")

async def proxyoff_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    global PROXY_ENABLED
    PROXY_ENABLED = False
    account_proxy_map.clear()
    await update.message.reply_text(
        "⚡ <b>Proxy mode: DISABLED</b>\n\n"
        "All accounts will use direct connection.",
        parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════════
# ♻️ RESTART
# ══════════════════════════════════════════════════════════════════════
async def _do_restart():
    try:
        save_accounts()
        save_sudo()
        save_proxy_health()
        add_log("♻️ Restart: state saved, disconnecting clients...")
        for phone, client in list(accounts.items()):
            try:
                if client.is_connected():
                    await client.disconnect()
            except: pass
        add_log("♻️ Restart: re-executing process now")
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Restart pre-cleanup error: {e}")
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def restart_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized."); return
    await update.message.reply_text(
        "♻️ <b>Restarting bot...</b>\n\n"
        "💾 All accounts & sudo data are being saved.\n"
        "🔄 Bot will reload in ~3 seconds.\n"
        "✅ Sessions will be restored automatically.\n\n"
        "Use /start once it's back online.",
        parse_mode="HTML")
    add_log(f"♻️ Restart triggered by user {update.effective_user.id}")
    await _do_restart()

# ══════════════════════════════════════════════════════════════════════
# 🔐 SUDO COMMANDS
# ══════════════════════════════════════════════════════════════════════
async def sudo_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can grant sudo."); return
    target_id = None; target_name = "Unknown"
    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        if u:
            target_id   = u.id
            target_name = ((u.first_name or "") + (" " + u.last_name if u.last_name else "")).strip() or u.username or str(u.id)
    elif ctx.args:
        arg = ctx.args[0].strip()
        target_id, target_name, err = await resolve_user_via_telethon(arg)
        if err: await update.message.reply_text(f"❌ {err}"); return
    else:
        await update.message.reply_text("⚠️ Usage:\n  /sudo @username\n  /sudo 123456789\n  Reply + /sudo"); return
    if target_id is None: await update.message.reply_text("❌ Could not resolve user."); return
    if target_id == OWNER_ID: await update.message.reply_text("ℹ️ Owner already has full access!"); return
    sudo_users.add(int(target_id))
    sudo_info[int(target_id)] = {"name": target_name, "username": "", "added": datetime.now().isoformat()}
    save_sudo(); add_log(f"🔑 Sudo granted: {target_name} ({target_id})")
    await update.message.reply_text(
        f"✅ <b>Sudo Granted!</b>\n👤 {target_name}\n🆔 <code>{target_id}</code>", parse_mode="HTML")

async def rmsudo_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can revoke sudo."); return
    target_id = None; target_name = "Unknown"
    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        if u: target_id = u.id; target_name = (u.first_name or "") or str(u.id)
    elif ctx.args:
        arg = ctx.args[0].strip()
        if arg.lstrip("@").isdigit():
            target_id   = int(arg.lstrip("@"))
            target_name = sudo_info.get(target_id, {}).get("name", str(target_id))
        else:
            target_id, target_name, err = await resolve_user_via_telethon(arg)
            if err: await update.message.reply_text(f"❌ {err}"); return
    else:
        await update.message.reply_text("⚠️ Usage:\n  /rmsudo @username\n  /rmsudo 123456789"); return
    if target_id is None: await update.message.reply_text("❌ Could not resolve user."); return
    if target_id == OWNER_ID: await update.message.reply_text("⛔ Cannot remove owner!"); return
    target_id = int(target_id)
    if target_id not in sudo_users:
        await update.message.reply_text(f"ℹ️ User <code>{target_id}</code> has no sudo.", parse_mode="HTML"); return
    sudo_users.discard(target_id)
    name = sudo_info.pop(target_id, {}).get("name", target_name)
    save_sudo(); add_log(f"🔒 Sudo revoked: {name} ({target_id})")
    await update.message.reply_text(
        f"🔒 <b>Sudo Revoked!</b>\n👤 {name}\n🆔 <code>{target_id}</code>", parse_mode="HTML")

async def sudolist_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner."); return
    if not sudo_users:
        await update.message.reply_text("📋 No sudo users.\nUse /sudo to grant."); return
    txt = "🔑 <b>SUDO USERS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, uid in enumerate(sudo_users, 1):
        info  = sudo_info.get(uid, {})
        name  = info.get("name", "Unknown")
        uname = info.get("username", "")
        txt  += f"{i}. <b>{name}</b>" + (f" (@{uname})" if uname else "") + f"\n   🆔 <code>{uid}</code>\n\n"
    txt += f"━━━━━━━━━━━━━━━━━━━━\n📊 Total: <b>{len(sudo_users)}</b>"
    await update.message.reply_text(txt, parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════════
# 📱 ADD ACCOUNT
# ══════════════════════════════════════════════════════════════════════
async def addaccount_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text(
        "📱 <b>ADD ACCOUNT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Choose your method — just send one of:\n\n"
        "1️⃣ <b>Phone number</b> (with country code):\n"
        "    <code>+91XXXXXXXXXX</code>\n"
        "    → Bot will send OTP, you reply with code\n\n"
        "2️⃣ <b>Session string</b> (Telethon OR Pyrogram):\n"
        "    Paste the long string (250+ chars)\n"
        "    → Instant login, no OTP needed\n\n"
        "💡 Bot auto-detects which one you sent.\n"
        "/cancel to abort.",
        parse_mode="HTML")
    return PHONE

async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()

    if looks_like_session_string(raw):
        wait_msg = await update.message.reply_text(
            "🔍 <b>Detected session string</b>\n"
            "⏳ Trying Telethon format... then Pyrogram fallback...",
            parse_mode="HTML")
        client, ident, err = await try_load_session_string(raw)
        if not client:
            await wait_msg.edit_text(
                f"❌ Session login failed: {err}\n\n"
                f"Try again or send a phone number, or /cancel.",
                parse_mode="HTML")
            return PHONE
        if ident in accounts:
            try: await client.disconnect()
            except: pass
            await wait_msg.edit_text(f"⚠️ Account <code>{ident}</code> already exists!", parse_mode="HTML")
            return ConversationHandler.END
        accounts[ident] = client
        account_device_map[ident] = random_device()
        save_accounts()
        add_log(f"✅ Added via session string: {ident}")
        await wait_msg.edit_text(
            f"✅ <b>Logged in via session string!</b>\n"
            f"📱 <code>{ident}</code>\n"
            f"📱 Device: <code>{account_device_map[ident]['device_model']}</code>\n"
            f"📊 Total accounts: <b>{len(accounts)}</b>",
            parse_mode="HTML")
        return ConversationHandler.END

    phone = raw
    if not phone.startswith("+"):
        phone = "+" + phone.lstrip("+")
    ctx.user_data["phone"] = phone
    if phone in accounts:
        await update.message.reply_text("⚠️ Already exists!"); return ConversationHandler.END
    try:
        proxy  = next_proxy()
        device = random_device()
        client = build_client(StringSession(), proxy, device)
        try:
            await asyncio.wait_for(client.connect(), timeout=15)
        except Exception as e:
            if proxy:
                add_log(f"⚠️ Add-account proxy failed, retrying direct: {type(e).__name__}")
                try: await client.disconnect()
                except: pass
                proxy = None
                client = build_client(StringSession(), None, device)
                await asyncio.wait_for(client.connect(), timeout=15)
            else:
                raise
        sent   = await client.send_code_request(phone)
        ctx.user_data.update({"phone_hash": sent.phone_code_hash, "temp_client": client,
                              "temp_proxy": proxy, "temp_device": device})
        await update.message.reply_text(
            "📩 <b>OTP sent!</b>\n\n"
            "Enter the code you received.\n"
            "💡 Add spaces between digits if Telegram blocks the raw code:\n"
            "    e.g. <code>1 2 3 4 5</code>",
            parse_mode="HTML")
        add_log(f"📱 Adding: {phone} [{device['device_model']}]")
        return CODE
    except errors.PhoneNumberInvalidError:
        await update.message.reply_text("❌ Invalid number! Try again or /cancel:"); return PHONE
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}"); return ConversationHandler.END

async def add_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    code   = update.message.text.strip().replace(" ", "").replace("-", "")
    phone  = ctx.user_data.get("phone")
    p_hash = ctx.user_data.get("phone_hash")
    client = ctx.user_data.get("temp_client")
    proxy  = ctx.user_data.get("temp_proxy")
    device = ctx.user_data.get("temp_device")
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=p_hash)
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        if device: account_device_map[phone] = device
        save_accounts(); add_log(f"✅ Added: {phone}")
        await update.message.reply_text(f"✅ <b>Added!</b>\n📱 <code>{phone}</code>\nTotal: <b>{len(accounts)}</b>", parse_mode="HTML")
        return ConversationHandler.END
    except errors.SessionPasswordNeededError:
        await update.message.reply_text("🔒 2FA — enter password:"); return PASSWORD
    except errors.PhoneCodeInvalidError:
        await update.message.reply_text("❌ Wrong code! Try again or /cancel:"); return CODE
    except errors.PhoneCodeExpiredError:
        await update.message.reply_text("❌ Code expired! Restart with /addaccount."); return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}"); return ConversationHandler.END

async def add_password(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    client = ctx.user_data.get("temp_client"); phone = ctx.user_data.get("phone")
    proxy  = ctx.user_data.get("temp_proxy"); device = ctx.user_data.get("temp_device")
    try:
        await client.sign_in(password=update.message.text.strip())
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        if device: account_device_map[phone] = device
        save_accounts(); add_log(f"✅ Added (2FA): {phone}")
        await update.message.reply_text(f"✅ <b>Added (2FA)!</b>\n📱 <code>{phone}</code>", parse_mode="HTML")
        return ConversationHandler.END
    except errors.PasswordHashInvalidError:
        await update.message.reply_text("❌ Wrong password! Try again or /cancel:"); return PASSWORD
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}"); return ConversationHandler.END

async def rmaccount_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("📭 No accounts."); return ConversationHandler.END
    txt = "📱 <b>REMOVE ACCOUNT</b>\n\nSend the exact identifier to remove:\n\n"
    for p in accounts: txt += f"• <code>{p}</code>\n"
    await update.message.reply_text(txt, parse_mode="HTML")
    return RM_PHONE

async def rm_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    if phone not in accounts:
        await update.message.reply_text("❌ Not found! Try again or /cancel:"); return RM_PHONE
    try:
        client = accounts[phone]
        try: await client.log_out()
        except: pass
        try: await client.disconnect()
        except: pass
        del accounts[phone]
        account_proxy_map.pop(phone, None)
        account_device_map.pop(phone, None)
        save_accounts(); add_log(f"🗑 Removed: {phone}")
        await update.message.reply_text(f"✅ Removed <code>{phone}</code>\nRemaining: <b>{len(accounts)}</b>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 🎯 KEYBOARDS
# ══════════════════════════════════════════════════════════════════════
def _build_full_cat_keyboard(prefix: str):
    rows = []
    for key, data in FULL_REPORT_CATEGORIES.items():
        rows.append([InlineKeyboardButton(
            f"{data['emoji']} {data['label']}",
            callback_data=f"{prefix}|{key}")])
    return InlineKeyboardMarkup(rows)

def _build_sub_keyboard(cat_key: str, prefix: str):
    cat = FULL_REPORT_CATEGORIES[cat_key]
    rows = []
    for sub_key, sub_label in cat["subs"]:
        rows.append([InlineKeyboardButton(
            sub_label,
            callback_data=f"{prefix}|{cat_key}|{sub_key}")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"{prefix}|back")])
    return InlineKeyboardMarkup(rows)

# ══════════════════════════════════════════════════════════════════════
# 🎯 /report — FAST MULTI-MSG ROUND-ROBIN FLOW
# ══════════════════════════════════════════════════════════════════════
async def report_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats()
    ctx.user_data["msg_links"] = []   # list of (ident, msg_id, original_link)
    add_log("🎯 /report flow started")
    await update.message.reply_text(
        f"🎯 <b>REPORT FLOW — Step 1</b>\n\n"
        f"✅ Active: <b>{active}/{len(accounts)}</b> accounts\n\n"
        f"📥 Send <b>GROUP / CHANNEL LINK</b>:\n\n"
        f"  • Public  → <code>t.me/groupname</code>\n"
        f"  • Private → <code>t.me/+invitehash</code>\n"
        f"  • Private ch → <code>t.me/c/1234567890</code>\n\n"
        f"/cancel to abort.",
        parse_mode="HTML")
    return GRP_LINK

async def receive_grp_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, ltype, err = parse_group_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return GRP_LINK
    ctx.user_data.update({"grp_ident": ident, "grp_type": ltype, "grp_link": link})
    add_log(f"📥 Group: {link} (type: {ltype})")
    if ltype == "username":
        await update.message.reply_text(
            f"ℹ️ Public group — direct report (no join needed).\n\n"
            f"📥 <b>Step 2</b> — Send first <b>MESSAGE LINK</b>:\n"
            f"  • <code>t.me/groupname/123</code>\n"
            f"  • <code>t.me/c/1234567890/123</code>",
            parse_mode="HTML")
    else:
        await update.message.reply_text(f"🔄 Joining (parallel)...\n{link}", parse_mode="HTML")
        ok, fail = await join_group_all(ident, ltype)
        if ok == 0:
            await update.message.reply_text("❌ No accounts could join! Check link/invite."); return ConversationHandler.END
        await update.message.reply_text(
            f"✅ Join complete!\n✅ <b>{ok}</b> | ❌ <b>{fail}</b>\n\n"
            f"📥 <b>Step 2</b> — Send first <b>MESSAGE LINK</b>:", parse_mode="HTML")
    return MSG_LINK

def _msg_more_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("➕ Aur Bhejo (Add another link)", callback_data="MSG|add"),
        InlineKeyboardButton("⏭️ Skip / Next Step",            callback_data="MSG|skip"),
    ]])

async def receive_msg_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, msg_id, err = parse_message_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return MSG_LINK
    msgs = ctx.user_data.setdefault("msg_links", [])
    msgs.append((ident, msg_id, link))
    add_log(f"📥 Message added (#{len(msgs)}): {link}")
    await update.message.reply_text(
        f"✅ Added message <b>#{len(msgs)}</b> (ID: <code>{msg_id}</code>)\n\n"
        f"📥 Aur message link bhejna hai ya skip karna hai?\n"
        f"<i>(har account saare msgs ek saath report karega)</i>",
        parse_mode="HTML",
        reply_markup=_msg_more_keyboard())
    return MSG_LINK_MORE

async def msg_more_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data.split("|", 1)[1]
    if action == "add":
        try:
            await query.edit_message_text(
                f"📥 Send <b>next MESSAGE LINK</b>:\n"
                f"(currently {len(ctx.user_data.get('msg_links',[]))} added)",
                parse_mode="HTML")
        except Exception:
            pass
        return MSG_LINK
    # skip → next step
    msgs = ctx.user_data.get("msg_links", [])
    if not msgs:
        try:
            await query.edit_message_text("❌ No message links added. Cancelled.")
        except: pass
        return ConversationHandler.END
    try:
        await query.edit_message_text(
            f"✅ <b>{len(msgs)} message(s)</b> queued.\n\n"
            f"📋 <b>Step 3</b> — Select report reason:",
            parse_mode="HTML",
            reply_markup=_build_full_cat_keyboard("CAT"))
    except Exception:
        await update.effective_chat.send_message(
            f"✅ {len(msgs)} message(s) queued.\n📋 Step 3 — Select reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
    return REASON_CAT

async def category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2: return REASON_CAT
    if parts[1] == "back":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    cat_key = parts[1]
    if cat_key not in FULL_REPORT_CATEGORIES:
        return REASON_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data.update({"cat_key": cat_key, "cat_label": cat["label"], "reason_api": cat["api"]})

    if not cat["subs"]:
        ctx.user_data.update({"sub_key": "N/A", "sub_label": "N/A"})
        if cat_key != "other":
            ctx.user_data["custom_msg"] = ""
            await query.edit_message_text(
                f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
                f"🔢 <b>Step 5</b> — Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
                parse_mode="HTML")
            return COUNT
        await query.edit_message_text(
            f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
            f"📝 <b>Step 4</b> — Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return CUSTOM_MSG

    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
        f"📋 <b>Step 4</b> — Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "SUB"),
        parse_mode="HTML")
    return REASON_SUB

async def subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    if len(parts) < 3: return REASON_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return REASON_SUB
    sub_label = next((lbl for k, lbl in cat["subs"] if k == sub_key), sub_key)
    ctx.user_data.update({"sub_key": sub_key, "sub_label": sub_label})
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b> → {sub_label}\n\n"
        f"📝 <b>Step 5</b> — Optional message or send <code>skip</code>:",
        parse_mode="HTML")
    return CUSTOM_MSG

async def receive_custom_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip": text = ""
    ctx.user_data["custom_msg"] = text
    add_log(f"📥 Custom msg: {(text[:40] or '(pool)')}")
    await update.message.reply_text(
        f"✅ Saved!\n\n🔢 <b>Step 6</b> — Reports per account?\n\n"
        f"💡 1–2 = ✅ Safe | 3–10 = ⚠️ Moderate | 10+ = 🚨 Aggressive\n\n"
        f"Enter 1–{MAX_REPORTS_PER_ACCOUNT}:", parse_mode="HTML")
    return COUNT

async def report_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1-{MAX_REPORTS_PER_ACCOUNT}!"); return COUNT
    except ValueError:
        await update.message.reply_text("❌ Enter a number!"); return COUNT

    msg_links: List[Tuple[str, int, str]] = ctx.user_data.get("msg_links", [])
    grp_ident   = ctx.user_data.get("grp_ident")
    grp_type    = ctx.user_data.get("grp_type")
    reason_api  = ctx.user_data.get("reason_api")
    cat_lbl     = ctx.user_data.get("cat_label", "N/A")
    sub_lbl     = ctx.user_data.get("sub_label", "N/A")
    custom_msg  = ctx.user_data.get("custom_msg", "")

    if not msg_links:
        await update.message.reply_text("❌ No messages queued."); return ConversationHandler.END

    # Build authorized account list
    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total_msgs_per_round = len(msg_links)
    total_planned = len(auth_pairs) * count * total_msgs_per_round
    report_stats["total"] = total_planned
    report_stats["start_time"] = datetime.now()

    join_note = f"already joined ({grp_type})" if grp_type != "username" else "public — no join"

    await update.message.reply_text(
        f"🚀 <b>REPORTING STARTED</b> — ⚡ FAST MODE\n\n"
        f"📊 Total fires: <b>{total_planned}</b>\n"
        f"📱 Accounts: <b>{len(auth_pairs)}</b>\n"
        f"💬 Msgs per round: <b>{total_msgs_per_round}</b>\n"
        f"🔁 Rounds: <b>{count}</b>\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
        f"🔁 <i>Pattern: acc1→[all msgs] → acc2→[all msgs] → ... × {count} rounds</i>\n"
        f"🌐 {join_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━", parse_mode="HTML")

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0
    # batch progress reporting to avoid spam
    batch_lines: List[str] = []

    async def _flush_batch():
        if batch_lines:
            text = "\n".join(batch_lines[-15:])
            try:
                await update.message.reply_text(text, parse_mode="HTML")
            except Exception:
                pass
            batch_lines.clear()

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            # 🔥 FIRE ALL MSGS FOR THIS ACCOUNT IN PARALLEL → super fast
            async def _fire_one(ident, msg_id, link):
                return await send_report(phone, ident, msg_id, reason_api, custom_msg,
                                         grp_type, sub_lbl)
            tasks = [_fire_one(i, m, l) for (i, m, l) in msg_links]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (ident, msg_id, link), res in zip(msg_links, results):
                shot_num += 1
                if isinstance(res, Exception):
                    ok, status = False, f"Exception: {type(res).__name__}"
                else:
                    ok, status = res
                if ok:
                    total_ok += 1; per_acc_ok[phone] += 1; update_stats(True)
                    log_report_file(phone, msg_id, f"{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                    batch_lines.append(
                        f"✅ {shot_num}/{total_planned} | R{r+1} | 📱 ...{phone[-4:]} | msg <code>{msg_id}</code> → {status}")
                else:
                    total_fail += 1; per_acc_fail[phone] += 1; update_stats(False)
                    log_report_file(phone, msg_id, f"{cat_lbl}/{sub_lbl}", "FAILED", status)
                    batch_lines.append(
                        f"❌ {shot_num}/{total_planned} | R{r+1} | 📱 ...{phone[-4:]} | msg <code>{msg_id}</code> → {status}")
                    if "FloodWait" in status:
                        try:
                            wait = int(status.split()[1].replace("s",""))
                            await update.message.reply_text(f"⏳ FloodWait {wait}s — waiting...")
                            await asyncio.sleep(min(wait + 1, 180))
                        except: await asyncio.sleep(30)

            # flush every account
            await _flush_batch()
            # 🔥 fast account-switch jitter (was 5-12s, now 0.3-1s)
            if not (acc_idx == len(auth_pairs)-1 and r == count-1):
                await asyncio.sleep(random.uniform(0.3, 1.0))
        # tiny round break
        if r < count - 1:
            await asyncio.sleep(random.uniform(0.5, 1.5))

    await _flush_batch()

    elapsed = (datetime.now() - report_stats["start_time"]).seconds
    rate = (total_ok / total_planned * 100) if total_planned > 0 else 0
    add_log(f"🎉 Done: {total_ok}/{total_planned} ({rate:.1f}%)")

    breakdown = "\n".join(
        f"  📱 ...{p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)

    msg_summary = "\n".join(f"  • <code>{ident}/{mid}</code>" for ident, mid, _ in msg_links)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Gmail Blast (next)", callback_data="GMAIL_START")],
        [InlineKeyboardButton("🏠 Done",               callback_data="GMAIL_SKIP")]])
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>REPORTING COMPLETE</b>\n\n"
        f"✅ Success: <b>{total_ok}</b>\n"
        f"❌ Failed: <b>{total_fail}</b>\n"
        f"📈 Rate: <b>{rate:.1f}%</b>\n"
        f"⏱ Time: <b>{elapsed//60}m {elapsed%60}s</b>\n\n"
        f"<b>Per-account:</b>\n{breakdown}\n\n"
        f"<b>Reported messages ({len(msg_links)}):</b>\n{msg_summary}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n\n"
        f"📧 Want to also blast Gmail?",
        reply_markup=keyboard, parse_mode="HTML")
    return MAIL_SUBJECT

# ══════════════════════════════════════════════════════════════════════
# 👥 /groupreport — 3-DOT MENU STYLE with MSG SELECTION
# ══════════════════════════════════════════════════════════════════════
async def groupreport_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats()
    ctx.user_data["gr_msg_links"] = []
    add_log("👥 /groupreport flow started")
    await update.message.reply_text(
        f"👥 <b>GROUP REPORT — 3-Dot Menu Style</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Active: <b>{active}/{len(accounts)}</b> accounts\n\n"
        f"<i>Bot will simulate: tap msg → 3-dot → Report → category → sub → optional reason → submit.</i>\n"
        f"<i>The exact message you give a link to is what gets reported in-group.</i>\n\n"
        f"📥 <b>Step 1</b> — Send <b>GROUP / CHANNEL LINK</b>:\n"
        f"/cancel to abort.",
        parse_mode="HTML")
    return GR_GRP_LINK

async def gr_receive_grp(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, ltype, err = parse_group_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return GR_GRP_LINK
    ctx.user_data.update({"gr_grp_ident": ident, "gr_grp_type": ltype, "gr_grp_link": link})
    add_log(f"📥 GR group: {link} ({ltype})")
    if ltype == "username":
        await update.message.reply_text(
            f"ℹ️ Public group — no join needed.\n\n"
            f"📥 <b>Step 2</b> — Send first <b>MESSAGE LINK</b>:",
            parse_mode="HTML")
    else:
        await update.message.reply_text(f"🔄 Joining (parallel)...\n{link}", parse_mode="HTML")
        ok, fail = await join_group_all(ident, ltype)
        if ok == 0:
            await update.message.reply_text("❌ No accounts could join."); return ConversationHandler.END
        await update.message.reply_text(
            f"✅ Join done — ✅ <b>{ok}</b> | ❌ <b>{fail}</b>\n\n"
            f"📥 <b>Step 2</b> — Send first <b>MESSAGE LINK</b>:", parse_mode="HTML")
    return GR_MSG_LINK

def _gr_msg_more_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("➕ Aur Bhejo", callback_data="GRMSG|add"),
        InlineKeyboardButton("⏭️ Skip / Next", callback_data="GRMSG|skip"),
    ]])

async def gr_receive_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, msg_id, err = parse_message_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return GR_MSG_LINK
    msgs = ctx.user_data.setdefault("gr_msg_links", [])
    msgs.append((ident, msg_id, link))
    add_log(f"📥 GR msg added (#{len(msgs)}): {link}")
    await update.message.reply_text(
        f"✅ Added msg <b>#{len(msgs)}</b> (ID: <code>{msg_id}</code>)\n\n"
        f"📥 Aur message link bhejna hai ya skip?",
        parse_mode="HTML",
        reply_markup=_gr_msg_more_keyboard())
    return GR_MSG_LINK_MORE

async def gr_msg_more_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data.split("|", 1)[1]
    if action == "add":
        try:
            await query.edit_message_text(
                f"📥 Send <b>next MESSAGE LINK</b>:\n"
                f"(currently {len(ctx.user_data.get('gr_msg_links',[]))} added)",
                parse_mode="HTML")
        except: pass
        return GR_MSG_LINK
    msgs = ctx.user_data.get("gr_msg_links", [])
    if not msgs:
        try: await query.edit_message_text("❌ No msg links added. Cancelled.")
        except: pass
        return ConversationHandler.END
    try:
        await query.edit_message_text(
            f"✅ <b>{len(msgs)} message(s)</b> queued for group-report.\n\n"
            f"📋 <b>Step 3</b> — Select category (3-dot menu reason):",
            parse_mode="HTML",
            reply_markup=_build_full_cat_keyboard("GRCAT"))
    except Exception:
        await update.effective_chat.send_message(
            "Select category:", reply_markup=_build_full_cat_keyboard("GRCAT"))
    return GR_CAT

async def gr_category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2: return GR_CAT
    if parts[1] == "back":
        await query.edit_message_text(
            "📋 Select category:",
            reply_markup=_build_full_cat_keyboard("GRCAT"))
        return GR_CAT
    cat_key = parts[1]
    if cat_key not in FULL_REPORT_CATEGORIES: return GR_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data.update({"gr_cat_key": cat_key, "gr_cat_label": cat["label"], "gr_reason_api": cat["api"]})
    if not cat["subs"]:
        ctx.user_data.update({"gr_sub_key": "N/A", "gr_sub_label": "N/A"})
        await query.edit_message_text(
            f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
            f"📝 <b>Step 5</b> — Paste optional reason (or send <code>skip</code>):",
            parse_mode="HTML")
        return GR_CUSTOM_MSG
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
        f"📋 <b>Step 4</b> — Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "GRSUB"),
        parse_mode="HTML")
    return GR_SUB

async def gr_sub_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text(
            "📋 Select category:",
            reply_markup=_build_full_cat_keyboard("GRCAT"))
        return GR_CAT
    if len(parts) < 3: return GR_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return GR_SUB
    sub_label = next((lbl for k, lbl in cat["subs"] if k == sub_key), sub_key)
    ctx.user_data.update({"gr_sub_key": sub_key, "gr_sub_label": sub_label})
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b> → {sub_label}\n\n"
        f"📝 <b>Step 5</b> — Paste optional reason (or send <code>skip</code>):",
        parse_mode="HTML")
    return GR_CUSTOM_MSG

async def gr_receive_custom(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip": text = ""
    ctx.user_data["gr_custom_msg"] = text
    await update.message.reply_text(
        f"✅ Saved!\n\n🔢 <b>Step 6</b> — Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
        parse_mode="HTML")
    return GR_COUNT

async def gr_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1-{MAX_REPORTS_PER_ACCOUNT}!"); return GR_COUNT
    except ValueError:
        await update.message.reply_text("❌ Enter a number!"); return GR_COUNT

    msg_links: List[Tuple[str, int, str]] = ctx.user_data.get("gr_msg_links", [])
    grp_ident   = ctx.user_data.get("gr_grp_ident")
    grp_type    = ctx.user_data.get("gr_grp_type")
    reason_api  = ctx.user_data.get("gr_reason_api")
    cat_lbl     = ctx.user_data.get("gr_cat_label", "N/A")
    sub_lbl     = ctx.user_data.get("gr_sub_label", "N/A")
    custom_msg  = ctx.user_data.get("gr_custom_msg", "")

    if not msg_links:
        await update.message.reply_text("❌ No messages queued."); return ConversationHandler.END

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total_planned = len(auth_pairs) * count * len(msg_links)
    report_stats["total"] = total_planned
    report_stats["start_time"] = datetime.now()

    await update.message.reply_text(
        f"🚀 <b>GROUP REPORT STARTED</b> (3-Dot Style)\n\n"
        f"📊 Total fires: <b>{total_planned}</b>\n"
        f"📱 Accounts: <b>{len(auth_pairs)}</b> | Msgs: <b>{len(msg_links)}</b> | Rounds: <b>{count}</b>\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
        f"🔁 <i>Pattern: acc1→all msgs → acc2→all msgs → ...</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0
    batch_lines: List[str] = []

    async def _flush():
        if batch_lines:
            try:
                await update.message.reply_text("\n".join(batch_lines[-15:]), parse_mode="HTML")
            except: pass
            batch_lines.clear()

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            async def _fire(ident, msg_id):
                return await send_group_report(phone, ident, msg_id, reason_api, custom_msg,
                                               grp_type, cat_lbl, sub_lbl)
            tasks = [_fire(i, m) for (i, m, _l) in msg_links]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (ident, msg_id, link), res in zip(msg_links, results):
                shot_num += 1
                if isinstance(res, Exception):
                    ok, status = False, f"Exception: {type(res).__name__}"
                else:
                    ok, status = res
                if ok:
                    total_ok += 1; per_acc_ok[phone] += 1; update_stats(True)
                    log_report_file(phone, msg_id, f"GR-{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                    batch_lines.append(
                        f"✅ GR {shot_num}/{total_planned} | R{r+1} | 📱 ...{phone[-4:]} | msg <code>{msg_id}</code> → {status}")
                else:
                    total_fail += 1; per_acc_fail[phone] += 1; update_stats(False)
                    log_report_file(phone, msg_id, f"GR-{cat_lbl}/{sub_lbl}", "FAILED", status)
                    batch_lines.append(
                        f"❌ GR {shot_num}/{total_planned} | R{r+1} | 📱 ...{phone[-4:]} | msg <code>{msg_id}</code> → {status}")
                    if "FloodWait" in status:
                        try:
                            wait = int(status.split()[1].replace("s",""))
                            await update.message.reply_text(f"⏳ FloodWait {wait}s — waiting...")
                            await asyncio.sleep(min(wait + 1, 180))
                        except: await asyncio.sleep(30)

            await _flush()
            if not (acc_idx == len(auth_pairs)-1 and r == count-1):
                await asyncio.sleep(random.uniform(0.3, 1.0))
        if r < count - 1:
            await asyncio.sleep(random.uniform(0.5, 1.5))

    await _flush()

    elapsed = (datetime.now() - report_stats["start_time"]).seconds
    rate = (total_ok / total_planned * 100) if total_planned > 0 else 0
    add_log(f"🎉 GroupReport done: {total_ok}/{total_planned} ({rate:.1f}%)")

    breakdown = "\n".join(
        f"  📱 ...{p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    msg_summary = "\n".join(f"  • <code>{ident}/{mid}</code>" for ident, mid, _ in msg_links)

    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>GROUP REPORT COMPLETE</b>\n\n"
        f"✅ Success: <b>{total_ok}</b>\n"
        f"❌ Failed: <b>{total_fail}</b>\n"
        f"📈 Rate: <b>{rate:.1f}%</b>\n"
        f"⏱ Time: <b>{elapsed//60}m {elapsed%60}s</b>\n\n"
        f"<b>Per-account:</b>\n{breakdown}\n\n"
        f"<b>Reported messages ({len(msg_links)}):</b>\n{msg_summary}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}",
        parse_mode="HTML")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 📸 PFP REPORT FLOW
# ══════════════════════════════════════════════════════════════════════
def _build_pfp_reason_keyboard():
    rows = []; row = []
    for key, (label, _) in PFP_REPORT_REASONS.items():
        row.append(InlineKeyboardButton(label, callback_data=f"PFP|{key}"))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

async def accountreport_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear()
    await update.message.reply_text(
        f"📸 <b>NUCLEAR PFP REPORT</b>\n━━━━━━━━━━━━━━━━\n\n"
        f"✅ Active: <b>{active}/{len(accounts)}</b>\n"
        f"💀 Uses 6 methods + fallbacks\n\n"
        f"👤 Enter <b>@username</b> or <b>user ID</b>:\n/cancel to abort.",
        parse_mode="HTML")
    return AR_USER

async def ar_receive_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    add_log(f"📸 PFP target: {raw}")
    wait_msg = await update.message.reply_text("🔍 Resolving user...")
    client = await get_any_active_client()
    if not client:
        await wait_msg.edit_text("❌ No active accounts."); return ConversationHandler.END
    try:
        identifier = raw.lstrip("@")
        entity     = await client.get_entity(int(identifier) if identifier.isdigit() else identifier)
    except errors.UsernameNotOccupiedError:
        await wait_msg.edit_text("❌ Username not found. Try again:"); return AR_USER
    except ValueError:
        await wait_msg.edit_text("❌ Invalid format. Try @username or numeric ID:"); return AR_USER
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)[:60]}\nTry again:"); return AR_USER

    uid   = entity.id
    fname = getattr(entity, "first_name", "") or ""
    lname = getattr(entity, "last_name", "")  or ""
    uname = getattr(entity, "username", "")   or ""
    dname = f"{fname} {lname}".strip() or uname or str(uid)
    try:
        photos = await client.get_profile_photos(entity)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Could not fetch photos: {str(e)[:60]}"); return ConversationHandler.END

    ctx.user_data.update({
        "ar_uid": uid, "ar_name": dname, "ar_uname": uname,
        "ar_entity_id": raw,
    })
    await wait_msg.edit_text(
        f"✅ Found!\n👤 <b>{dname}</b>" + (f" (@{uname})" if uname else "") +
        f"\n🆔 <code>{uid}</code>\n📸 Photos: <b>{len(photos)}</b>\n\n📋 Select reason:",
        reply_markup=_build_pfp_reason_keyboard(), parse_mode="HTML")
    return AR_REASON

async def ar_reason_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, reason_key = query.data.split("|", 1)
    label, api    = PFP_REPORT_REASONS[reason_key]
    ctx.user_data.update({"ar_reason_key": reason_key, "ar_reason_label": label, "ar_reason_api": api})
    dname = ctx.user_data.get("ar_name", "Target")
    if reason_key == "pfp_other":
        await query.edit_message_text(
            f"✅ {label}\n\n✍️ Custom message (or /skip):", parse_mode="HTML"); return AR_OTHER_MSG
    ctx.user_data["ar_custom_msg"] = ""
    await query.edit_message_text(
        f"✅ {label}\n👤 <b>{dname}</b>\n\n🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):", parse_mode="HTML")
    return AR_COUNT

async def ar_other_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() in ("skip", "/skip"): text = ""
    ctx.user_data["ar_custom_msg"] = text
    await update.message.reply_text(
        f"✅ Saved!\n🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):", parse_mode="HTML")
    return AR_COUNT

async def ar_skip_other_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["ar_custom_msg"] = ""
    await update.message.reply_text(
        f"⏩ Skipped.\n🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):", parse_mode="HTML")
    return AR_COUNT

async def ar_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1-{MAX_REPORTS_PER_ACCOUNT}!"); return AR_COUNT
    except ValueError:
        await update.message.reply_text("❌ Enter a number!"); return AR_COUNT

    target_raw    = ctx.user_data["ar_entity_id"]
    target_name   = ctx.user_data.get("ar_name", "Target")
    reason_api    = ctx.user_data["ar_reason_api"]
    reason_label  = ctx.user_data["ar_reason_label"]
    custom_msg    = ctx.user_data.get("ar_custom_msg", "")

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total_reports = len(auth_pairs) * count
    await update.message.reply_text(
        f"🚀 <b>NUCLEAR PFP REPORT</b>\n👤 <b>{target_name}</b>\n⚠️ {reason_label}\n"
        f"📊 <b>{total_reports}</b> total ({len(auth_pairs)} × {count})\n"
        f"🔁 Round-robin\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    resolved: Dict[str, Tuple[object, list]] = {}
    for phone, client in auth_pairs:
        try:
            identifier = target_raw.lstrip("@")
            ent = await client.get_entity(int(identifier) if identifier.isdigit() else identifier)
            try:
                ph = await client.get_profile_photos(ent)
            except Exception:
                ph = []
            resolved[phone] = (ent, ph)
        except Exception as e:
            await update.message.reply_text(f"❌ ...{phone[-4:]}: Resolve — {str(e)[:40]}", parse_mode="HTML")
            resolved[phone] = (None, [])

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0
    batch_lines: List[str] = []

    async def _flush():
        if batch_lines:
            try:
                await update.message.reply_text("\n".join(batch_lines[-15:]), parse_mode="HTML")
            except: pass
            batch_lines.clear()

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            shot_num += 1
            ent, photos = resolved.get(phone, (None, []))
            if ent is None:
                total_fail += 1; per_acc_fail[phone] += 1
                batch_lines.append(f"❌ PFP {shot_num}/{total_reports} | R{r+1} | 📱 ...{phone[-4:]} → resolve failed")
                continue
            ok, status = await report_profile_photo_nuclear(phone, ent, photos, reason_api, custom_msg)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "SUCCESS", status)
                batch_lines.append(f"✅ PFP {shot_num}/{total_reports} | R{r+1} | 📱 ...{phone[-4:]} → {status}")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "FAILED", status)
                batch_lines.append(f"❌ PFP {shot_num}/{total_reports} | R{r+1} | 📱 ...{phone[-4:]} → {status}")
                if "FloodWait" in status:
                    try:
                        wait = int(status.split()[1].replace("s",""))
                        await asyncio.sleep(min(wait + 1, 180))
                    except: await asyncio.sleep(30)
            if not (acc_idx == len(auth_pairs)-1 and r == count-1):
                await asyncio.sleep(random.uniform(0.3, 1.0))
        await _flush()
        if r < count - 1: await asyncio.sleep(random.uniform(0.5, 1.5))

    await _flush()
    rate = (total_ok / total_reports * 100) if total_reports > 0 else 0
    add_log(f"🎉 PFP done: {total_ok}/{total_reports} ({rate:.1f}%)")
    breakdown = "\n".join(
        f"  📱 ...{p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>PFP COMPLETE</b>\n\n"
        f"👤 <b>{target_name}</b>\n⚠️ {reason_label}\n"
        f"✅ <b>{total_ok}</b> | ❌ <b>{total_fail}</b> | 📈 <b>{rate:.1f}%</b>\n\n"
        f"<b>Per-account:</b>\n{breakdown}",
        parse_mode="HTML")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 🤖 BOT REPORT FLOW
# ══════════════════════════════════════════════════════════════════════
async def botreport_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear()
    await update.message.reply_text(
        f"🤖 <b>BOT REPORT</b>\n━━━━━━━━━━━━━━━━\n\n"
        f"✅ Active: <b>{active}/{len(accounts)}</b>\n\n"
        f"🤖 Enter <b>@bot_username</b>:\n/cancel to abort.",
        parse_mode="HTML")
    return BR_USER

async def br_receive_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    add_log(f"🤖 Bot report target: {raw}")
    wait_msg = await update.message.reply_text("🔍 Resolving bot...")
    client = await get_any_active_client()
    if not client:
        await wait_msg.edit_text("❌ No active accounts."); return ConversationHandler.END
    try:
        identifier = raw.lstrip("@")
        entity     = await client.get_entity(identifier)
    except errors.UsernameNotOccupiedError:
        await wait_msg.edit_text("❌ Bot username not found. Try again:"); return BR_USER
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)[:60]}\nTry again:"); return BR_USER

    is_bot = getattr(entity, "bot", False)
    if not is_bot:
        await wait_msg.edit_text("⚠️ This is not a bot account. Use /accountreport for users.")
        return ConversationHandler.END

    uid   = entity.id
    fname = getattr(entity, "first_name", "") or ""
    uname = getattr(entity, "username", "")   or ""
    dname = fname or uname or str(uid)
    ctx.user_data.update({"br_uid": uid, "br_name": dname, "br_uname": uname, "br_entity_id": raw})
    await wait_msg.edit_text(
        f"✅ Found bot!\n🤖 <b>{dname}</b>" + (f" (@{uname})" if uname else "") +
        f"\n🆔 <code>{uid}</code>\n\n📋 Select reason:",
        reply_markup=_build_full_cat_keyboard("BCAT"), parse_mode="HTML")
    return BR_CAT

async def br_category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2: return BR_CAT
    if parts[1] == "back":
        await query.edit_message_text("📋 Select reason:", reply_markup=_build_full_cat_keyboard("BCAT")); return BR_CAT
    cat_key = parts[1]
    if cat_key not in FULL_REPORT_CATEGORIES: return BR_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data.update({"br_cat_key": cat_key, "br_cat_label": cat["label"], "br_reason_api": cat["api"]})
    if not cat["subs"]:
        ctx.user_data.update({"br_sub_key": "N/A", "br_sub_label": "N/A"})
        await query.edit_message_text(
            f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n📝 Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return BR_MSG
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n📋 Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "BSUB"),
        parse_mode="HTML")
    return BR_SUB

async def br_subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text("📋 Select reason:", reply_markup=_build_full_cat_keyboard("BCAT")); return BR_CAT
    if len(parts) < 3: return BR_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return BR_SUB
    sub_label = next((lbl for k, lbl in cat["subs"] if k == sub_key), sub_key)
    ctx.user_data.update({"br_sub_key": sub_key, "br_sub_label": sub_label})
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b> → {sub_label}\n\n📝 Optional message or send <code>skip</code>:",
        parse_mode="HTML")
    return BR_MSG

async def br_receive_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() in ("skip", "/skip"): text = ""
    ctx.user_data["br_custom_msg"] = text
    await update.message.reply_text(
        f"✅ Saved!\n🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):", parse_mode="HTML")
    return BR_COUNT

async def br_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1-{MAX_REPORTS_PER_ACCOUNT}!"); return BR_COUNT
    except ValueError:
        await update.message.reply_text("❌ Enter a number!"); return BR_COUNT

    target_raw  = ctx.user_data["br_entity_id"]
    target_name = ctx.user_data.get("br_name", "Target")
    reason_api  = ctx.user_data["br_reason_api"]
    cat_label   = ctx.user_data.get("br_cat_label", "N/A")
    sub_label   = ctx.user_data.get("br_sub_label", "N/A")
    custom_msg  = ctx.user_data.get("br_custom_msg", "")

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total = len(auth_pairs) * count
    await update.message.reply_text(
        f"🚀 <b>BOT REPORT STARTING</b>\n🤖 <b>{target_name}</b>\n"
        f"⚠️ {cat_label} → {sub_label}\n"
        f"📊 <b>{total}</b> total ({len(auth_pairs)} × {count})\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    resolved: Dict[str, object] = {}
    for phone, client in auth_pairs:
        try:
            identifier = target_raw.lstrip("@")
            ent = await client.get_entity(identifier)
            resolved[phone] = ent
        except Exception as e:
            await update.message.reply_text(f"❌ ...{phone[-4:]}: Resolve — {str(e)[:40]}", parse_mode="HTML")
            resolved[phone] = None

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0
    batch_lines: List[str] = []

    async def _flush():
        if batch_lines:
            try:
                await update.message.reply_text("\n".join(batch_lines[-15:]), parse_mode="HTML")
            except: pass
            batch_lines.clear()

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            shot_num += 1
            bot_entity = resolved.get(phone)
            if bot_entity is None:
                total_fail += 1; per_acc_fail[phone] += 1
                batch_lines.append(f"❌ BOT {shot_num}/{total} | R{r+1} | 📱 ...{phone[-4:]} → resolve failed")
                continue
            ok, status = await _report_bot_methods(phone, bot_entity, reason_api, custom_msg, sub_label)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "SUCCESS", status)
                batch_lines.append(f"✅ BOT {shot_num}/{total} | R{r+1} | 📱 ...{phone[-4:]} → {status}")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "FAILED", status)
                batch_lines.append(f"❌ BOT {shot_num}/{total} | R{r+1} | 📱 ...{phone[-4:]} → {status}")
                if "FloodWait" in status:
                    try:
                        wait = int(status.split()[1].replace("s",""))
                        await asyncio.sleep(min(wait + 1, 180))
                    except: await asyncio.sleep(30)
            if not (acc_idx == len(auth_pairs)-1 and r == count-1):
                await asyncio.sleep(random.uniform(0.3, 1.0))
        await _flush()
        if r < count - 1: await asyncio.sleep(random.uniform(0.5, 1.5))

    await _flush()
    rate = (total_ok / total * 100) if total > 0 else 0
    add_log(f"🎉 BOT report done: {total_ok}/{total} ({rate:.1f}%)")
    breakdown = "\n".join(
        f"  📱 ...{p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>BOT REPORT COMPLETE</b>\n\n"
        f"🤖 <b>{target_name}</b>\n⚠️ {cat_label} → {sub_label}\n"
        f"✅ <b>{total_ok}</b> | ❌ <b>{total_fail}</b> | 📈 <b>{rate:.1f}%</b>\n\n"
        f"<b>Per-account:</b>\n{breakdown}",
        parse_mode="HTML")
    return ConversationHandler.END

async def _report_bot_methods(phone, bot_entity, reason_api, custom_msg, sub_label="") -> Tuple[bool, str]:
    client = await ensure_connected(phone)
    if not client:
        return (False, "Account disconnected")
    proxy = account_proxy_map.get(phone)
    methods_tried = []

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        r = await client(functions.account.ReportPeerRequest(
            peer=bot_entity, reason=reason_api,
            message=craft_report_message(custom_msg, sub_label)))
        if r:
            mark_proxy_result(proxy, True)
            return (True, "M1:ReportPeer")
        methods_tried.append("M1")
    except errors.FloodWaitError as e:
        return (False, f"FloodWait {e.seconds}s")
    except Exception as e:
        methods_tried.append(f"M1-{type(e).__name__}")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            r = await client(functions.messages.ReportSpamRequest(peer=bot_entity))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "M2:ReportSpam")
            methods_tried.append("M2")
    except Exception as e:
        methods_tried.append(f"M2-{type(e).__name__}")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            msgs = await client.get_messages(bot_entity, limit=1)
            if msgs and msgs[0]:
                r = await client(functions.messages.ReportRequest(
                    peer=bot_entity, id=[msgs[0].id], reason=reason_api,
                    message=craft_report_message(custom_msg, sub_label)))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "M3:report-bot-msg")
            methods_tried.append("M3")
    except Exception as e:
        methods_tried.append(f"M3-{type(e).__name__}")

    try:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        client = await ensure_connected(phone)
        if client:
            photos = await client.get_profile_photos(bot_entity)
            if photos:
                ph = photos[0]
                ip = tl_types.InputPhoto(id=ph.id, access_hash=ph.access_hash, file_reference=ph.file_reference)
                r = await client(functions.account.ReportProfilePhotoRequest(
                    peer=bot_entity, photo_id=ip,
                    reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "M4:bot-PFP")
            methods_tried.append("M4")
    except Exception as e:
        methods_tried.append(f"M4-{type(e).__name__}")

    mark_proxy_result(proxy, False)
    return (False, f"All failed ({','.join(methods_tried)})")

# ══════════════════════════════════════════════════════════════════════
# 📧 GMAIL FLOW
# ══════════════════════════════════════════════════════════════════════
async def gmail_flow_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        if query.data == "GMAIL_SKIP":
            ctx.user_data.clear()
            await query.edit_message_text("✅ Session done! Use /start to open menu.")
            return ConversationHandler.END
        await query.edit_message_text(
            "📧 <b>Gmail BLAST — Step 1/5</b>\n\n"
            "All Gmail accounts will fire simultaneously per round.\n\n"
            "✏️ Enter <b>Email Subject</b>:", parse_mode="HTML")
    else:
        ctx.user_data.clear()
        await update.message.reply_text(
            "📧 <b>Gmail BLAST Mode — Step 1/5</b>\n\n"
            "🔥 All accounts fire at once + repeat N times!\n\n"
            "✏️ Enter <b>Email Subject</b>:", parse_mode="HTML")
    return MAIL_SUBJECT

async def receive_mail_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["mail_subject"] = update.message.text.strip()
    await update.message.reply_text("📝 <b>Step 2/5</b> — Enter <b>Email Body</b>:", parse_mode="HTML")
    return MAIL_BODY

async def receive_mail_body(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["mail_body"] = update.message.text.strip()
    await update.message.reply_text(
        "📎 <b>Step 3/5</b> (Optional)\n\n📸 Send evidence photo OR /skip", parse_mode="HTML")
    return MAIL_EVIDENCE

async def receive_mail_evidence(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo[-1]
    file  = await photo.get_file()
    data  = await file.download_as_bytearray()
    ctx.user_data["mail_evidence"] = bytes(data)
    ctx.user_data["mail_ev_name"]  = "evidence.jpg"
    await update.message.reply_text("✅ Evidence saved!\n\n📧 <b>Step 4/5</b> — Recipient Email:", parse_mode="HTML")
    return MAIL_RECIPIENT

async def skip_mail_evidence(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["mail_evidence"] = None
    await update.message.reply_text("⏩ Skipped.\n\n📧 <b>Step 4/5</b> — Recipient Email:", parse_mode="HTML")
    return MAIL_RECIPIENT

async def receive_mail_recipient(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    recipient = update.message.text.strip()
    if "@" not in recipient or "." not in recipient:
        await update.message.reply_text("⚠️ Invalid email! Try again:"); return MAIL_RECIPIENT
    ctx.user_data["mail_recipient"] = recipient
    await update.message.reply_text(
        f"✅ Recipient: <code>{recipient}</code>\n\n"
        f"🔢 <b>Step 5/5</b> — How many times to blast?\n"
        f"(All {len(GMAIL_ACCOUNTS)} accounts fire each round)\n\n"
        f"Enter 1–50:", parse_mode="HTML")
    return MAIL_BLAST_COUNT

async def receive_blast_count(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= 50:
            await update.message.reply_text("⚠️ Enter 1-50!"); return MAIL_BLAST_COUNT
    except ValueError:
        await update.message.reply_text("❌ Enter a number!"); return MAIL_BLAST_COUNT

    ctx.user_data["mail_blast_count"] = count
    recipient = ctx.user_data["mail_recipient"]
    await update.message.reply_text(
        f"🚀 <b>BLAST STARTING</b>\n\n"
        f"📬 Recipient: <code>{recipient}</code>\n"
        f"🔁 Rounds: <b>{count}</b>\n"
        f"📧 Accounts/round: <b>{len(GMAIL_ACCOUNTS)}</b>\n"
        f"📊 Total emails: <b>{count * len(GMAIL_ACCOUNTS)}</b>\n\n"
        f"⏳ Firing now...", parse_mode="HTML")
    total_ok, total_fail, details = await do_gmail_blast_n_times(ctx, count, update_msg=update.message)
    summary = (
        f"📬 <b>BLAST COMPLETE</b> → <code>{recipient}</code>\n\n"
        f"✅ Sent: <b>{total_ok}</b>\n"
        f"❌ Failed: <b>{total_fail}</b>\n"
        f"📊 Total attempts: <b>{count * len(GMAIL_ACCOUNTS)}</b>\n")
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Blast Again", callback_data="RESEND"),
        InlineKeyboardButton("✅ Done",         callback_data="DONE")]])
    if len(details) > 3500: details = details[:3500] + "\n...(truncated)"
    await update.message.reply_text(summary + "\n" + details, reply_markup=keyboard, parse_mode="HTML")
    return MAIL_RESEND

async def gmail_resend_or_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "DONE":
        ctx.user_data.clear()
        await query.edit_message_text("✅ All done! Use /start to open menu.")
        return ConversationHandler.END
    recipient = ctx.user_data.get("mail_recipient","N/A")
    count     = ctx.user_data.get("mail_blast_count", 1)
    await query.edit_message_text(
        f"🔄 <b>RE-BLAST</b> → <code>{recipient}</code> × {count} rounds\n⏳ Firing...", parse_mode="HTML")
    total_ok, total_fail, details = await do_gmail_blast_n_times(ctx, count)
    summary = (
        f"📬 <b>RE-BLAST COMPLETE</b> → <code>{recipient}</code>\n\n"
        f"✅ <b>{total_ok}</b> | ❌ <b>{total_fail}</b> | 📊 <b>{count*len(GMAIL_ACCOUNTS)}</b>\n")
    if len(details) > 3500: details = details[:3500] + "\n...(truncated)"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Blast Again", callback_data="RESEND"),
        InlineKeyboardButton("✅ Done",         callback_data="DONE")]])
    await query.edit_message_text(summary + "\n" + details, reply_markup=keyboard, parse_mode="HTML")
    return MAIL_RESEND

# ══════════════════════════════════════════════════════════════════════
# 🔄 POST INIT / SHUTDOWN
# ══════════════════════════════════════════════════════════════════════
async def post_init(application):
    load_sudo()
    load_proxy_health()
    load_accounts()
    # parallel connect on startup
    async def _c(p):
        try: await ensure_connected(p)
        except: pass
    await asyncio.gather(*[_c(p) for p in list(accounts.keys())], return_exceptions=True)
    add_log(f"✅ Startup complete — {len(accounts)} accounts loaded")

async def post_shutdown(application):
    add_log("🛑 Shutting down — saving state...")
    save_accounts()
    save_sudo()
    save_proxy_health()
    for phone, client in list(accounts.items()):
        try:
            if client.is_connected():
                await client.disconnect()
        except: pass

# ══════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    print_banner()
    app = Application.builder().token(BOT_TOKEN).build()
    app.post_init     = post_init
    app.post_shutdown = post_shutdown

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("addaccount", addaccount_cmd)],
        states={
            PHONE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
            CODE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_code)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False)

    rm_conv = ConversationHandler(
        entry_points=[CommandHandler("rmaccount", rmaccount_cmd)],
        states={RM_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, rm_phone)]},
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False)

    ar_conv = ConversationHandler(
        entry_points=[CommandHandler("accountreport", accountreport_cmd)],
        states={
            AR_USER:      [MessageHandler(filters.TEXT & ~filters.COMMAND, ar_receive_user)],
            AR_REASON:    [CallbackQueryHandler(ar_reason_selected, pattern="^PFP\\|")],
            AR_OTHER_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ar_other_msg),
                CommandHandler("skip", ar_skip_other_msg)],
            AR_COUNT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ar_execute)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False, allow_reentry=True)

    br_conv = ConversationHandler(
        entry_points=[CommandHandler("botreport", botreport_cmd)],
        states={
            BR_USER:   [MessageHandler(filters.TEXT & ~filters.COMMAND, br_receive_user)],
            BR_CAT:    [CallbackQueryHandler(br_category_selected, pattern="^BCAT\\|")],
            BR_SUB:    [CallbackQueryHandler(br_subcategory_selected, pattern="^BSUB\\|")],
            BR_MSG:    [MessageHandler(filters.TEXT & ~filters.COMMAND, br_receive_msg)],
            BR_COUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, br_execute)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False, allow_reentry=True)

    report_conv = ConversationHandler(
        entry_points=[CommandHandler("report", report_cmd)],
        states={
            GRP_LINK:      [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grp_link)],
            MSG_LINK:      [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_msg_link)],
            MSG_LINK_MORE: [CallbackQueryHandler(msg_more_router, pattern="^MSG\\|")],
            REASON_CAT:    [CallbackQueryHandler(category_selected, pattern="^CAT\\|")],
            REASON_SUB:    [CallbackQueryHandler(subcategory_selected, pattern="^SUB\\|")],
            CUSTOM_MSG:    [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_msg)],
            COUNT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, report_execute)],
            MAIL_SUBJECT: [
                CallbackQueryHandler(gmail_flow_start, pattern="^(GMAIL_START|GMAIL_SKIP)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mail_subject)],
            MAIL_BODY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mail_body)],
            MAIL_EVIDENCE:    [MessageHandler(filters.PHOTO, receive_mail_evidence),
                               CommandHandler("skip", skip_mail_evidence)],
            MAIL_RECIPIENT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mail_recipient)],
            MAIL_BLAST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_blast_count)],
            MAIL_RESEND:      [CallbackQueryHandler(gmail_resend_or_done, pattern="^(RESEND|DONE)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False, allow_reentry=True)

    group_report_conv = ConversationHandler(
        entry_points=[CommandHandler("groupreport", groupreport_cmd)],
        states={
            GR_GRP_LINK:      [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_receive_grp)],
            GR_MSG_LINK:      [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_receive_msg)],
            GR_MSG_LINK_MORE: [CallbackQueryHandler(gr_msg_more_router, pattern="^GRMSG\\|")],
            GR_CAT:           [CallbackQueryHandler(gr_category_selected, pattern="^GRCAT\\|")],
            GR_SUB:           [CallbackQueryHandler(gr_sub_selected, pattern="^GRSUB\\|")],
            GR_CUSTOM_MSG:    [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_receive_custom)],
            GR_COUNT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_execute)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False, allow_reentry=True)

    gmail_conv = ConversationHandler(
        entry_points=[CommandHandler("massgmail", gmail_flow_start)],
        states={
            MAIL_SUBJECT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mail_subject)],
            MAIL_BODY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mail_body)],
            MAIL_EVIDENCE:    [MessageHandler(filters.PHOTO, receive_mail_evidence),
                               CommandHandler("skip", skip_mail_evidence)],
            MAIL_RECIPIENT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mail_recipient)],
            MAIL_BLAST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_blast_count)],
            MAIL_RESEND:      [CallbackQueryHandler(gmail_resend_or_done, pattern="^(RESEND|DONE)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)], per_message=False, allow_reentry=True)

    app.add_handler(CommandHandler("start",         start_cmd))
    app.add_handler(CommandHandler("help",          help_cmd))
    app.add_handler(CommandHandler("restart",       restart_cmd))
    app.add_handler(CommandHandler("allaccounts",   allaccounts_cmd))
    app.add_handler(CommandHandler("proxystatus",   proxystatus_cmd))
    app.add_handler(CommandHandler("reloadproxies", reloadproxies_cmd))
    app.add_handler(CommandHandler("proxyon",       proxyon_cmd))
    app.add_handler(CommandHandler("proxyoff",      proxyoff_cmd))
    app.add_handler(CommandHandler("logs",          logs_cmd))
    app.add_handler(CommandHandler("clearlogs",     clearlogs_cmd))
    app.add_handler(CommandHandler("sudo",          sudo_cmd))
    app.add_handler(CommandHandler("rmsudo",        rmsudo_cmd))
    app.add_handler(CommandHandler("sudolist",      sudolist_cmd))
    app.add_handler(add_conv)
    app.add_handler(rm_conv)
    app.add_handler(ar_conv)
    app.add_handler(br_conv)
    app.add_handler(report_conv)
    app.add_handler(group_report_conv)
    app.add_handler(gmail_conv)
    app.add_handler(CallbackQueryHandler(menu_router, pattern="^MENU\\|"))

    logger.info(f"⚡ ULTIMATE REPORTER v{BOT_VERSION} — RUNNING")
    add_log(f"⚡ Bot v{BOT_VERSION} online (proxy={'ON' if PROXY_ENABLED else 'OFF'})")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
