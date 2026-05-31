"""
╔══════════════════════════════════════════════════════════════════════╗
║   ⚡ ULTIMATE TELEGRAM REPORTER v13.0 — CYBER JUSTICE ELITE ⚡       ║
║──────────────────────────────────────────────────────────────────────║
║   🌐 SMART Proxy (OFF by default → ZERO connection errors)          ║
║   ✅ Auto-fallback: dead proxy → direct connect (no crash)          ║
║   🔄 Health-check + auto-skip dead proxies                          ║
║   🎨 BEAUTIFUL inline button menu on /start                          ║
║   📸 NUCLEAR PFP Reporter (6 methods)                               ║
║   🤖 Bot Reporter w/ FULL Telegram report categories + subs         ║
║   📩 Message Reporter w/ FULL Telegram report categories + subs     ║
║   🔁 ROUND-ROBIN distribution (acc1→acc2→acc3→acc1→...)             ║
║   💥 Gmail BLAST x N (custom loop count)                            ║
║   🔐 Sudo System (atomic save/load)                                 ║
║   🚀 Up to 100 reports/account                                      ║
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
BOT_VERSION             = "13.0"

PROXY_ENABLED = False

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
        return f"{C.DIM}[{ts}]{C.RESET} {lvl} {record.getMessage()}"

logger = logging.getLogger("ultimate")
logger.setLevel(logging.INFO)
logger.handlers.clear()

_console = logging.StreamHandler(sys.stdout)
_console.setFormatter(ColorFormatter())
logger.addHandler(_console)

_file = logging.FileHandler(LOGS_DIR / "bot.log", encoding="utf-8")
_file.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(_file)

logging.getLogger("telethon").setLevel(logging.ERROR)
logging.getLogger("telethon.network").setLevel(logging.CRITICAL)

# ══════════════════════════════════════════════════════════════════════
# 💾 GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════
accounts: Dict[str, TelegramClient] = {}
sudo_users: set = set()
sudo_info:  Dict[int, dict] = {}
account_proxy_map: Dict[str, dict] = {}
proxy_health: Dict[str, dict] = {}
proxy_cursor: int = 0
live_logs: List[str] = []
report_stats = {"total": 0, "success": 0, "failed": 0, "start_time": None}

# ══════════════════════════════════════════════════════════════════════
# 🎭 REALISTIC REPORT MESSAGES
# ══════════════════════════════════════════════════════════════════════
REALISTIC_REPORT_MSGS = [
    "This content violates Telegram's Terms of Service. Please review urgently.",
    "Highly inappropriate material being shared. Requesting immediate moderation.",
    "Disturbing content that should not be on this platform. Please take action.",
    "Reporting for explicit violation of community guidelines.",
    "This user repeatedly shares prohibited content. Strong action needed.",
    "Found extremely offensive and harmful material. Urgent review required.",
    "Content endangering minors / vulnerable users. Immediate removal please.",
    "This breaches multiple Telegram policies. Kindly investigate.",
    "Spam / scam content detected — please remove and ban.",
    "Hateful and abusive content. Reporting for swift action.",
    "Illegal content shared publicly. Telegram team please respond.",
    "Account appears to be involved in fraudulent activity.",
    "Sharing private/leaked content without consent. Take down please.",
    "Promotes self-harm / dangerous behaviour. Needs immediate action.",
    "Impersonation of a real person/brand. Verify and take down.",
    "CSAM-adjacent content detected. Escalating to Telegram safety.",
    "Coordinated harassment campaign — please investigate group.",
    "Phishing links being distributed. Urgent intervention needed.",
    "Promotes terrorism / extremist propaganda. Immediate removal.",
    "Selling drugs / illegal goods openly. Please act.",
    "Doxing innocent users — privacy violation, take action.",
    "Glorifies violence against specific groups. Hate speech.",
    "Pyramid scheme / financial fraud being promoted here.",
    "Hacked / leaked credentials being distributed.",
    "Adult content shared in a public group with minors present.",
    "This is a known scam operator — multiple victims already reported.",
    "Repeated TOS violations despite previous warnings. Permanent ban requested.",
    "Misinformation that can cause real-world harm.",
    "Animal cruelty videos being shared. Disgusting — please remove.",
]
REPORT_PREFIXES = ["Dear Telegram Team, ", "Hello Support, ", "Hi Moderators, ",
                   "Respected team, ", "Urgent: ", "Reporting: ", "Concerned user here — ",
                   "Hi, as a long-time user — ", "Greetings, ", ""]

# ══════════════════════════════════════════════════════════════════════
# 🏷️ FULL TELEGRAM REPORT CATEGORIES (matches in-app report flow)
# Used by BOTH /report (message) and /botreport
# ══════════════════════════════════════════════════════════════════════
# Structure: key -> {emoji, label, api_reason, subs: [(sub_key, sub_label), ...] or None,
#                    direct: bool (True = no sub-menu, jump to optional msg)}
FULL_REPORT_CATEGORIES = {
    "dont_like": {
        "emoji": "👎", "label": "I don't like it",
        "api": types.InputReportReasonOther(),
        "subs": None, "direct": True, "needs_msg": False,
    },
    "child_abuse": {
        "emoji": "👶", "label": "Child abuse",
        "api": types.InputReportReasonChildAbuse(),
        "subs": [
            ("csa", "Child sexual abuse"),
            ("cpa", "Child physical abuse"),
        ],
        "direct": False, "needs_msg": True,
    },
    "violence": {
        "emoji": "🔪", "label": "Violence",
        "api": types.InputReportReasonViolence(),
        "subs": [
            ("v1", "Insults or false information"),
            ("v2", "Graphic or disturbing content"),
            ("v3", "Extreme violence, dismemberment"),
            ("v4", "Hate speech or symbols"),
            ("v5", "Calling for violence"),
            ("v6", "Organized crime"),
            ("v7", "Terrorism"),
            ("v8", "Animal abuse"),
        ],
        "direct": False, "needs_msg": True,
    },
    "illegal_goods": {
        "emoji": "⚖️", "label": "Illegal goods and services",
        "api": types.InputReportReasonIllegalDrugs(),
        "subs": [
            ("ig1", "Weapons"),
            ("ig2", "Drugs"),
            ("ig3", "Fake documents"),
            ("ig4", "Counterfeit money"),
            ("ig5", "Hacking tools and malware"),
            ("ig6", "Counterfeit merchandise"),
            ("ig7", "Other goods and services"),
        ],
        "direct": False, "needs_msg": True,
    },
    "illegal_adult": {
        "emoji": "🔞", "label": "Illegal adult content",
        "api": types.InputReportReasonPornography(),
        "subs": [
            ("ia1", "Child abuse"),
            ("ia2", "Illegal sexual services"),
            ("ia3", "Animal abuse"),
            ("ia4", "Non-consensual sexual imagery"),
            ("ia5", "Pornography"),
            ("ia6", "Other illegal sexual content"),
        ],
        "direct": False, "needs_msg": True,
    },
    "personal_data": {
        "emoji": "🆔", "label": "Personal data",
        "api": types.InputReportReasonPersonalDetails(),
        "subs": [
            ("pd1", "Private images"),
            ("pd2", "Phone number"),
            ("pd3", "Address"),
            ("pd4", "Stolen data or credentials"),
            ("pd5", "Other personal information"),
        ],
        "direct": False, "needs_msg": True,
    },
    "scam_fraud": {
        "emoji": "🎭", "label": "Scam or fraud",
        "api": types.InputReportReasonFake(),
        "subs": [
            ("sf1", "Impersonation"),
            ("sf2", "Deceptive or unrealistic financial claims"),
            ("sf3", "Malware, phishing"),
            ("sf4", "Fraudulent seller, product or service"),
        ],
        "direct": False, "needs_msg": True,
    },
    "copyright": {
        "emoji": "©️", "label": "Copyright",
        "api": types.InputReportReasonCopyright(),
        "subs": None, "direct": True, "needs_msg": True,
    },
    "spam": {
        "emoji": "🚫", "label": "Spam",
        "api": types.InputReportReasonSpam(),
        "subs": [
            ("sp1", "Insults or false information"),
            ("sp2", "Promoting illegal content"),
            ("sp3", "Promoting other content"),
        ],
        "direct": False, "needs_msg": True,
    },
    "other": {
        "emoji": "❓", "label": "Other",
        "api": types.InputReportReasonOther(),
        "subs": None, "direct": True, "needs_msg": True,
    },
    "not_illegal": {
        "emoji": "⚠️", "label": "It's not illegal, but must be taken down",
        "api": types.InputReportReasonOther(),
        "subs": None, "direct": True, "needs_msg": True,
    },
}

# Conversation states
(PHONE, CODE, PASSWORD,
 RM_PHONE,
 GRP_LINK, MSG_LINK, REASON_CAT, REASON_SUB, CUSTOM_MSG, COUNT,
 MAIL_SUBJECT, MAIL_BODY, MAIL_EVIDENCE, MAIL_RECIPIENT, MAIL_BLAST_COUNT, MAIL_RESEND,
 AR_USER, AR_REASON, AR_OTHER_MSG, AR_COUNT,
 BR_USER, BR_CAT, BR_SUB, BR_MSG, BR_COUNT,
) = range(25)

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
    if len(live_logs) > 800:
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

def craft_report_message(base_msg: str, sub_label: str = "") -> str:
    pool_msg = random.choice(REALISTIC_REPORT_MSGS)
    prefix   = random.choice(REPORT_PREFIXES)
    extras = []
    if sub_label and sub_label not in ("N/A", ""):
        extras.append(f"Category: {sub_label}.")
    if base_msg and base_msg.strip() and base_msg.strip().lower() not in ("skip", "default", ""):
        roll = random.random()
        if   roll < 0.3: body = base_msg
        elif roll < 0.7: body = f"{base_msg} {pool_msg}"
        else:            body = f"{pool_msg} {base_msg}"
    else:
        body = pool_msg
    body = " ".join(extras + [body]).strip()
    if random.random() < 0.4:
        body += f" [Ref#{random.randint(10000, 99999)}]"
    return f"{prefix}{body}".strip()

# ══════════════════════════════════════════════════════════════════════
# 📱 TELEGRAM CLIENT FACTORY
# ══════════════════════════════════════════════════════════════════════
def build_client(session, proxy_cfg=None) -> TelegramClient:
    kwargs = dict(
        device_model="iPhone 14 Pro",
        system_version="iOS 16.5",
        app_version="9.6.3",
        lang_code="en", system_lang_code="en-US",
        connection_retries=2, retry_delay=1, timeout=20,
    )
    if PROXY_ENABLED and proxy_cfg and socks is not None:
        p_type = socks.SOCKS5 if proxy_cfg.get("type","").lower() == "socks5" else socks.HTTP
        kwargs["proxy"] = (
            p_type, proxy_cfg["addr"], int(proxy_cfg["port"]), True,
            proxy_cfg.get("username"), proxy_cfg.get("password"),
        )
    return TelegramClient(session, API_ID, API_HASH, **kwargs)

async def safe_connect(client: TelegramClient, phone: str = "") -> bool:
    try:
        await asyncio.wait_for(client.connect(), timeout=15)
        return True
    except Exception as e:
        if PROXY_ENABLED and phone:
            add_log(f"⚠️ Proxy failed for {phone[-4:]} ({type(e).__name__}) — falling back to direct")
            try:
                try: await client.disconnect()
                except: pass
                px = account_proxy_map.get(phone)
                if px:
                    mark_proxy_result(px, False)
                    account_proxy_map.pop(phone, None)
                sess = client.session
                new_client = build_client(sess, None)
                new_client._proxy = None
                await asyncio.wait_for(new_client.connect(), timeout=15)
                accounts[phone] = new_client
                add_log(f"✅ Direct connect OK: {phone[-4:]}")
                return True
            except Exception as e2:
                add_log(f"❌ Direct connect also failed for {phone[-4:]}: {type(e2).__name__}")
                return False
        else:
            add_log(f"❌ Connect failed: {type(e).__name__}: {str(e)[:60]}")
            return False

def load_accounts():
    data = safe_load_json(ACCOUNTS_FILE, {})
    if not data: return
    proxies = healthy_proxies() if PROXY_ENABLED else []
    for i, (phone, sess) in enumerate(data.items()):
        try:
            proxy = proxies[i % len(proxies)] if proxies else None
            client = build_client(StringSession(sess), proxy)
            accounts[phone] = client
            if proxy: account_proxy_map[phone] = proxy
            add_log(f"✅ Loaded: {phone}" + (f" [proxy: {proxy['addr']}]" if proxy else " [direct]"))
        except Exception as e:
            logger.error(f"Load error {phone}: {e}")

def save_accounts():
    try:
        data = {p: StringSession.save(c.session) for p, c in accounts.items() if c.session}
        if atomic_save_json(ACCOUNTS_FILE, data):
            add_log(f"💾 Saved {len(data)} accounts")
    except Exception as e:
        logger.error(f"Save error: {e}")

async def count_active() -> int:
    n = 0
    for c in accounts.values():
        try:
            if await c.is_user_authorized(): n += 1
        except: pass
    return n

async def get_any_active_client() -> Optional[TelegramClient]:
    for c in accounts.values():
        try:
            if await c.is_user_authorized(): return c
        except: pass
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
# 🔄 GROUP JOIN
# ══════════════════════════════════════════════════════════════════════
async def join_group_all(identifier, link_type) -> Tuple[int, int]:
    if link_type == "username":
        add_log(f"ℹ️ Public group '{identifier}' — skipping join.")
        return (len(accounts), 0)
    ok, fail = 0, 0
    for phone, client in accounts.items():
        try:
            if not await client.is_user_authorized():
                fail += 1; continue
            if link_type == "invite":
                try:
                    await client(ImportChatInviteRequest(identifier))
                    ok += 1; add_log(f"✅ Joined (invite): {phone[-4:]}")
                except errors.UserAlreadyParticipantError:
                    ok += 1; add_log(f"✅ Already member: {phone[-4:]}")
                except errors.InviteHashExpiredError:
                    fail += 1; add_log(f"❌ Expired invite: {phone[-4:]}")
                except errors.InviteHashInvalidError:
                    fail += 1; add_log(f"❌ Invalid invite: {phone[-4:]}")
                except Exception as e:
                    fail += 1; add_log(f"❌ Invite join fail: {phone[-4:]} — {e}")
            elif link_type == "private_channel":
                try:
                    await client(JoinChannelRequest(identifier))
                    ok += 1; add_log(f"✅ Joined (private ch): {phone[-4:]}")
                except errors.UserAlreadyParticipantError:
                    ok += 1; add_log(f"✅ Already member: {phone[-4:]}")
                except Exception as e:
                    fail += 1; add_log(f"❌ Private ch join fail: {phone[-4:]} — {e}")
            await asyncio.sleep(random.uniform(1.5, 3.5))
        except Exception as e:
            fail += 1; add_log(f"❌ Join error: {phone[-4:]} — {e}")
    return (ok, fail)

# ══════════════════════════════════════════════════════════════════════
# 🎯 ENTITY RESOLVER
# ══════════════════════════════════════════════════════════════════════
async def resolve_chat_entity(client, identifier: str, link_type: str):
    if str(identifier).lstrip("-").isdigit():
        raw = str(identifier).lstrip("-")
        for candidate in (int(f"-100{raw}"), int(raw), -int(raw)):
            try:
                return await client.get_input_entity(candidate)
            except Exception:
                continue
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
# 🚀 CORE MESSAGE REPORT ENGINE
# ══════════════════════════════════════════════════════════════════════
async def send_report(client, channel_id, msg_id, reason_api, custom_msg, phone,
                      link_type="username", sub_label="") -> Tuple[bool, str]:
    proxy = account_proxy_map.get(phone)
    try:
        try:
            entity = await resolve_chat_entity(client, channel_id, link_type)
        except Exception as e:
            mark_proxy_result(proxy, False)
            return (False, f"Entity error: {str(e)[:50]}")

        msg_id_int = int(msg_id)
        await asyncio.sleep(random.uniform(0.3, 1.2))

        # M1
        try:
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=[msg_id_int],
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M1 OK: {phone[-4:]}")
                return (True, "Success (M1: messages.report)")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except errors.MessageIdInvalidError:
            return (False, "Invalid Message ID")
        except errors.ChannelPrivateError:
            return (False, "Private channel — no access")
        except errors.UserBannedInChannelError:
            return (False, "Account banned in channel")
        except Exception as e:
            add_log(f"⚠️ M1 fail {phone[-4:]}: {type(e).__name__}")

        # M2
        await asyncio.sleep(random.uniform(0.5, 1.5))
        try:
            msgs = await client.get_messages(entity, ids=msg_id_int)
            if msgs:
                result = await client(functions.messages.ReportRequest(
                    peer=entity, id=[msg_id_int],
                    reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
                if result:
                    mark_proxy_result(proxy, True)
                    add_log(f"✅ M2 OK: {phone[-4:]}")
                    return (True, "Success (M2: prefetch+report)")
        except Exception as e:
            add_log(f"⚠️ M2 fail {phone[-4:]}: {type(e).__name__}")

        # M3
        await asyncio.sleep(random.uniform(0.5, 1.0))
        try:
            result = await client(functions.account.ReportPeerRequest(
                peer=entity, reason=reason_api,
                message=f"Re: Msg ID {msg_id} — {craft_report_message(custom_msg, sub_label)}"))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M3 OK: {phone[-4:]}")
                return (True, "Success (M3: account.reportPeer)")
        except Exception as e:
            add_log(f"⚠️ M3 fail {phone[-4:]}: {type(e).__name__}")

        # M4
        await asyncio.sleep(random.uniform(0.5, 1.0))
        try:
            entity = await resolve_chat_entity(client, channel_id, link_type)
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=[msg_id_int],
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M4 OK: {phone[-4:]}")
                return (True, "Success (M4: re-resolve+report)")
        except Exception as e:
            add_log(f"⚠️ M4 fail {phone[-4:]}: {type(e).__name__}")

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
# 📸 NUCLEAR PFP REPORT (unchanged, kept for /accountreport)
# ══════════════════════════════════════════════════════════════════════
PFP_REPORT_REASONS = {
    "pfp_porn":     ("🔞 Pornographic",        types.InputReportReasonPornography()),
    "pfp_child":    ("👶 Child Abuse",         types.InputReportReasonChildAbuse()),
    "pfp_violen":   ("🔪 Violence",            types.InputReportReasonViolence()),
    "pfp_fake":     ("🎭 Fake / Impersonation",types.InputReportReasonFake()),
    "pfp_personal": ("🆔 Personal Details",    types.InputReportReasonPersonalDetails()),
    "pfp_other":    ("❓ Other",               types.InputReportReasonOther()),
}

async def report_profile_photo_nuclear(client, user_entity, photos, reason_api, custom_msg, phone) -> Tuple[bool, str]:
    proxy = account_proxy_map.get(phone)
    methods_tried = []

    if photos:
        try:
            photo = photos[0]
            input_photo = tl_types.InputPhoto(
                id=photo.id, access_hash=photo.access_hash,
                file_reference=photo.file_reference)
            await asyncio.sleep(random.uniform(0.3, 1.0))
            result = await client(functions.account.ReportProfilePhotoRequest(
                peer=user_entity, photo_id=input_photo,
                reason=reason_api, message=craft_report_message(custom_msg)))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ PFP-M1 OK: {phone[-4:]}")
                return (True, "Success (M1: ReportProfilePhoto)")
            methods_tried.append("M1")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except Exception as e:
            methods_tried.append(f"M1-fail({type(e).__name__})")

    if photos and len(photos) > 1:
        for idx, ph in enumerate(photos[1:6], start=2):
            try:
                await asyncio.sleep(random.uniform(0.4, 1.0))
                ip = tl_types.InputPhoto(id=ph.id, access_hash=ph.access_hash, file_reference=ph.file_reference)
                r = await client(functions.account.ReportProfilePhotoRequest(
                    peer=user_entity, photo_id=ip,
                    reason=reason_api, message=craft_report_message(custom_msg)))
                if r:
                    mark_proxy_result(proxy, True)
                    add_log(f"✅ PFP-M2[{idx}] OK: {phone[-4:]}")
                    return (True, f"Success (M2: older photo #{idx})")
            except errors.FloodWaitError as e:
                return (False, f"FloodWait {e.seconds}s")
            except Exception:
                continue
        methods_tried.append("M2")

    try:
        await asyncio.sleep(random.uniform(0.5, 1.2))
        r = await client(functions.account.ReportPeerRequest(
            peer=user_entity, reason=reason_api,
            message=f"Profile photo violation. {craft_report_message(custom_msg)}"))
        if r:
            mark_proxy_result(proxy, True)
            add_log(f"✅ PFP-M3 OK: {phone[-4:]}")
            return (True, "Success (M3: ReportPeer)")
        methods_tried.append("M3")
    except Exception as e:
        methods_tried.append(f"M3-fail({type(e).__name__})")

    try:
        await asyncio.sleep(random.uniform(0.6, 1.4))
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
                add_log(f"✅ PFP-M4 OK: {phone[-4:]}")
                return (True, "Success (M4: refresh+retry)")
        methods_tried.append("M4")
    except Exception as e:
        methods_tried.append(f"M4-fail({type(e).__name__})")

    try:
        await asyncio.sleep(random.uniform(0.4, 1.0))
        r = await client(functions.messages.ReportRequest(
            peer=user_entity, id=[0], reason=reason_api,
            message=craft_report_message(custom_msg)))
        if r:
            mark_proxy_result(proxy, True)
            add_log(f"✅ PFP-M5 OK: {phone[-4:]}")
            return (True, "Success (M5: messages.report)")
        methods_tried.append("M5")
    except Exception:
        methods_tried.append("M5")

    try:
        await asyncio.sleep(random.uniform(0.4, 0.9))
        r = await client(functions.messages.ReportSpamRequest(peer=user_entity))
        if r:
            mark_proxy_result(proxy, True)
            add_log(f"✅ PFP-M6 OK: {phone[-4:]}")
            return (True, "Success (M6: ReportSpam fallback)")
        methods_tried.append("M6")
    except Exception:
        methods_tried.append("M6")

    mark_proxy_result(proxy, False)
    add_log(f"❌ PFP ALL FAIL: {phone[-4:]} — tried: {','.join(methods_tried)}")
    return (False, "All 6 methods failed")

# ══════════════════════════════════════════════════════════════════════
# ⏱ DELAYS
# ══════════════════════════════════════════════════════════════════════
def smart_delay(i, total) -> float:
    base  = random.uniform(4, 10)
    extra = random.uniform(0, 6) if random.random() < 0.3 else 0
    if i > total * 0.7: extra += random.uniform(2, 5)
    return base + extra

def account_switch_delay() -> float:
    return random.uniform(5, 12)

def round_robin_delay() -> float:
    """Smaller delay since we're rotating between accounts each shot."""
    return random.uniform(3, 7)

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
            await asyncio.sleep(random.uniform(3, 6))
    return (total_ok, total_fail, "\n\n".join(details_all))

# ══════════════════════════════════════════════════════════════════════
# 🚀 POST INIT / SHUTDOWN
# ══════════════════════════════════════════════════════════════════════
async def post_init(app):
    add_log("🔧 Initializing...")
    if PROXY_ENABLED:
        add_log("🌐 Loading & testing free proxies...")
        load_free_proxies(max_proxies=15, test=True)
        add_log(f"🌐 {len(PROXY_LIST)} working proxies loaded")
    else:
        add_log("⚡ PROXY OFF — direct connection mode (no errors)")
    load_proxy_health()
    load_sudo()
    load_accounts()
    for phone, client in list(accounts.items()):
        ok = await safe_connect(client, phone)
        if ok:
            try:
                client = accounts[phone]
                if await client.is_user_authorized():
                    add_log(f"🟢 Connected: {phone}")
                else:
                    add_log(f"🔴 Not authorized: {phone}")
            except Exception as e:
                logger.error(f"Auth check {phone}: {e}")

async def post_shutdown(app):
    add_log("🛑 Shutting down…")
    save_accounts(); save_sudo(); save_proxy_health()
    for phone, client in accounts.items():
        try: await client.disconnect()
        except: pass

# ══════════════════════════════════════════════════════════════════════
# 🎬 ANIMATED /start
# ══════════════════════════════════════════════════════════════════════
async def animated_start(message):
    frames = [
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▱▱▱▱▱▱▱▱▱▱  0%",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▱▱▱▱▱▱▱▱  20%\n\n🔧 Loading core modules...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▱▱▱▱▱▱  40%\n\n🌐 Verifying network...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▱▱▱▱  60%\n\n📸 Arming PFP nuclear engine...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▰▰▱▱  80%\n\n🛡️ Engaging stealth mode...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▰▰▰▰  100%\n\n🚀 ONLINE — having vibes 😎",
    ]
    msg = await message.reply_text(frames[0], parse_mode="HTML")
    for f in frames[1:]:
        await asyncio.sleep(0.45)
        try:
            await msg.edit_text(f, parse_mode="HTML")
        except Exception:
            pass
    await asyncio.sleep(0.3)
    return msg

def _main_menu_keyboard(is_owner: bool):
    rows = [
        [InlineKeyboardButton("📩 Message Report", callback_data="MENU|report"),
         InlineKeyboardButton("👤 Account Report", callback_data="MENU|accountreport")],
        [InlineKeyboardButton("🤖 Bot Report",     callback_data="MENU|botreport"),
         InlineKeyboardButton("📧 Mass Gmail",     callback_data="MENU|massgmail")],
        [InlineKeyboardButton("➕ Add Account",    callback_data="MENU|addaccount"),
         InlineKeyboardButton("📋 All Accounts",   callback_data="MENU|allaccounts")],
        [InlineKeyboardButton("🗑️ Remove Account",callback_data="MENU|rmaccount"),
         InlineKeyboardButton("📊 Logs",           callback_data="MENU|logs")],
        [InlineKeyboardButton("🌐 Proxy Status",   callback_data="MENU|proxystatus"),
         InlineKeyboardButton("🔄 Reload Proxies", callback_data="MENU|reloadproxies")],
        [InlineKeyboardButton("ℹ️ Help",           callback_data="MENU|help"),
         InlineKeyboardButton("🧹 Clear Logs",     callback_data="MENU|clearlogs")],
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
    await asyncio.sleep(0.4)

    proxy_status = "🟢 ON" if PROXY_ENABLED else "⚡ OFF (direct)"
    welcome = (
        f"⚡ <b>ULTIMATE REPORTER v{BOT_VERSION}</b>\n"
        f"<b>CYBER JUSTICE ELITE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ Access : <b>{owner_tag}</b>\n"
        f"🌐 Proxy  : <b>{proxy_status}</b>\n"
        f"📱 Accounts: <b>{len(accounts)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <b>Choose an action below:</b>"
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
    info_map = {
        "report":        ("📩 <b>Message Report</b>\n\nUse /report to start a message-report flow with the full Telegram report category tree (11 categories + subcategories).", "/report"),
        "accountreport": ("👤 <b>Account / PFP Report</b>\n\nUse /accountreport — 6-method nuclear PFP reporter.", "/accountreport"),
        "botreport":     ("🤖 <b>Bot Report</b>\n\nUse /botreport — same full Telegram report categories as message report (3-dots → Report flow).", "/botreport"),
        "massgmail":     ("📧 <b>Mass Gmail Blast</b>\n\nUse /massgmail — fires all Gmail accounts × N rounds.", "/massgmail"),
        "addaccount":    ("➕ <b>Add Telegram Account</b>\n\nUse /addaccount and follow prompts.", "/addaccount"),
        "rmaccount":     ("🗑️ <b>Remove Account</b>\n\nUse /rmaccount to remove an account.", "/rmaccount"),
        "allaccounts":   ("📋 Use /allaccounts to list all accounts.", "/allaccounts"),
        "logs":          ("📊 Use /logs to view activity.", "/logs"),
        "clearlogs":     ("🧹 Use /clearlogs to clear logs & stats.", "/clearlogs"),
        "proxystatus":   ("🌐 Use /proxystatus to view proxy health.", "/proxystatus"),
        "reloadproxies": ("🔄 Use /reloadproxies to refresh proxy pool.", "/reloadproxies"),
        "help":          ("ℹ️ Use /help for full command list.", "/help"),
        "sudolist":      ("🔑 Use /sudolist (owner only).", "/sudolist"),
        "toggleproxy":   ("⚙️ Use /proxyon to enable proxy, /proxyoff to disable.", "/proxyon /proxyoff"),
    }
    text, hint = info_map.get(action, ("Unknown action.", "/start"))
    is_owner = (update.effective_user.id == OWNER_ID)
    try:
        await query.edit_message_text(
            text + f"\n\n👉 Type: <code>{hint}</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="MENU|back")
            ]]))
    except Exception:
        pass
    if action == "back":
        try:
            proxy_status = "🟢 ON" if PROXY_ENABLED else "⚡ OFF (direct)"
            welcome = (
                f"⚡ <b>ULTIMATE REPORTER v{BOT_VERSION}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 Proxy: <b>{proxy_status}</b> | 📱 Accounts: <b>{len(accounts)}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👇 Choose an action:")
            await query.edit_message_text(welcome, parse_mode="HTML",
                                          reply_markup=_main_menu_keyboard(is_owner))
        except Exception:
            pass

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    await update.message.reply_text(
        f"📖 <b>HELP — v{BOT_VERSION}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 <b>/report</b> — Report a message (full TG categories)\n"
        "📸 <b>/accountreport</b> — Nuclear PFP report\n"
        "🤖 <b>/botreport</b> — Report a bot (full TG categories)\n"
        "📧 <b>/massgmail</b> — Gmail blast × N\n"
        "➕ <b>/addaccount</b> — Add Telegram account\n"
        "🗑️ <b>/rmaccount</b> — Remove account\n"
        "📋 <b>/allaccounts</b> — List accounts\n"
        "🌐 <b>/proxystatus</b> — Proxy health\n"
        "🔄 <b>/reloadproxies</b> — Refresh proxy pool\n"
        "⚙️ <b>/proxyon /proxyoff</b> — Toggle proxy (owner)\n"
        "📊 <b>/logs</b> — Activity logs\n"
        "🧹 <b>/clearlogs</b> — Clear logs & stats\n"
        "❌ <b>/cancel</b> — Cancel current flow\n\n"
        "👑 Owner: /sudo /rmsudo /sudolist\n\n"
        "💡 <b>Tip:</b> Round-robin firing — acc1→acc2→acc3→acc1→...\n",
        parse_mode="HTML"
    )

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    add_log("❌ User cancelled flow")
    await update.message.reply_text("❌ Cancelled.\nUse /start to open the menu again.")
    return ConversationHandler.END

async def logs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    txt = f"📊 <b>ACTIVITY</b>\n\n{get_stats()}\n\n<pre>{get_logs(60)}</pre>"
    if len(txt) > 4000: txt = txt[:3990] + "\n...(truncated)"
    await update.message.reply_text(txt, parse_mode="HTML")

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
            auth   = await client.is_user_authorized()
            status = "🟢 Active" if auth else "🔴 Inactive"
            if auth: active += 1
            proxy  = account_proxy_map.get(phone)
            p_txt  = f" [🌐 {proxy['addr']}]" if proxy else " [⚡ direct]"
        except:
            status = "🔴 Inactive"; p_txt = ""
        txt += f"{i}. <code>{phone}</code> — {status}{p_txt}\n"
    txt += f"\n📊 Total: {len(accounts)} | 🟢 {active} | 🔴 {len(accounts)-active}"
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
    txt += f"<b>Pool:</b> {len(PROXY_LIST)} total\n\n"
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
    await msg.edit_text(f"✅ Loaded {len(PROXY_LIST)} <b>working</b> proxies\n"
                        f"Mode: {'🟢 ON' if PROXY_ENABLED else '⚡ OFF (direct)'}",
                        parse_mode="HTML")

async def proxyon_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    global PROXY_ENABLED
    PROXY_ENABLED = True
    await update.message.reply_text(
        "🟢 <b>Proxy mode: ENABLED</b>\n\n"
        "⚠️ Free proxies are often dead — if you see connection errors, run /proxyoff.\n"
        "Run /reloadproxies to refresh the pool.",
        parse_mode="HTML")

async def proxyoff_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    global PROXY_ENABLED
    PROXY_ENABLED = False
    account_proxy_map.clear()
    await update.message.reply_text(
        "⚡ <b>Proxy mode: DISABLED</b>\n\n"
        "All accounts will use direct connection.\n"
        "Zero proxy errors. Recommended for stability.",
        parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════════
# 🔐 SUDO
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
    txt += f"━━━━━━━━━━━━━━━━━━━━\n📊 Total: {len(sudo_users)}"
    await update.message.reply_text(txt, parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════════
# 📱 ADD / REMOVE ACCOUNT
# ══════════════════════════════════════════════════════════════════════
async def addaccount_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📱 <b>ADD ACCOUNT</b>\n\nEnter phone with country code:\n<code>+91XXXXXXXXXX</code>\n\n/cancel to abort.", parse_mode="HTML")
    return PHONE

async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    ctx.user_data["phone"] = phone
    if phone in accounts:
        await update.message.reply_text("⚠️ Already exists!"); return ConversationHandler.END
    try:
        proxy  = next_proxy()
        client = build_client(StringSession(), proxy)
        try:
            await asyncio.wait_for(client.connect(), timeout=15)
        except Exception as e:
            if proxy:
                add_log(f"⚠️ Add-account proxy failed, retrying direct: {type(e).__name__}")
                try: await client.disconnect()
                except: pass
                proxy = None
                client = build_client(StringSession(), None)
                await asyncio.wait_for(client.connect(), timeout=15)
            else:
                raise
        sent   = await client.send_code_request(phone)
        ctx.user_data.update({"phone_hash": sent.phone_code_hash, "temp_client": client, "temp_proxy": proxy})
        await update.message.reply_text("📩 OTP sent! Enter code:")
        add_log(f"📱 Adding: {phone}")
        return CODE
    except errors.PhoneNumberInvalidError:
        await update.message.reply_text("❌ Invalid number! Try again:"); return PHONE
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}"); return ConversationHandler.END

async def add_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    code   = update.message.text.strip().replace(" ","").replace("-","")
    phone  = ctx.user_data.get("phone")
    p_hash = ctx.user_data.get("phone_hash")
    client = ctx.user_data.get("temp_client")
    proxy  = ctx.user_data.get("temp_proxy")
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=p_hash)
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        save_accounts(); add_log(f"✅ Added: {phone}")
        await update.message.reply_text(f"✅ <b>Added!</b>\n📱 <code>{phone}</code>\nTotal: {len(accounts)}", parse_mode="HTML")
        return ConversationHandler.END
    except errors.SessionPasswordNeededError:
        await update.message.reply_text("🔒 2FA — enter password:"); return PASSWORD
    except errors.PhoneCodeInvalidError:
        await update.message.reply_text("❌ Wrong code! Try again:"); return CODE
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}"); return ConversationHandler.END

async def add_password(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    client = ctx.user_data.get("temp_client"); phone = ctx.user_data.get("phone")
    proxy  = ctx.user_data.get("temp_proxy")
    try:
        await client.sign_in(password=update.message.text.strip())
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        save_accounts(); add_log(f"✅ Added (2FA): {phone}")
        await update.message.reply_text(f"✅ <b>Added (2FA)!</b>\n📱 <code>{phone}</code>", parse_mode="HTML")
        return ConversationHandler.END
    except errors.PasswordHashInvalidError:
        await update.message.reply_text("❌ Wrong password! Try again:"); return PASSWORD
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}"); return ConversationHandler.END

async def rmaccount_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("📭 No accounts."); return ConversationHandler.END
    txt = "📱 <b>REMOVE ACCOUNT</b>\n\nEnter phone to remove:\n\n"
    for p in accounts: txt += f"• <code>{p}</code>\n"
    await update.message.reply_text(txt, parse_mode="HTML")
    return RM_PHONE

async def rm_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    if phone not in accounts:
        await update.message.reply_text("❌ Not found! Try again:"); return RM_PHONE
    try:
        client = accounts[phone]
        try: await client.log_out()
        except: pass
        try: await client.disconnect()
        except: pass
        del accounts[phone]
        account_proxy_map.pop(phone, None)
        save_accounts(); add_log(f"🗑 Removed: {phone}")
        await update.message.reply_text(f"✅ Removed <code>{phone}</code>\nRemaining: {len(accounts)}", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 🎯 KEYBOARDS — FULL REPORT CATEGORY TREE
# ══════════════════════════════════════════════════════════════════════
def _build_full_cat_keyboard(prefix: str):
    """prefix: 'CAT' for /report, 'BCAT' for /botreport"""
    rows = []
    for key, data in FULL_REPORT_CATEGORIES.items():
        rows.append([InlineKeyboardButton(
            f"{data['emoji']} {data['label']}",
            callback_data=f"{prefix}|{key}")])
    return InlineKeyboardMarkup(rows)

def _build_sub_keyboard(cat_key: str, prefix: str):
    """prefix: 'SUB' for /report, 'BSUB' for /botreport"""
    cat = FULL_REPORT_CATEGORIES[cat_key]
    rows = []
    for sub_key, sub_label in cat["subs"]:
        rows.append([InlineKeyboardButton(
            sub_label,
            callback_data=f"{prefix}|{cat_key}|{sub_key}")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"{prefix}|__back__")])
    return InlineKeyboardMarkup(rows)

# ══════════════════════════════════════════════════════════════════════
# 🎯 MESSAGE REPORT FLOW
# ══════════════════════════════════════════════════════════════════════
async def report_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats()
    add_log("🎯 Report flow started")
    await update.message.reply_text(
        f"🎯 <b>REPORT FLOW</b> — Step 1/7\n\n"
        f"✅ Active: {active}/{len(accounts)} accounts\n\n"
        f"📥 Send <b>GROUP / CHANNEL LINK</b>:\n\n"
        f"  • Public  → <code>t.me/groupname</code>\n"
        f"  • Private → <code>t.me/+invitehash</code>\n\n"
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
            f"📥 <b>Step 2/7</b> — Send <b>MESSAGE LINK</b>:\n"
            f"  • <code>t.me/groupname/123</code>\n"
            f"  • <code>t.me/c/1234567890/123</code>",
            parse_mode="HTML")
    else:
        await update.message.reply_text(f"🔄 Joining private group...\n<code>{link}</code>", parse_mode="HTML")
        ok, fail = await join_group_all(ident, ltype)
        if ok == 0:
            await update.message.reply_text("❌ No accounts could join! Check link/invite."); return ConversationHandler.END
        await update.message.reply_text(
            f"✅ Join complete!\n✅ {ok} | ❌ {fail}\n\n"
            f"📥 <b>Step 2/7</b> — Send <b>MESSAGE LINK</b>:", parse_mode="HTML")
    return MSG_LINK

async def receive_msg_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, msg_id, err = parse_message_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return MSG_LINK
    ctx.user_data.update({"msg_ident": ident, "msg_id": msg_id, "msg_link": link})
    add_log(f"📥 Message: {link} (ID:{msg_id})")
    await update.message.reply_text(
        "📋 <b>Step 3/7</b> — Select report reason:",
        reply_markup=_build_full_cat_keyboard("CAT"),
        parse_mode="HTML")
    return REASON_CAT

async def category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2:
        return REASON_CAT
    cat_key = parts[1]
    if cat_key == "__back__":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    if cat_key not in FULL_REPORT_CATEGORIES:
        return REASON_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data.update({
        "cat_key": cat_key,
        "cat_label": f"{cat['emoji']} {cat['label']}",
        "api_reason": cat["api"],
    })
    add_log(f"📥 Category: {cat['label']}")

    if cat.get("direct"):
        ctx.user_data["sub_label"] = "—"
        if cat_key == "dont_like":
            # No message field per Telegram UI
            ctx.user_data["custom_msg"] = ""
            await query.edit_message_text(
                f"✅ {cat['emoji']} {cat['label']}\n\n"
                f"🔢 <b>Step 6/7</b> — Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
                parse_mode="HTML")
            return COUNT
        await query.edit_message_text(
            f"✅ {cat['emoji']} {cat['label']}\n\n"
            f"📝 <b>Step 5/7</b> — Optional message or <code>skip</code>:",
            parse_mode="HTML")
        return CUSTOM_MSG

    # Has subcategories
    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']}\n\n"
        f"📋 <b>Step 4/7</b> — Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "SUB"),
        parse_mode="HTML")
    return REASON_SUB

async def subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "__back__":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    if len(parts) < 3:
        return REASON_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat or not cat["subs"]: return REASON_SUB
    sub_label = next((lbl for k, lbl in cat["subs"] if k == sub_key), "—")
    ctx.user_data["sub_label"] = sub_label
    add_log(f"📥 Sub-category: {sub_label}")
    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']} → <b>{sub_label}</b>\n\n"
        f"📝 <b>Step 5/7</b> — Optional message or <code>skip</code>:",
        parse_mode="HTML")
    return CUSTOM_MSG

async def receive_custom_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip": text = ""
    ctx.user_data["custom_msg"] = text
    add_log(f"📥 Custom msg: {(text[:40] or '(pool)')}")
    await update.message.reply_text(
        f"✅ Saved!\n\n🔢 <b>Step 6/7</b> — Reports per account?\n\n"
        f"💡 1–2 = ✅ Safe | 3–10 = ⚠️ Moderate | 10+ = 🚨 Aggressive\n\n"
        f"Enter 1–{MAX_REPORTS_PER_ACCOUNT}:", parse_mode="HTML")
    return COUNT

async def report_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT: raise ValueError
    except ValueError:
        await update.message.reply_text(f"❌ Invalid! Enter 1–{MAX_REPORTS_PER_ACCOUNT}:"); return COUNT
    ident       = ctx.user_data["msg_ident"]
    msg_id      = ctx.user_data["msg_id"]
    msg_link    = ctx.user_data.get("msg_link","")
    link_type   = ctx.user_data.get("grp_type", "username")
    reason_api  = ctx.user_data["api_reason"]
    custom_msg  = ctx.user_data.get("custom_msg","")
    cat_lbl     = ctx.user_data["cat_label"]
    sub_lbl     = ctx.user_data.get("sub_label","—")
    join_note   = "Public — direct report" if link_type == "username" else "Private — joined first"

    # Only authorized clients
    auth_pairs = []
    for phone, client in accounts.items():
        try:
            if await client.is_user_authorized():
                auth_pairs.append((phone, client))
        except: pass

    if not auth_pairs:
        await update.message.reply_text("⚠️ No authorized accounts."); return ConversationHandler.END

    total_planned = len(auth_pairs) * count
    report_stats["total"] = total_planned
    report_stats["start_time"] = datetime.now()

    await update.message.reply_text(
        f"🚀 <b>REPORTING STARTED (ROUND-ROBIN)</b> — Step 7/7\n\n"
        f"📊 Total: {total_planned}\n"
        f"📱 Accounts: {len(auth_pairs)} × {count}\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
        f"🔁 Pattern: acc1→acc2→...→accN→acc1→... (×{count} rounds)\n"
        f"🌐 {join_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━", parse_mode="HTML")

    # 🔁 ROUND-ROBIN: outer loop = round (0..count-1), inner = each account once
    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, client) in enumerate(auth_pairs):
            shot_num += 1
            ok, status = await send_report(
                client, ident, msg_id, reason_api, custom_msg,
                phone, link_type, sub_lbl)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1; update_stats(True)
                log_report_file(phone, msg_id, f"{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ {shot_num}/{total_planned} | R{r+1} | 📱 <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1; update_stats(False)
                log_report_file(phone, msg_id, f"{cat_lbl}/{sub_lbl}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ {shot_num}/{total_planned} | R{r+1} | 📱 <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
                if "FloodWait" in status:
                    try:
                        wait = int(status.split()[1].replace("s",""))
                        await update.message.reply_text(f"⏳ FloodWait {wait}s — waiting...")
                        await asyncio.sleep(min(wait + 2, 300))
                    except: await asyncio.sleep(60)
            # short delay between accounts within a round
            if acc_idx < len(auth_pairs) - 1:
                await asyncio.sleep(round_robin_delay())
        # bigger delay between rounds
        if r < count - 1:
            d = account_switch_delay()
            add_log(f"🔄 Round {r+1}/{count} done — sleeping {d:.1f}s before next round")
            await asyncio.sleep(d)

    elapsed = (datetime.now() - report_stats["start_time"]).seconds if report_stats["start_time"] else 0
    rate = (total_ok / total_planned) * 100 if total_planned > 0 else 0
    add_log(f"🎉 Done: {total_ok}/{total_planned} ({rate:.1f}%)")

    breakdown = "\n".join(
        f"  📱 <code>{p[-4:]}</code> → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Gmail Blast (next)", callback_data="GMAIL_START")],
        [InlineKeyboardButton("🏠 Done",               callback_data="GMAIL_SKIP")]])
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>REPORTING COMPLETE</b>\n\n"
        f"✅ Success: {total_ok}\n"
        f"❌ Failed: {total_fail}\n"
        f"📈 Rate: {rate:.1f}%\n"
        f"⏱ Time: {elapsed//60}m {elapsed%60}s\n\n"
        f"<b>Per-account breakdown:</b>\n{breakdown}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
        f"🔗 {msg_link}\n\n"
        f"📧 Want to also blast Gmail?",
        reply_markup=keyboard, parse_mode="HTML")
    return MAIL_SUBJECT

# ══════════════════════════════════════════════════════════════════════
# 📸 PFP REPORT FLOW (unchanged behavior, round-robin added)
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
        f"✅ Active: {active}/{len(accounts)}\n"
        f"💀 Uses 6 methods + fallbacks\n\n"
        f"👤 Enter @username or user ID:\n/cancel to abort.",
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
        f"\n🆔 <code>{uid}</code>\n📸 Photos: {len(photos)}\n\n📋 Select reason:",
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
        f"✅ {label}\n👤 {dname}\n\n🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):", parse_mode="HTML")
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
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT: raise ValueError
    except ValueError:
        await update.message.reply_text(f"❌ Invalid! Enter 1–{MAX_REPORTS_PER_ACCOUNT}:"); return AR_COUNT
    target_raw    = ctx.user_data["ar_entity_id"]
    target_name   = ctx.user_data.get("ar_name", target_raw)
    reason_label  = ctx.user_data["ar_reason_label"]
    reason_api    = ctx.user_data["ar_reason_api"]
    custom_msg    = ctx.user_data.get("ar_custom_msg","")

    auth_pairs = []
    for phone, client in accounts.items():
        try:
            if await client.is_user_authorized():
                auth_pairs.append((phone, client))
        except: pass

    if not auth_pairs:
        await update.message.reply_text("⚠️ No authorized accounts."); return ConversationHandler.END

    total_reports = len(auth_pairs) * count
    await update.message.reply_text(
        f"🚀 <b>NUCLEAR PFP REPORT (ROUND-ROBIN)</b>\n👤 {target_name}\n⚠️ {reason_label}\n"
        f"📊 {total_reports} total ({len(auth_pairs)} × {count})\n"
        f"🔁 Pattern: acc1→acc2→...→accN→acc1→...\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    # Pre-resolve entity + photos per account
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
            await update.message.reply_text(f"❌ <code>{phone[-4:]}</code>: Resolve — {str(e)[:40]}", parse_mode="HTML")
            resolved[phone] = (None, [])

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, client) in enumerate(auth_pairs):
            shot_num += 1
            ent, photos = resolved.get(phone, (None, []))
            if ent is None:
                total_fail += 1; per_acc_fail[phone] += 1
                await update.message.reply_text(
                    f"❌ PFP {shot_num}/{total_reports} | R{r+1} | 📱 <code>{phone[-4:]}</code> → resolve failed",
                    parse_mode="HTML")
                continue
            ok, status = await report_profile_photo_nuclear(client, ent, photos, reason_api, custom_msg, phone)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ PFP {shot_num}/{total_reports} | R{r+1} | 📱 <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ PFP {shot_num}/{total_reports} | R{r+1} | 📱 <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
                if "FloodWait" in status:
                    try:
                        wait = int(status.split()[1].replace("s",""))
                        await asyncio.sleep(min(wait + 2, 300))
                    except: await asyncio.sleep(60)
            if acc_idx < len(auth_pairs) - 1:
                await asyncio.sleep(round_robin_delay())
        if r < count - 1:
            await asyncio.sleep(account_switch_delay())

    rate = (total_ok / total_reports) * 100 if total_reports > 0 else 0
    add_log(f"🎉 PFP done: {total_ok}/{total_reports} ({rate:.1f}%)")
    breakdown = "\n".join(
        f"  📱 <code>{p[-4:]}</code> → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>PFP COMPLETE</b>\n\n"
        f"👤 {target_name}\n⚠️ {reason_label}\n"
        f"✅ {total_ok} | ❌ {total_fail} | 📈 {rate:.1f}%\n\n"
        f"<b>Per-account:</b>\n{breakdown}\n\n"
        f"Use /accountreport for another target.",
        parse_mode="HTML")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 🤖 BOT REPORT FLOW — now uses FULL Telegram report categories (3-dots → Report)
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
        f"🤖 <b>BOT REPORT</b> (3-dots → Report style)\n━━━━━━━━━━━━━━━━\n\n"
        f"✅ Active: {active}/{len(accounts)}\n"
        f"💀 Full Telegram report category tree (same as message report)\n"
        f"🔁 Round-robin: acc1→acc2→acc3→acc1→...\n\n"
        f"🤖 Enter <b>@bot_username</b> (must end with <code>bot</code>):\n"
        f"/cancel to abort.",
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
    ctx.user_data.update({
        "br_uid": uid, "br_name": dname, "br_uname": uname,
        "br_entity_id": raw,
    })
    await wait_msg.edit_text(
        f"✅ Found bot!\n🤖 <b>{dname}</b>" +
        (f" (@{uname})" if uname else "") +
        f"\n🆔 <code>{uid}</code>\n\n📋 Select report reason:",
        reply_markup=_build_full_cat_keyboard("BCAT"), parse_mode="HTML")
    return BR_CAT

async def br_category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2: return BR_CAT
    cat_key = parts[1]
    if cat_key == "__back__":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("BCAT"))
        return BR_CAT
    if cat_key not in FULL_REPORT_CATEGORIES:
        return BR_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data.update({
        "br_cat_key": cat_key,
        "br_cat_label": f"{cat['emoji']} {cat['label']}",
        "br_reason_api": cat["api"],
    })
    add_log(f"🤖 BotReport Category: {cat['label']}")

    if cat.get("direct"):
        ctx.user_data["br_sub_label"] = "—"
        if cat_key == "dont_like":
            ctx.user_data["br_custom_msg"] = ""
            await query.edit_message_text(
                f"✅ {cat['emoji']} {cat['label']}\n\n"
                f"🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
                parse_mode="HTML")
            return BR_COUNT
        await query.edit_message_text(
            f"✅ {cat['emoji']} {cat['label']}\n\n"
            f"📝 Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return BR_MSG

    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']}\n\n📋 Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "BSUB"),
        parse_mode="HTML")
    return BR_SUB

async def br_subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "__back__":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("BCAT"))
        return BR_CAT
    if len(parts) < 3:
        return BR_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat or not cat["subs"]: return BR_SUB
    sub_label = next((lbl for k, lbl in cat["subs"] if k == sub_key), "—")
    ctx.user_data["br_sub_label"] = sub_label
    add_log(f"🤖 BotReport Sub: {sub_label}")
    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']} → <b>{sub_label}</b>\n\n"
        f"📝 Optional message or send <code>skip</code>:",
        parse_mode="HTML")
    return BR_MSG

async def br_receive_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() in ("skip", "/skip"): text = ""
    ctx.user_data["br_custom_msg"] = text
    await update.message.reply_text(
        f"✅ Saved!\n🔢 Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
        parse_mode="HTML")
    return BR_COUNT

async def br_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT: raise ValueError
    except ValueError:
        await update.message.reply_text(f"❌ Invalid! Enter 1–{MAX_REPORTS_PER_ACCOUNT}:"); return BR_COUNT

    target_raw   = ctx.user_data["br_entity_id"]
    target_name  = ctx.user_data["br_name"]
    cat_label    = ctx.user_data["br_cat_label"]
    sub_label    = ctx.user_data.get("br_sub_label", "—")
    reason_api   = ctx.user_data["br_reason_api"]
    custom_msg   = ctx.user_data.get("br_custom_msg", "")

    auth_pairs = []
    for phone, client in accounts.items():
        try:
            if await client.is_user_authorized():
                auth_pairs.append((phone, client))
        except: pass

    if not auth_pairs:
        await update.message.reply_text("⚠️ No authorized accounts."); return ConversationHandler.END

    total = len(auth_pairs) * count
    await update.message.reply_text(
        f"🚀 <b>BOT REPORT STARTING (ROUND-ROBIN)</b>\n"
        f"🤖 {target_name}\n"
        f"⚠️ {cat_label} → {sub_label}\n"
        f"📊 {total} total ({len(auth_pairs)} × {count})\n"
        f"🔁 Pattern: acc1→acc2→...→accN→acc1→...\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    # Pre-resolve bot entity per account
    resolved: Dict[str, object] = {}
    for phone, client in auth_pairs:
        try:
            identifier = target_raw.lstrip("@")
            ent = await client.get_entity(identifier)
            resolved[phone] = ent
        except Exception as e:
            await update.message.reply_text(f"❌ <code>{phone[-4:]}</code>: Resolve — {str(e)[:40]}", parse_mode="HTML")
            resolved[phone] = None

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, client) in enumerate(auth_pairs):
            shot_num += 1
            bot_entity = resolved.get(phone)
            if bot_entity is None:
                total_fail += 1; per_acc_fail[phone] += 1
                await update.message.reply_text(
                    f"❌ BOT {shot_num}/{total} | R{r+1} | 📱 <code>{phone[-4:]}</code> → resolve failed",
                    parse_mode="HTML")
                continue
            ok, status = await _report_bot_methods(client, bot_entity, reason_api, custom_msg, phone, sub_label)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ BOT {shot_num}/{total} | R{r+1} | 📱 <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ BOT {shot_num}/{total} | R{r+1} | 📱 <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
                if "FloodWait" in status:
                    try:
                        wait = int(status.split()[1].replace("s",""))
                        await asyncio.sleep(min(wait + 2, 300))
                    except: await asyncio.sleep(60)
            if acc_idx < len(auth_pairs) - 1:
                await asyncio.sleep(round_robin_delay())
        if r < count - 1:
            await asyncio.sleep(account_switch_delay())

    rate = (total_ok / total) * 100 if total > 0 else 0
    add_log(f"🎉 BOT report done: {total_ok}/{total} ({rate:.1f}%)")
    breakdown = "\n".join(
        f"  📱 <code>{p[-4:]}</code> → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>BOT REPORT COMPLETE</b>\n\n"
        f"🤖 {target_name}\n⚠️ {cat_label} → {sub_label}\n"
        f"✅ {total_ok} | ❌ {total_fail} | 📈 {rate:.1f}%\n\n"
        f"<b>Per-account:</b>\n{breakdown}",
        parse_mode="HTML")
    return ConversationHandler.END

async def _report_bot_methods(client, bot_entity, reason_api, custom_msg, phone, sub_label="") -> Tuple[bool, str]:
    proxy = account_proxy_map.get(phone)
    methods_tried = []

    # M1: account.ReportPeer (this is what 3-dots → Report effectively triggers)
    try:
        await asyncio.sleep(random.uniform(0.3, 1.0))
        r = await client(functions.account.ReportPeerRequest(
            peer=bot_entity, reason=reason_api,
            message=craft_report_message(custom_msg, sub_label)))
        if r:
            mark_proxy_result(proxy, True)
            return (True, "Success (M1: ReportPeer)")
        methods_tried.append("M1")
    except errors.FloodWaitError as e:
        return (False, f"FloodWait {e.seconds}s")
    except Exception as e:
        methods_tried.append(f"M1-{type(e).__name__}")

    # M2: messages.ReportSpam (legacy spam button)
    try:
        await asyncio.sleep(random.uniform(0.4, 1.0))
        r = await client(functions.messages.ReportSpamRequest(peer=bot_entity))
        if r:
            mark_proxy_result(proxy, True)
            return (True, "Success (M2: ReportSpam)")
        methods_tried.append("M2")
    except Exception as e:
        methods_tried.append(f"M2-{type(e).__name__}")

    # M3: report bot's own message
    try:
        await asyncio.sleep(random.uniform(0.5, 1.2))
        msgs = await client.get_messages(bot_entity, limit=1)
        if msgs and msgs[0]:
            r = await client(functions.messages.ReportRequest(
                peer=bot_entity, id=[msgs[0].id], reason=reason_api,
                message=craft_report_message(custom_msg, sub_label)))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "Success (M3: report bot msg)")
        methods_tried.append("M3")
    except Exception as e:
        methods_tried.append(f"M3-{type(e).__name__}")

    # M4: report bot's profile photo
    try:
        await asyncio.sleep(random.uniform(0.4, 1.0))
        photos = await client.get_profile_photos(bot_entity)
        if photos:
            ph = photos[0]
            ip = tl_types.InputPhoto(id=ph.id, access_hash=ph.access_hash, file_reference=ph.file_reference)
            r = await client(functions.account.ReportProfilePhotoRequest(
                peer=bot_entity, photo_id=ip,
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "Success (M4: bot PFP)")
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
            "📧 <b>Gmail BLAST</b> — Step 1/5\n\n"
            "All Gmail accounts will fire simultaneously per round.\n\n"
            "✏️ Enter <b>Email Subject</b>:", parse_mode="HTML")
    else:
        ctx.user_data.clear()
        await update.message.reply_text(
            "📧 <b>Gmail BLAST Mode</b> — Step 1/5\n\n"
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
        if not 1 <= count <= 50: raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid! Enter 1–50:"); return MAIL_BLAST_COUNT
    ctx.user_data["mail_blast_count"] = count
    recipient = ctx.user_data["mail_recipient"]
    await update.message.reply_text(
        f"🚀 <b>BLAST STARTING</b>\n\n"
        f"📬 Recipient: <code>{recipient}</code>\n"
        f"🔁 Rounds: {count}\n"
        f"📧 Accounts/round: {len(GMAIL_ACCOUNTS)}\n"
        f"📊 Total emails: {count * len(GMAIL_ACCOUNTS)}\n\n"
        f"⏳ Firing now...", parse_mode="HTML")
    total_ok, total_fail, details = await do_gmail_blast_n_times(ctx, count, update_msg=update.message)
    summary = (
        f"📬 <b>BLAST COMPLETE</b> → <code>{recipient}</code>\n\n"
        f"✅ Sent: {total_ok}\n"
        f"❌ Failed: {total_fail}\n"
        f"📊 Total attempts: {count * len(GMAIL_ACCOUNTS)}\n")
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
        f"✅ {total_ok} | ❌ {total_fail} | 📊 {count*len(GMAIL_ACCOUNTS)}\n")
    if len(details) > 3500: details = details[:3500] + "\n...(truncated)"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Blast Again", callback_data="RESEND"),
        InlineKeyboardButton("✅ Done",         callback_data="DONE")]])
    await query.edit_message_text(summary + "\n" + details, reply_markup=keyboard, parse_mode="HTML")
    return MAIL_RESEND

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
            GRP_LINK:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grp_link)],
            MSG_LINK:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_msg_link)],
            REASON_CAT: [CallbackQueryHandler(category_selected, pattern="^CAT\\|")],
            REASON_SUB: [CallbackQueryHandler(subcategory_selected, pattern="^SUB\\|")],
            CUSTOM_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_msg)],
            COUNT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, report_execute)],
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
    app.add_handler(gmail_conv)
    app.add_handler(CallbackQueryHandler(menu_router, pattern="^MENU\\|"))

    logger.info(f"⚡ ULTIMATE REPORTER v{BOT_VERSION} — RUNNING")
    add_log(f"⚡ Bot v{BOT_VERSION} online (proxy={'ON' if PROXY_ENABLED else 'OFF'})")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
