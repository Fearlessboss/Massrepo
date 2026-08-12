"""
╔══════════════════════════════════════════════════════════════════════╗
║   ⚡ ULTIMATE TELEGRAM REPORTER v16.0 — MONGO + MULTI-USER ELITE++ ⚡ ║
║──────────────────────────────────────────────────────────────────────║
║   ✅ MongoDB persistence (sessions, sudo, gmails, proxy_health)      ║
║   ✅ /addmail (owner only) — add gmail accounts dynamically          ║
║   ✅ /groupreport now supports MULTIPLE msg links + skip             ║
║   ✅ POWERFUL multi-paragraph report messages (faster + stronger)    ║
║   ✅ Per-user concurrent flows — multi-user safe, no global locks    ║
║   ✅ Each session randomized device model (looks like diff devices)  ║
║   ✅ Telegram-accurate report category tree (exact official options) ║
║   ✅ Full backward feature parity with v15                           ║
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

# MongoDB
from pymongo import MongoClient
from pymongo.errors import PyMongoError

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
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID    = 33628258
API_HASH  = "0850762925b9c1715b9b122f7b753128"
OWNER_ID  = 6980326908

MONGO_URL = "mongodb+srv://moderatorhelperorg_db_user:nze86usap2dYthZN@cluster0.uokrixs.mongodb.net/mydatabase?retryWrites=true&w=majority"
MONGO_DB_NAME = "mydatabase"

MAX_REPORTS_PER_ACCOUNT = 100
MAX_MSG_LINKS           = 50
BOT_VERSION             = "16.0"

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
# 📁 PATHS
# ══════════════════════════════════════════════════════════════════════
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# 🎨 ANSI COLORS + LOGGING
# ══════════════════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; MAGENTA = "\033[95m"; CYAN = "\033[96m"; WHITE = "\033[97m"
    BG_RED = "\033[41m"; BG_GRN = "\033[42m"

def print_banner():
    # os.system("cls" if os.name == "nt" else "clear")   # ← Yeh comment kar do
    print(f"{C.CYAN}{C.BOLD}")
    print(f"  ⚡ Ultimate Reporter v{BOT_VERSION} — running...{C.RESET}")
    print(f"{C.DIM}  Proxy mode: {'ON' if PROXY_ENABLED else 'OFF (direct)'}{C.RESET}\n")

class ColorFormatter(logging.Formatter):
    COLORS = {"DEBUG": C.DIM + C.WHITE, "INFO": C.CYAN, "WARNING": C.YELLOW,
              "ERROR": C.RED, "CRITICAL": C.BG_RED + C.WHITE}
    def format(self, record):
        col = self.COLORS.get(record.levelname, C.WHITE)
        ts  = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        lvl = f"{col}{record.levelname:<7}{C.RESET}"
        return f"{C.DIM}[{ts}]{C.RESET} {lvl} {record.getMessage()}"

# Logging setup
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)  # force=True added
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# 🗂 GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════
accounts: Dict[str, TelegramClient] = {}
account_proxy_map: Dict[str, dict] = {}
account_device_map: Dict[str, dict] = {}  # per-account device fingerprint
sudo_users: set = set()
sudo_info: Dict[int, dict] = {}
GMAIL_ACCOUNTS: List[dict] = []
proxy_health: Dict[str, dict] = {}
proxy_cursor = 0

live_logs: List[str] = []
# Per-user stats (multi-user safe). report_stats[user_id] = {...}
report_stats: Dict[int, dict] = {}

# Per-user locks so one user's heavy job doesn't block another user
user_locks: Dict[int, asyncio.Lock] = {}

def get_user_lock(uid: int) -> asyncio.Lock:
    lk = user_locks.get(uid)
    if lk is None:
        lk = asyncio.Lock()
        user_locks[uid] = lk
    return lk

# ══════════════════════════════════════════════════════════════════════
# 📦 MONGO LAYER
# ══════════════════════════════════════════════════════════════════════
mongo_client: Optional[MongoClient] = None
db = None

def mongo_init():
    global mongo_client, db
    try:
        mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=15000)
        # ping
        mongo_client.admin.command("ping")
        db = mongo_client[MONGO_DB_NAME]
        # indexes
        db.accounts.create_index("phone", unique=True)
        db.sudo.create_index("user_id", unique=True)
        db.gmails.create_index("email", unique=True)
        db.proxy_health.create_index("key", unique=True)
        db.devices.create_index("phone", unique=True)
        logger.info(f"{C.GREEN}✅ MongoDB connected → {MONGO_DB_NAME}{C.RESET}")
        return True
    except Exception as e:
        logger.error(f"{C.RED}❌ MongoDB connect FAIL: {e}{C.RESET}")
        return False

# ----- accounts -----
def db_save_account(phone: str, session_str: str):
    try:
        db.accounts.update_one(
            {"phone": phone},
            {"$set": {"phone": phone, "session": session_str,
                      "updated": datetime.utcnow()}},
            upsert=True)
    except PyMongoError as e:
        logger.error(f"db_save_account fail: {e}")

def db_remove_account(phone: str):
    try:
        db.accounts.delete_one({"phone": phone})
        db.devices.delete_one({"phone": phone})
    except PyMongoError as e:
        logger.error(f"db_remove_account fail: {e}")

def db_load_accounts() -> Dict[str, str]:
    out = {}
    try:
        for doc in db.accounts.find({}):
            out[doc["phone"]] = doc.get("session", "")
    except PyMongoError as e:
        logger.error(f"db_load_accounts fail: {e}")
    return out

# ----- devices (per-account fingerprint so each looks different) -----
DEVICE_POOL = [
    {"device_model": "iPhone 14 Pro",       "system_version": "iOS 16.5", "app_version": "9.6.3"},
    {"device_model": "iPhone 13",           "system_version": "iOS 16.2", "app_version": "9.5.7"},
    {"device_model": "iPhone 15",           "system_version": "iOS 17.1", "app_version": "10.1.2"},
    {"device_model": "iPhone 12 Pro Max",   "system_version": "iOS 15.7", "app_version": "9.2.1"},
    {"device_model": "Samsung Galaxy S23",  "system_version": "Android 13","app_version": "10.0.8"},
    {"device_model": "Samsung Galaxy S22",  "system_version": "Android 12","app_version": "9.7.5"},
    {"device_model": "Pixel 7 Pro",         "system_version": "Android 13","app_version": "10.2.0"},
    {"device_model": "Pixel 8",             "system_version": "Android 14","app_version": "10.3.1"},
    {"device_model": "OnePlus 11",          "system_version": "Android 13","app_version": "10.1.0"},
    {"device_model": "Xiaomi Mi 13",        "system_version": "Android 13","app_version": "9.8.2"},
    {"device_model": "Redmi Note 12",       "system_version": "Android 12","app_version": "9.6.0"},
    {"device_model": "Realme GT Neo 5",     "system_version": "Android 13","app_version": "10.0.5"},
    {"device_model": "MacBook Pro M2",      "system_version": "macOS 14.1","app_version": "10.4.0"},
    {"device_model": "PC 64bit",            "system_version": "Windows 11","app_version": "4.14.5 x64"},
    {"device_model": "PC 64bit",            "system_version": "Windows 10","app_version": "4.12.2 x64"},
]

def get_or_assign_device(phone: str) -> dict:
    if phone in account_device_map:
        return account_device_map[phone]
    try:
        doc = db.devices.find_one({"phone": phone})
        if doc and "device" in doc:
            account_device_map[phone] = doc["device"]
            return doc["device"]
    except Exception:
        pass
    dev = random.choice(DEVICE_POOL).copy()
    account_device_map[phone] = dev
    try:
        db.devices.update_one(
            {"phone": phone},
            {"$set": {"phone": phone, "device": dev, "updated": datetime.utcnow()}},
            upsert=True)
    except Exception as e:
        logger.error(f"save device fail: {e}")
    return dev

# ----- sudo -----
def db_load_sudo():
    global sudo_users, sudo_info
    sudo_users = set(); sudo_info = {}
    try:
        for doc in db.sudo.find({}):
            uid = int(doc["user_id"])
            sudo_users.add(uid)
            sudo_info[uid] = {
                "name": doc.get("name", str(uid)),
                "username": doc.get("username", ""),
                "added": doc.get("added", ""),
            }
    except PyMongoError as e:
        logger.error(f"db_load_sudo fail: {e}")

def db_add_sudo(uid: int, name: str, username: str = ""):
    try:
        db.sudo.update_one(
            {"user_id": uid},
            {"$set": {"user_id": uid, "name": name, "username": username,
                      "added": datetime.utcnow().isoformat()}},
            upsert=True)
    except PyMongoError as e:
        logger.error(f"db_add_sudo fail: {e}")

def db_remove_sudo(uid: int):
    try:
        db.sudo.delete_one({"user_id": uid})
    except PyMongoError as e:
        logger.error(f"db_remove_sudo fail: {e}")

# ----- gmails -----
DEFAULT_GMAILS = [
    {"email": "deviramrani489@gmail.com",      "password": "eprrbxhaibzwwhqv", "name": "Devi Ramrani"},
    {"email": "fearlessaditya322@gmail.com",   "password": "kmbpigpqrmlgyala", "name": "Aditya Mishra"},
    {"email": "moderatorhelper.org@gmail.com", "password": "loanhgpmocqmwbka", "name": "Moderator Helper"},
    {"email": "helpingpeople.or@gmail.com",    "password": "qpgoyrpuyesdxfnj", "name": "Community Support"},
]

def db_load_gmails():
    global GMAIL_ACCOUNTS
    GMAIL_ACCOUNTS = []
    try:
        for doc in db.gmails.find({}):
            GMAIL_ACCOUNTS.append({
                "email": doc["email"],
                "password": doc["password"],
                "name": doc.get("name", doc["email"].split("@")[0]),
            })
        if not GMAIL_ACCOUNTS:
            # seed defaults so blast still works out of box
            for g in DEFAULT_GMAILS:
                db.gmails.update_one(
                    {"email": g["email"]},
                    {"$set": g}, upsert=True)
            GMAIL_ACCOUNTS = list(DEFAULT_GMAILS)
    except PyMongoError as e:
        logger.error(f"db_load_gmails fail: {e}")
        GMAIL_ACCOUNTS = list(DEFAULT_GMAILS)

def db_add_gmail(email: str, password: str, name: str = "") -> bool:
    try:
        db.gmails.update_one(
            {"email": email},
            {"$set": {"email": email, "password": password,
                      "name": name or email.split("@")[0],
                      "added": datetime.utcnow()}},
            upsert=True)
        return True
    except PyMongoError as e:
        logger.error(f"db_add_gmail fail: {e}")
        return False

def db_remove_gmail(email: str) -> bool:
    try:
        res = db.gmails.delete_one({"email": email})
        return res.deleted_count > 0
    except PyMongoError as e:
        logger.error(f"db_remove_gmail fail: {e}")
        return False

# ----- proxy health -----
def db_load_proxy_health():
    global proxy_health
    proxy_health = {}
    try:
        for doc in db.proxy_health.find({}):
            proxy_health[doc["key"]] = {
                "ok": doc.get("ok", 0),
                "fail": doc.get("fail", 0),
                "bad": doc.get("bad", False),
            }
    except PyMongoError as e:
        logger.error(f"db_load_proxy_health fail: {e}")

def db_save_proxy_health_entry(key: str, h: dict):
    try:
        db.proxy_health.update_one(
            {"key": key},
            {"$set": {"key": key, **h, "updated": datetime.utcnow()}},
            upsert=True)
    except PyMongoError as e:
        logger.error(f"db_save_proxy_health_entry fail: {e}")

# ══════════════════════════════════════════════════════════════════════
# 🔐 AUTHZ
# ══════════════════════════════════════════════════════════════════════
def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in sudo_users

# ══════════════════════════════════════════════════════════════════════
# 🌐 PROXY HEALTH HELPERS
# ══════════════════════════════════════════════════════════════════════
def _proxy_key(p: dict) -> str:
    return f"{p.get('type','?')}://{p.get('addr','?')}:{p.get('port','?')}"

def mark_proxy_result(proxy: Optional[dict], success: bool):
    if not proxy: return
    k = _proxy_key(proxy)
    h = proxy_health.setdefault(k, {"ok": 0, "fail": 0, "bad": False})
    if success: h["ok"] += 1
    else:       h["fail"] += 1
    total = h["ok"] + h["fail"]
    if total >= 3 and h["fail"] / total > 0.7:
        h["bad"] = True
    db_save_proxy_health_entry(k, h)

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
# 📊 LOGS + STATS (per-user)
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

def _stats_for(uid: int) -> dict:
    s = report_stats.get(uid)
    if s is None:
        s = {"total": 0, "success": 0, "failed": 0, "start_time": None}
        report_stats[uid] = s
    return s

def update_stats(uid: int, success: bool):
    s = _stats_for(uid)
    if success: s["success"] += 1
    else:       s["failed"]  += 1

def reset_stats(uid: int):
    report_stats[uid] = {"total": 0, "success": 0, "failed": 0, "start_time": None}

def get_stats(uid: int) -> str:
    s = _stats_for(uid)
    elapsed = ""
    if s["start_time"]:
        sec = (datetime.now() - s["start_time"]).seconds
        elapsed = f" | ⏱ {sec//60}m {sec%60}s"
    tot = s["success"] + s["failed"]
    return (f"📊 {tot}/{s['total']} | ✅ {s['success']} | ❌ {s['failed']}{elapsed}")

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
# 🧠 REPORT MESSAGE POOL (POWERFUL, MULTI-PARAGRAPH)
# ══════════════════════════════════════════════════════════════════════
REPORT_PREFIXES = [
    "Hello Telegram Moderation Team,",
    "Dear Telegram Team,",
    "To the Telegram Safety Team,",
    "Urgent: Telegram Moderators,",
    "Telegram Trust & Safety,",
]

CONTEXT_PHRASES = [
    "This content is a clear and repeated violation of Telegram's Terms of Service and community guidelines.",
    "This is a serious, ongoing violation that endangers other users and undermines Telegram's safety.",
    "This account/chat has been engaging in abusive behavior over a sustained period and must be removed.",
    "Multiple users have witnessed this behavior; immediate moderation is required to prevent further harm.",
    "This violates Telegram's policies on harmful, illegal and abusive content and must be acted on urgently.",
]

REALISTIC_REPORT_MSGS = [
    "The targeted content/account is harming users and must be removed under Telegram's official policies.",
    "Please review the attached references — the violation is unmistakable and ongoing.",
    "This activity is causing direct harm to victims and to the platform's reputation; please act fast.",
    "Reporting on behalf of affected community members. Evidence is consistent across multiple sightings.",
    "This is not a minor issue — it is a sustained pattern of policy-breaking content, please escalate.",
    "The behavior is repeated, deliberate, and clearly violates Telegram's published rules.",
    "Strongly requesting removal under your harmful-content policy. Multiple reports have been filed.",
]

def craft_report_message(base_msg: str, sub_label: str = "") -> str:
    """Build a powerful, multi-paragraph contextual report message."""
    pool_msg = random.choice(REALISTIC_REPORT_MSGS)
    prefix   = random.choice(REPORT_PREFIXES)
    context  = random.choice(CONTEXT_PHRASES)

    parts = [prefix]
    if sub_label and sub_label not in ("N/A", ""):
        parts.append(f"Reported category: {sub_label}.")

    if base_msg and base_msg.strip() and base_msg.strip().lower() not in ("skip", "default", ""):
        roll = random.random()
        if roll < 0.5:
            parts.append(base_msg.strip())
            parts.append(context)
        else:
            parts.append(context)
            parts.append(base_msg.strip())
        parts.append(pool_msg)
    else:
        parts.append(context)
        parts.append(pool_msg)

    parts.append("Requesting urgent moderation action. Thank you for protecting the community.")
    final = " ".join(parts)
    if len(final) > 480:
        final = final[:477] + "..."
    return final

# ══════════════════════════════════════════════════════════════════════
# 📋 TELEGRAM-ACCURATE REPORT CATEGORIES (matches official UI)
# ══════════════════════════════════════════════════════════════════════
# Maps to Telethon InputReportReason* enums
FULL_REPORT_CATEGORIES = {
    "dontlike": {
        "emoji": "👎", "label": "I don't like it",
        "api": types.InputReportReasonOther(),
        "subs": [],  # direct
    },
    "child_abuse": {
        "emoji": "👶", "label": "Child abuse",
        "api": types.InputReportReasonChildAbuse(),
        "subs": [
            ("csa", "Child sexual abuse"),
            ("cpa", "Child physical abuse"),
        ],
    },
    "violence": {
        "emoji": "🔪", "label": "Violence",
        "api": types.InputReportReasonViolence(),
        "subs": [
            ("vio_insults",   "Insults or false information"),
            ("vio_graphic",   "Graphic or disturbing content"),
            ("vio_extreme",   "Extreme violence, dismemberment"),
            ("vio_hate",      "Hate speech or symbols"),
            ("vio_call",      "Calling for violence"),
            ("vio_org",       "Organized crime"),
            ("vio_terror",    "Terrorism"),
            ("vio_animal",    "Animal abuse"),
        ],
    },
    "illegal_goods": {
        "emoji": "🛒", "label": "Illegal goods and services",
        "api": types.InputReportReasonIllegalDrugs(),
        "subs": [
            ("ig_weapons",   "Weapons"),
            ("ig_drugs",     "Drugs"),
            ("ig_fake_docs", "Fake documents"),
            ("ig_counter_money", "Counterfeit money"),
            ("ig_hacking",   "Hacking tools and malware"),
            ("ig_counter_merch", "Counterfeit merchandise"),
            ("ig_other",     "Other goods and services"),
        ],
    },
    "illegal_adult": {
        "emoji": "🔞", "label": "Illegal adult content",
        "api": types.InputReportReasonPornography(),
        "subs": [
            ("ia_child",     "Child abuse"),
            ("ia_sex_serv",  "Illegal sexual services"),
            ("ia_animal",    "Animal abuse"),
            ("ia_nonconsent","Non-consensual sexual imagery"),
            ("ia_porn",      "Pornography"),
            ("ia_other",     "Other illegal sexual content"),
        ],
    },
    "personal_data": {
        "emoji": "🆔", "label": "Personal data",
        "api": types.InputReportReasonPersonalDetails(),
        "subs": [
            ("pd_private_imgs", "Private images"),
            ("pd_phone",        "Phone number"),
            ("pd_address",      "Address"),
            ("pd_stolen",       "Stolen data or credentials"),
            ("pd_other",        "Other personal information"),
        ],
    },
    "scam_fraud": {
        "emoji": "🎭", "label": "Scam or fraud",
        "api": types.InputReportReasonFake(),
        "subs": [
            ("sf_imperson",     "Impersonation"),
            ("sf_finance",      "Deceptive or unrealistic financial claims"),
            ("sf_malware",      "Malware, phishing"),
            ("sf_fraud_seller", "Fraudulent seller, product or service"),
        ],
    },
    "copyright": {
        "emoji": "©️", "label": "Copyright",
        "api": types.InputReportReasonCopyright(),
        "subs": [],  # direct, only optional message
    },
    "spam": {
        "emoji": "📨", "label": "Spam",
        "api": types.InputReportReasonSpam(),
        "subs": [
            ("sp_insults",       "Insults or false information"),
            ("sp_illegal_prom",  "Promoting illegal content"),
            ("sp_other_prom",    "Promoting other content"),
        ],
    },
    "other": {
        "emoji": "❓", "label": "Other",
        "api": types.InputReportReasonOther(),
        "subs": [],  # direct
    },
    "not_illegal": {
        "emoji": "⚠️", "label": "It's not illegal, but must be taken down",
        "api": types.InputReportReasonOther(),
        "subs": [],  # direct
    },
}

# ══════════════════════════════════════════════════════════════════════
# 🔧 TELETHON CLIENT BUILDER + CONNECT
# ══════════════════════════════════════════════════════════════════════
def build_client(session, proxy_cfg: Optional[dict], device: Optional[dict] = None) -> TelegramClient:
    dev = device or random.choice(DEVICE_POOL)
    kwargs = dict(
        device_model=dev["device_model"],
        system_version=dev["system_version"],
        app_version=dev["app_version"],
        lang_code="en", system_lang_code="en-US",
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
        await asyncio.wait_for(client.connect(), timeout=15)
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
                dev = get_or_assign_device(phone)
                new_client = build_client(sess, None, dev)
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

def load_accounts_from_db():
    data = db_load_accounts()
    if not data: return
    proxies = healthy_proxies() if PROXY_ENABLED else []
    for i, (phone, sess) in enumerate(data.items()):
        try:
            proxy = proxies[i % len(proxies)] if proxies else None
            dev = get_or_assign_device(phone)
            client = build_client(StringSession(sess), proxy, dev)
            accounts[phone] = client
            if proxy: account_proxy_map[phone] = proxy
            add_log(f"✅ Loaded: {phone} [{dev['device_model']}]" +
                    (f" [proxy: {proxy['addr']}]" if proxy else " [direct]"))
        except Exception as e:
            logger.error(f"Load error {phone}: {e}")

def save_account_to_db(phone: str):
    try:
        c = accounts.get(phone)
        if not c: return
        sess = StringSession.save(c.session)
        db_save_account(phone, sess)
    except Exception as e:
        logger.error(f"save_account_to_db fail: {e}")

async def count_active() -> int:
    n = 0
    for phone, c in list(accounts.items()):
        try:
            if not c.is_connected():
                try: await asyncio.wait_for(c.connect(), timeout=10)
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
# 🔍 SESSION STRING DETECTION + PYROGRAM CONVERTER
# ══════════════════════════════════════════════════════════════════════
def looks_like_session_string(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    cleaned = t.replace("+", "").replace(" ", "").replace("-", "")
    if cleaned.isdigit() and len(cleaned) <= 20:
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
    dev = random.choice(DEVICE_POOL)

    try:
        client = build_client(StringSession(session_str), proxy, dev)
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

    try:
        telethon_str = convert_pyrogram_to_telethon(session_str)
        if telethon_str:
            client = build_client(StringSession(telethon_str), proxy, dev)
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

def parse_multi_msg_links(text: str) -> Tuple[List[Tuple[str, int, str]], List[str]]:
    valid: List[Tuple[str, int, str]] = []
    invalid: List[str] = []
    lines = re.split(r"[\s\n]+", text.strip())
    seen = set()
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        ident, msg_id, err = parse_message_link(ln)
        if err or ident is None or msg_id is None:
            invalid.append(ln)
            continue
        key = f"{ident}:{msg_id}"
        if key in seen:
            continue
        seen.add(key)
        valid.append((ident, msg_id, ln))
        if len(valid) >= MAX_MSG_LINKS:
            break
    return valid, invalid

# ══════════════════════════════════════════════════════════════════════
# 🔄 GROUP JOIN
# ══════════════════════════════════════════════════════════════════════
async def join_group_all(identifier, link_type) -> Tuple[int, int]:
    if link_type == "username":
        add_log(f"ℹ️ Public group '{identifier}' — skipping join.")
        return (len(accounts), 0)
    ok, fail = 0, 0
    for phone in list(accounts.keys()):
        client = await ensure_connected(phone)
        if not client:
            fail += 1; continue
        try:
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
                    fail += 1; add_log(f"❌ Invite join fail: {phone[-4:]} — {type(e).__name__}")
            elif link_type == "private_channel":
                try:
                    await client(JoinChannelRequest(identifier))
                    ok += 1; add_log(f"✅ Joined (private ch): {phone[-4:]}")
                except errors.UserAlreadyParticipantError:
                    ok += 1; add_log(f"✅ Already member: {phone[-4:]}")
                except Exception as e:
                    fail += 1; add_log(f"❌ Private ch join fail: {phone[-4:]} — {type(e).__name__}")
            await asyncio.sleep(random.uniform(0.8, 2.0))
        except Exception as e:
            fail += 1; add_log(f"❌ Join error: {phone[-4:]} — {type(e).__name__}")
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
# 🚀 CORE MESSAGE REPORT ENGINE — BATCH (FAST + POWERFUL)
# ══════════════════════════════════════════════════════════════════════
async def send_report_batch(phone, channel_id, msg_ids: List[int], reason_api, custom_msg,
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

        msg_ids_int = [int(m) for m in msg_ids]
        await asyncio.sleep(random.uniform(0.1, 0.35))  # faster

        # M1
        try:
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=msg_ids_int,
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M1 OK: {phone[-4:]} ({len(msg_ids_int)} msgs)")
                return (True, f"Success (M1: {len(msg_ids_int)} msgs in 1 call)")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except errors.MessageIdInvalidError:
            return (False, "Invalid Message ID(s)")
        except errors.ChannelPrivateError:
            return (False, "Private channel — no access")
        except errors.UserBannedInChannelError:
            return (False, "Account banned in channel")
        except (ConnectionError, OSError):
            add_log(f"⚠️ M1 disconnect {phone[-4:]} — reconnecting")
            client = await ensure_connected(phone)
            if not client:
                return (False, "Reconnect failed")
        except Exception as e:
            add_log(f"⚠️ M1 fail {phone[-4:]}: {type(e).__name__}")

        # M2
        await asyncio.sleep(random.uniform(0.2, 0.5))
        try:
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
            await client.get_messages(entity, ids=msg_ids_int)
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=msg_ids_int,
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M2 OK: {phone[-4:]} ({len(msg_ids_int)} msgs)")
                return (True, f"Success (M2: prefetch+report, {len(msg_ids_int)} msgs)")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except Exception as e:
            add_log(f"⚠️ M2 fail {phone[-4:]}: {type(e).__name__}")

        # M3
        await asyncio.sleep(random.uniform(0.2, 0.5))
        try:
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
            result = await client(functions.account.ReportPeerRequest(
                peer=entity, reason=reason_api,
                message=f"Re: Msg IDs {','.join(map(str,msg_ids_int))} — {craft_report_message(custom_msg, sub_label)}"))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M3 OK: {phone[-4:]}")
                return (True, "Success (M3: account.reportPeer)")
        except Exception as e:
            add_log(f"⚠️ M3 fail {phone[-4:]}: {type(e).__name__}")

        # M4
        await asyncio.sleep(random.uniform(0.2, 0.5))
        try:
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
            entity = await resolve_chat_entity(client, channel_id, link_type)
            result = await client(functions.messages.ReportRequest(
                peer=entity, id=msg_ids_int,
                reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
            if result:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M4 OK: {phone[-4:]}")
                return (True, f"Success (M4: re-resolve+report, {len(msg_ids_int)} msgs)")
        except Exception as e:
            add_log(f"⚠️ M4 fail {phone[-4:]}: {type(e).__name__}")

        # M5 per-msg
        per_msg_ok = 0
        try:
            client = await ensure_connected(phone)
            if client:
                entity = await resolve_chat_entity(client, channel_id, link_type)
                for mid in msg_ids_int:
                    try:
                        r = await client(functions.messages.ReportRequest(
                            peer=entity, id=[mid],
                            reason=reason_api, message=craft_report_message(custom_msg, sub_label)))
                        if r:
                            per_msg_ok += 1
                        await asyncio.sleep(random.uniform(0.15, 0.4))
                    except errors.FloodWaitError as e:
                        return (False, f"FloodWait {e.seconds}s")
                    except Exception:
                        continue
            if per_msg_ok > 0:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M5 OK: {phone[-4:]} ({per_msg_ok}/{len(msg_ids_int)})")
                return (True, f"Success (M5: per-msg, {per_msg_ok}/{len(msg_ids_int)})")
        except Exception as e:
            add_log(f"⚠️ M5 fail {phone[-4:]}: {type(e).__name__}")

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
            await asyncio.sleep(random.uniform(0.2, 0.5))
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
                await asyncio.sleep(random.uniform(0.2, 0.5))
                client = await ensure_connected(phone)
                if not client: break
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
        await asyncio.sleep(random.uniform(0.2, 0.5))
        client = await ensure_connected(phone)
        if client:
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
        await asyncio.sleep(random.uniform(0.3, 0.6))
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
                    add_log(f"✅ PFP-M4 OK: {phone[-4:]}")
                    return (True, "Success (M4: refresh+retry)")
            methods_tried.append("M4")
    except Exception as e:
        methods_tried.append(f"M4-fail({type(e).__name__})")

    try:
        await asyncio.sleep(random.uniform(0.2, 0.5))
        client = await ensure_connected(phone)
        if client:
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
        await asyncio.sleep(random.uniform(0.2, 0.5))
        client = await ensure_connected(phone)
        if client:
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
# ⏱ DELAYS — POWERFUL: even faster than v15
# ══════════════════════════════════════════════════════════════════════
def smart_delay(i, total) -> float:
    base  = random.uniform(1.2, 3.0)
    extra = random.uniform(0, 1.5) if random.random() < 0.3 else 0
    if i > total * 0.7: extra += random.uniform(0.5, 1.5)
    return base + extra

def account_switch_delay() -> float:
    return random.uniform(1.2, 3.0)

def round_robin_delay() -> float:
    return random.uniform(0.8, 2.0)

# ══════════════════════════════════════════════════════════════════════
# 📧 GMAIL ENGINE
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
    if not GMAIL_ACCOUNTS:
        return (0, 0, "⚠️ No gmail accounts configured. Owner can /addmail.")
    tasks = [_send_single_gmail(acc, subject, body, recipient, evidence, ev_name, round_num) for acc in GMAIL_ACCOUNTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    lines = []; ok = 0
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            lines.append(f"❌ {GMAIL_ACCOUNTS[i]['email']} → Exception")
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
            await asyncio.sleep(random.uniform(1.5, 3.5))
    return (total_ok, total_fail, "\n\n".join(details_all))

# ══════════════════════════════════════════════════════════════════════
# 🎬 ANIMATED /start
# ══════════════════════════════════════════════════════════════════════
async def animated_start(message):
    frames = [
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▱▱▱▱▱▱▱▱▱▱  0%",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▱▱▱▱▱▱▱▱  20%\n\n🔧 Loading core modules...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▱▱▱▱▱▱  40%\n\n🌐 Verifying network...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▱▱▱▱  60%\n\n📸 Arming engine...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▰▰▱▱  80%\n\n🛡️ Engaging stealth mode...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▰▰▰▰  100%\n\n🚀 <b>ONLINE</b> — ready to strike 😎",
    ]
    msg = await message.reply_text(frames[0], parse_mode="HTML")
    for f in frames[1:]:
        await asyncio.sleep(0.3)
        try:
            await msg.edit_text(f, parse_mode="HTML")
        except Exception:
            pass
    await asyncio.sleep(0.2)
    return msg

# ══════════════════════════════════════════════════════════════════════
# 🔢 STATES
# ══════════════════════════════════════════════════════════════════════
(
    PHONE, CODE, PASSWORD, RM_PHONE,
    GRP_LINK, MSG_LINK, REASON_CAT, REASON_SUB, CUSTOM_MSG, COUNT,
    MAIL_SUBJECT, MAIL_BODY, MAIL_EVIDENCE, MAIL_RECIPIENT,
    MAIL_BLAST_COUNT, MAIL_RESEND,
    AR_USER, AR_REASON, AR_OTHER_MSG, AR_COUNT,
    BR_USER, BR_CAT, BR_SUB, BR_MSG, BR_COUNT,
    GR_GRP_LINK, GR_MSG_LINK, GR_REASON_CAT, GR_REASON_SUB, GR_CUSTOM_MSG, GR_COUNT,
    AM_EMAIL, AM_PASS, AM_NAME,
) = range(34)

# (Part 1 ends here — Part 2 continues with handlers and main())
# ══════════════════════════════════════════════════════════════════════
# 🎨 KEYBOARDS
# ══════════════════════════════════════════════════════════════════════
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
         InlineKeyboardButton("🌐 Proxy Status",   callback_data="MENU|proxystatus")],
        [InlineKeyboardButton("🔄 Reload Proxies", callback_data="MENU|reloadproxies"),
         InlineKeyboardButton("ℹ️ Help",           callback_data="MENU|help")],
        [InlineKeyboardButton("🧹 Clear Logs",     callback_data="MENU|clearlogs"),
         InlineKeyboardButton("♻️ Restart Bot",    callback_data="MENU|restart")],
    ]
    if is_owner:
        rows.append([InlineKeyboardButton("➕ Add Mail",    callback_data="MENU|addmail"),
                     InlineKeyboardButton("📧 Mail List",   callback_data="MENU|maillist")])
        rows.append([InlineKeyboardButton("🔑 Sudo List",   callback_data="MENU|sudolist"),
                     InlineKeyboardButton("⚙️ Toggle Proxy",callback_data="MENU|toggleproxy")])
    return InlineKeyboardMarkup(rows)

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

def _build_pfp_reason_keyboard():
    rows = []; row = []
    for key, (label, _) in PFP_REPORT_REASONS.items():
        row.append(InlineKeyboardButton(label, callback_data=f"PFP|{key}"))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

# ══════════════════════════════════════════════════════════════════════
# 🤖 BASIC COMMANDS
# ══════════════════════════════════════════════════════════════════════
async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized.\nContact owner for access.")
        return
    is_owner = (update.effective_user.id == OWNER_ID)
    owner_tag = "👑 Owner" if is_owner else "🔑 Sudo"

    anim_msg = await animated_start(update.message)
    await asyncio.sleep(0.2)

    proxy_status = "🟢 ON" if PROXY_ENABLED else "⚡ OFF (direct)"
    welcome = (
        f"⚡ <b>ULTIMATE REPORTER v{BOT_VERSION}</b>\n"
        f"<i>CYBER JUSTICE ELITE++ (Mongo edition)</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ Access  : {owner_tag}\n"
        f"🌐 Proxy   : {proxy_status}\n"
        f"📱 Accounts: <b>{len(accounts)}</b>\n"
        f"📧 Gmails  : <b>{len(GMAIL_ACCOUNTS)}</b>\n"
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
        "report":        ("📩 <b>Message Report</b>\n\nUse /report — supports MULTIPLE message links + skip.", "/report"),
        "groupreport":   ("👥 <b>Group Report</b>\n\nUse /groupreport — MULTIPLE msg links + skip, 3-dot menu flow.", "/groupreport"),
        "accountreport": ("👤 <b>Account / PFP Report</b>\n\nUse /accountreport — 6-method nuclear PFP.", "/accountreport"),
        "botreport":     ("🤖 <b>Bot Report</b>\n\nUse /botreport — full Telegram report categories.", "/botreport"),
        "massgmail":     ("📧 <b>Mass Gmail Blast</b>\n\nUse /massgmail.", "/massgmail"),
        "addaccount":    ("➕ <b>Add Telegram Account</b>\n\nUse /addaccount — phone+OTP OR session string.", "/addaccount"),
        "rmaccount":     ("🗑️ Use /rmaccount.", "/rmaccount"),
        "allaccounts":   ("📋 Use /allaccounts.", "/allaccounts"),
        "logs":          ("📊 Use /logs.", "/logs"),
        "clearlogs":     ("🧹 Use /clearlogs.", "/clearlogs"),
        "proxystatus":   ("🌐 Use /proxystatus.", "/proxystatus"),
        "reloadproxies": ("🔄 Use /reloadproxies.", "/reloadproxies"),
        "help":          ("ℹ️ Use /help.", "/help"),
        "sudolist":      ("🔑 Use /sudolist (owner).", "/sudolist"),
        "toggleproxy":   ("⚙️ /proxyon | /proxyoff", "/proxyon /proxyoff"),
        "addmail":       ("➕ <b>Add Gmail</b> (owner only)\n\nUse /addmail — bot will ask for email, app password, name.", "/addmail"),
        "maillist":      ("📧 Use /maillist (owner).", "/maillist"),
        "back":          ("Main menu", "/start"),
    }
    text, hint = info_map.get(action, ("Unknown action.", "/start"))
    is_owner = (update.effective_user.id == OWNER_ID)
    if action == "back":
        proxy_status = "🟢 ON" if PROXY_ENABLED else "⚡ OFF (direct)"
        welcome = (
            f"⚡ <b>ULTIMATE REPORTER v{BOT_VERSION}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 Proxy: {proxy_status} | 📱 Accounts: {len(accounts)} | 📧 Mails: {len(GMAIL_ACCOUNTS)}\n"
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
    owner_section = ""
    if update.effective_user.id == OWNER_ID:
        owner_section = (
            "\n👑 <b>Owner:</b>\n"
            "/sudo /rmsudo /sudolist\n"
            "/addmail /rmmail /maillist\n"
            "/proxyon /proxyoff\n"
        )
    await update.message.reply_text(
        f"📖 <b>HELP — v{BOT_VERSION}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 /report — Message report (MULTI-LINK + skip)\n"
        "👥 /groupreport — Group-level report (MULTI-LINK + skip)\n"
        "📸 /accountreport — Nuclear PFP report\n"
        "🤖 /botreport — Report a bot\n"
        "📧 /massgmail — Gmail blast × N\n"
        "➕ /addaccount — Phone+OTP OR Session String\n"
        "🗑️ /rmaccount — Remove account\n"
        "📋 /allaccounts — List accounts\n"
        "🌐 /proxystatus — Proxy health\n"
        "🔄 /reloadproxies — Refresh proxy pool\n"
        "📊 /logs — Send activity log files\n"
        "🧹 /clearlogs — Clear logs & stats\n"
        "♻️ /restart — Restart bot (state preserved)\n"
        "❌ /cancel — Cancel current flow\n"
        f"{owner_section}",
        parse_mode="HTML"
    )

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    add_log(f"❌ User {update.effective_user.id} cancelled flow")
    await update.message.reply_text("❌ Cancelled.\nUse /start to open the menu again.")
    return ConversationHandler.END

async def logs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    uid = update.effective_user.id
    txt = f"📊 <b>ACTIVITY STATS</b>\n\n{get_stats(uid)}\n\nRecent logs:\n<pre>{get_logs(30)}</pre>"
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
                    caption=f"📋 Activity log — {today}")
            sent_any = True
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not send activity log: {e}")

    if reports_file.exists() and reports_file.stat().st_size > 0:
        try:
            with open(reports_file, "rb") as f:
                await update.message.reply_document(
                    document=f, filename=reports_file.name,
                    caption=f"🎯 Reports log — {today}")
            sent_any = True
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not send reports log: {e}")

    if not sent_any:
        await update.message.reply_text("📭 No log files yet for today.")

async def clearlogs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    clear_logs(); reset_stats(update.effective_user.id)
    await update.message.reply_text("🗑️ Logs cleared & stats reset!")

async def allaccounts_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    if not accounts:
        await update.message.reply_text("📭 No accounts. Use /addaccount"); return
    txt = "📱 <b>ALL ACCOUNTS</b>\n\n"; active = 0
    for i, (phone, client) in enumerate(accounts.items(), 1):
        try:
            if not client.is_connected():
                try: await asyncio.wait_for(client.connect(), timeout=8)
                except: pass
            auth   = await client.is_user_authorized() if client.is_connected() else False
            status = "🟢 Active" if auth else "🔴 Inactive"
            if auth: active += 1
            dev = account_device_map.get(phone, {})
            dev_txt = f" [{dev.get('device_model','?')}]" if dev else ""
        except:
            status = "🔴 Inactive"; dev_txt = ""
        txt += f"{i}. <code>{phone}</code> — {status}{dev_txt}\n"
    txt += f"\n📊 Total: {len(accounts)} | 🟢 {active} | 🔴 {len(accounts)-active}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def proxystatus_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    mode = "🟢 ENABLED" if PROXY_ENABLED else "⚡ DISABLED (direct mode)"
    if not PROXY_LIST:
        await update.message.reply_text(
            f"🌐 Proxy Mode: <b>{mode}</b>\n\n"
            f"📭 No proxies in pool.\n"
            f"Use /reloadproxies to fetch.",
            parse_mode="HTML"); return
    txt = f"🌐 Proxy Mode: <b>{mode}</b>\n"
    txt += f"Pool: {len(PROXY_LIST)} total\n\n"
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
    await update.message.reply_text("🟢 Proxy mode: <b>ENABLED</b>", parse_mode="HTML")

async def proxyoff_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    global PROXY_ENABLED
    PROXY_ENABLED = False
    account_proxy_map.clear()
    await update.message.reply_text("⚡ Proxy mode: <b>DISABLED</b>", parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════════
# ♻️ RESTART
# ══════════════════════════════════════════════════════════════════════
async def _do_restart():
    try:
        # accounts are auto-saved to mongo on add/remove; just disconnect cleanly
        add_log("♻️ Restart: disconnecting clients...")
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
        "💾 All data is in MongoDB — fully persistent.\n"
        "🔄 Bot will reload in ~3 seconds.\n"
        "✅ Sessions will be restored automatically.",
        parse_mode="HTML")
    add_log(f"♻️ Restart triggered by user {update.effective_user.id}")
    await _do_restart()

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
    db_add_sudo(int(target_id), target_name, "")
    add_log(f"🔑 Sudo granted: {target_name} ({target_id})")
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
    db_remove_sudo(target_id)
    add_log(f"🔒 Sudo revoked: {name} ({target_id})")
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
# 📧 ADD MAIL (OWNER ONLY)
# ══════════════════════════════════════════════════════════════════════
async def addmail_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return ConversationHandler.END
    await update.message.reply_text(
        "➕ <b>ADD GMAIL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send the Gmail address:\n"
        "  e.g. <code>example@gmail.com</code>\n\n"
        "/cancel to abort.",
        parse_mode="HTML")
    return AM_EMAIL

async def am_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Invalid email. Try again or /cancel:"); return AM_EMAIL
    ctx.user_data["am_email"] = email
    await update.message.reply_text(
        "🔑 Now send the <b>App Password</b> (16 chars from Google):\n"
        "  e.g. <code>abcd efgh ijkl mnop</code> (spaces OK)",
        parse_mode="HTML")
    return AM_PASS

async def am_pass(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    pw = update.message.text.strip().replace(" ", "")
    if len(pw) < 8:
        await update.message.reply_text("❌ Password too short. Try again or /cancel:"); return AM_PASS
    ctx.user_data["am_pass"] = pw
    await update.message.reply_text(
        "👤 Send a display name for this account (or send <code>skip</code> to auto-derive):",
        parse_mode="HTML")
    return AM_NAME

async def am_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    email = ctx.user_data["am_email"]
    pw    = ctx.user_data["am_pass"]
    if name.lower() in ("skip", "/skip", ""):
        name = email.split("@")[0].title()
    ok = db_add_gmail(email, pw, name)
    if ok:
        db_load_gmails()  # reload pool
        add_log(f"📧 Gmail added: {email}")
        await update.message.reply_text(
            f"✅ <b>Gmail Added!</b>\n📧 {email}\n👤 {name}\n\nTotal mails: {len(GMAIL_ACCOUNTS)}",
            parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Failed to save to MongoDB.")
    return ConversationHandler.END

async def rmmail_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    if not ctx.args:
        await update.message.reply_text("⚠️ Usage: /rmmail email@gmail.com"); return
    email = ctx.args[0].strip()
    if db_remove_gmail(email):
        db_load_gmails()
        await update.message.reply_text(f"✅ Removed: {email}\nRemaining: {len(GMAIL_ACCOUNTS)}")
    else:
        await update.message.reply_text(f"❌ Not found: {email}")

async def maillist_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    if not GMAIL_ACCOUNTS:
        await update.message.reply_text("📭 No gmail accounts. Use /addmail."); return
    txt = "📧 <b>GMAIL ACCOUNTS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, g in enumerate(GMAIL_ACCOUNTS, 1):
        txt += f"{i}. <b>{g['name']}</b>\n   📧 <code>{g['email']}</code>\n\n"
    txt += f"━━━━━━━━━━━━━━━━━━━━\n📊 Total: {len(GMAIL_ACCOUNTS)}"
    await update.message.reply_text(txt, parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════════
# 📱 ADD / REMOVE ACCOUNT
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
            "🔍 Detected session string\n⏳ Trying Telethon → Pyrogram fallback...",
            parse_mode="HTML")
        client, ident, err = await try_load_session_string(raw)
        if not client:
            await wait_msg.edit_text(
                f"❌ Session login failed: {err}\n\nTry again or send a phone number, or /cancel.",
                parse_mode="HTML")
            return PHONE
        if ident in accounts:
            try: await client.disconnect()
            except: pass
            await wait_msg.edit_text(f"⚠️ Account <code>{ident}</code> already exists!", parse_mode="HTML")
            return ConversationHandler.END
        accounts[ident] = client
        # assign + persist device
        get_or_assign_device(ident)
        save_account_to_db(ident)
        add_log(f"✅ Added via session string: {ident}")
        await wait_msg.edit_text(
            f"✅ <b>Logged in via session string!</b>\n📱 <code>{ident}</code>\n📊 Total: {len(accounts)}",
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
        dev = random.choice(DEVICE_POOL)
        client = build_client(StringSession(), proxy, dev)
        try:
            await asyncio.wait_for(client.connect(), timeout=15)
        except Exception as e:
            if proxy:
                add_log(f"⚠️ Add-account proxy failed, retrying direct: {type(e).__name__}")
                try: await client.disconnect()
                except: pass
                proxy = None
                client = build_client(StringSession(), None, dev)
                await asyncio.wait_for(client.connect(), timeout=15)
            else:
                raise
        sent   = await client.send_code_request(phone)
        ctx.user_data.update({"phone_hash": sent.phone_code_hash, "temp_client": client,
                              "temp_proxy": proxy, "temp_device": dev})
        await update.message.reply_text(
            "📩 <b>OTP sent!</b>\n\n"
            "Enter the code you received.\n"
            "💡 Add spaces between digits if Telegram blocks the raw code:\n"
            "    e.g. <code>1 2 3 4 5</code>",
            parse_mode="HTML")
        add_log(f"📱 Adding: {phone}")
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
    dev    = ctx.user_data.get("temp_device")
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=p_hash)
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        if dev:
            account_device_map[phone] = dev
            db.devices.update_one({"phone": phone}, {"$set": {"phone": phone, "device": dev}}, upsert=True)
        save_account_to_db(phone)
        add_log(f"✅ Added: {phone}")
        await update.message.reply_text(f"✅ <b>Added!</b>\n📱 <code>{phone}</code>\nTotal: {len(accounts)}", parse_mode="HTML")
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
    proxy  = ctx.user_data.get("temp_proxy"); dev = ctx.user_data.get("temp_device")
    try:
        await client.sign_in(password=update.message.text.strip())
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        if dev:
            account_device_map[phone] = dev
            db.devices.update_one({"phone": phone}, {"$set": {"phone": phone, "device": dev}}, upsert=True)
        save_account_to_db(phone)
        add_log(f"✅ Added (2FA): {phone}")
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
        db_remove_account(phone)
        add_log(f"🗑 Removed: {phone}")
        await update.message.reply_text(f"✅ Removed <code>{phone}</code>\nRemaining: {len(accounts)}", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:80]}")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 🎯 MESSAGE REPORT FLOW  (/report) — MULTI-LINK + SKIP
# ══════════════════════════════════════════════════════════════════════
async def report_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats(update.effective_user.id)
    ctx.user_data["msg_links_buf"] = []
    add_log(f"🎯 Report flow started by user {update.effective_user.id}")
    await update.message.reply_text(
        f"🎯 <b>REPORT FLOW</b> — Step 1/7\n\n"
        f"✅ Active: <b>{active}/{len(accounts)}</b> accounts\n\n"
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
            f"📥 <b>Step 2/7</b> — Send MESSAGE LINK(s):\n\n"
            f"  • <code>t.me/groupname/123</code>\n"
            f"  • <code>t.me/c/1234567890/123</code>\n\n"
            f"💡 Paste multiple links (newline/space-separated),\n"
            f"or send one by one — type <code>skip</code> when done.\n"
            f"Max {MAX_MSG_LINKS} links.",
            parse_mode="HTML")
    else:
        await update.message.reply_text(f"🔄 Joining private group...\n{link}", parse_mode="HTML")
        ok, fail = await join_group_all(ident, ltype)
        if ok == 0:
            await update.message.reply_text("❌ No accounts could join! Check link/invite."); return ConversationHandler.END
        await update.message.reply_text(
            f"✅ Join complete!\n✅ {ok} | ❌ {fail}\n\n"
            f"📥 <b>Step 2/7</b> — Send MESSAGE LINK(s):\n\n"
            f"💡 Paste multiple links OR send one by one — type <code>skip</code> when done.\n"
            f"Max {MAX_MSG_LINKS} links.",
            parse_mode="HTML")
    return MSG_LINK

async def receive_msg_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw_text = update.message.text.strip()
    buf: List[Tuple[str, int, str]] = ctx.user_data.get("msg_links_buf", [])

    if raw_text.lower() in ("skip", "done", "/skip", "/done"):
        if not buf:
            await update.message.reply_text(
                "⚠️ You haven't added any message link yet!\n"
                "Send at least one message link, then type <code>skip</code>.",
                parse_mode="HTML")
            return MSG_LINK
        ctx.user_data["msg_links_buf"] = buf
        summary = "\n".join(f"  {i+1}. <code>{ln}</code>" for i, (_,_,ln) in enumerate(buf))
        await update.message.reply_text(
            f"✅ Collected <b>{len(buf)}</b> message link(s):\n{summary}\n\n"
            f"📋 <b>Step 3/7</b> — Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"),
            parse_mode="HTML")
        return REASON_CAT

    new_valid, invalid = parse_multi_msg_links(raw_text)
    if not new_valid:
        await update.message.reply_text(
            "❌ No valid message link found.\n"
            "Send a link like <code>t.me/groupname/123</code> or type <code>skip</code>.",
            parse_mode="HTML")
        return MSG_LINK

    existing_keys = {f"{i}:{m}" for i, m, _ in buf}
    added = 0
    for ident, mid, ln in new_valid:
        k = f"{ident}:{mid}"
        if k in existing_keys: continue
        if len(buf) >= MAX_MSG_LINKS: break
        buf.append((ident, mid, ln))
        existing_keys.add(k)
        added += 1
    ctx.user_data["msg_links_buf"] = buf
    add_log(f"📥 Msg links: +{added} (total {len(buf)})")
    invalid_note = f"\n⚠️ Skipped {len(invalid)} invalid line(s)." if invalid else ""
    reached_cap = f"\n🚫 Cap reached: {MAX_MSG_LINKS} links max." if len(buf) >= MAX_MSG_LINKS else ""
    await update.message.reply_text(
        f"✅ Added <b>{added}</b> new link(s). Total queued: <b>{len(buf)}</b>{invalid_note}{reached_cap}\n\n"
        f"➕ Send more, OR type <code>skip</code> to continue.",
        parse_mode="HTML")
    return MSG_LINK

async def category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2:
        return REASON_CAT
    cat_key = parts[1]
    if cat_key == "back":
        await query.edit_message_text("📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    if cat_key not in FULL_REPORT_CATEGORIES:
        return REASON_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data["cat_key"] = cat_key
    ctx.user_data["cat_label"] = cat["label"]
    ctx.user_data["reason_api"] = cat["api"]
    if not cat["subs"]:
        # direct → custom msg
        ctx.user_data["sub_key"]   = "N/A"
        ctx.user_data["sub_label"] = "N/A"
        await query.edit_message_text(
            f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
            f"📝 <b>Step 5/7</b> — Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return CUSTOM_MSG

    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
        f"📋 <b>Step 4/7</b> — Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "SUB"),
        parse_mode="HTML")
    return REASON_SUB

async def subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text("📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    if len(parts) < 3:
        return REASON_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return REASON_SUB
    sub_label = next((s[1] for s in cat["subs"] if s[0] == sub_key), "N/A")
    ctx.user_data["sub_key"]   = sub_key
    ctx.user_data["sub_label"] = sub_label
    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']} → <b>{sub_label}</b>\n\n"
        f"📝 <b>Step 5/7</b> — Optional message or send <code>skip</code>:",
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
    uid = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            raise ValueError
    except:
        await update.message.reply_text(f"❌ Invalid! Enter 1–{MAX_REPORTS_PER_ACCOUNT}:"); return COUNT

    # acquire per-user lock so SAME user can't double-fire,
    # but DIFFERENT users can fire concurrently
    lock = get_user_lock(uid)
    if lock.locked():
        await update.message.reply_text("⚠️ You already have a job running. Wait for it to finish or /cancel.")
        return ConversationHandler.END

    async with lock:
        return await _report_execute_inner(update, ctx, count)

async def _report_execute_inner(update, ctx, count):
    uid = update.effective_user.id
    cat_key   = ctx.user_data["cat_key"]
    cat_lbl   = ctx.user_data["cat_label"]
    sub_lbl   = ctx.user_data.get("sub_label", "N/A")
    reason_api= ctx.user_data["reason_api"]
    custom_msg= ctx.user_data.get("custom_msg", "")
    link_type = ctx.user_data["grp_type"]
    msg_buf: List[Tuple[str,int,str]] = ctx.user_data.get("msg_links_buf", [])
    if not msg_buf:
        await update.message.reply_text("⚠️ No message links queued.")
        return ConversationHandler.END

    # group by chat ident
    grouped: Dict[str, List[Tuple[int,str]]] = {}
    for ident, mid, ln in msg_buf:
        grouped.setdefault(ident, []).append((mid, ln))

    chats_count = len(grouped)
    total_msgs  = sum(len(v) for v in grouped.values())

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts ready!"); return ConversationHandler.END

    total_planned = count * len(auth_pairs) * chats_count
    s = _stats_for(uid); s["total"] = total_planned; s["start_time"] = datetime.now()

    join_note = "Already joined" if link_type != "username" else "Public — no join"
    msg_summary = "\n".join(
        f"  • <code>{ident}</code> → {len(mids)} msg(s)"
        for ident, mids in grouped.items())

    await update.message.reply_text(
        f"🚀 <b>REPORTING STARTED (BATCHED + ROUND-ROBIN)</b> — Step 7/7\n\n"
        f"📊 Report calls: <b>{total_planned}</b>\n"
        f"🗂 Chats: {chats_count} | 📨 Messages queued: {total_msgs}\n"
        f"📱 Accounts: {len(auth_pairs)} × {count} rounds\n"
        f"⚠️ <b>{cat_lbl}</b> → {sub_lbl}\n"
        f"🌐 {join_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n{msg_summary}\n━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            for chat_ident, mid_list in grouped.items():
                shot_num += 1
                msg_ids_only = [mid for mid, _ in mid_list]
                ok, status = await send_report_batch(
                    phone, chat_ident, msg_ids_only, reason_api, custom_msg,
                    link_type, sub_lbl)
                if ok:
                    total_ok += 1; per_acc_ok[phone] += 1; update_stats(uid, True)
                    log_report_file(phone, f"{chat_ident}/{msg_ids_only}", f"{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                    try:
                        await update.message.reply_text(
                            f"✅ {shot_num}/{total_planned} | R{r+1} | 📱 <code>{phone[-4:]}</code> | {len(msg_ids_only)} msg → {status}",
                            parse_mode="HTML")
                    except: pass
                else:
                    total_fail += 1; per_acc_fail[phone] += 1; update_stats(uid, False)
                    log_report_file(phone, f"{chat_ident}/{msg_ids_only}", f"{cat_lbl}/{sub_lbl}", "FAILED", status)
                    try:
                        await update.message.reply_text(
                            f"❌ {shot_num}/{total_planned} | R{r+1} | 📱 <code>{phone[-4:]}</code> | {len(msg_ids_only)} msg → {status}",
                            parse_mode="HTML")
                    except: pass
                    if "FloodWait" in status:
                        try:
                            wait = int(status.split()[1].replace("s",""))
                            await update.message.reply_text(f"⏳ FloodWait {wait}s — waiting...")
                            await asyncio.sleep(min(wait + 2, 300))
                        except: await asyncio.sleep(60)
            if acc_idx < len(auth_pairs) - 1:
                await asyncio.sleep(round_robin_delay())
        if r < count - 1:
            await asyncio.sleep(account_switch_delay())

    elapsed = (datetime.now() - s["start_time"]).seconds
    rate = (total_ok * 100 / total_planned) if total_planned > 0 else 0
    add_log(f"🎉 Done (user {uid}): {total_ok}/{total_planned} ({rate:.1f}%)")
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
        f"Per-account:\n{breakdown}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n\n"
        f"📧 Also blast Gmail?",
        reply_markup=keyboard, parse_mode="HTML")
    return MAIL_SUBJECT

# ══════════════════════════════════════════════════════════════════════
# 👥 GROUP REPORT  (/groupreport) — MULTI-LINK + SKIP
# ══════════════════════════════════════════════════════════════════════
async def groupreport_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats(update.effective_user.id)
    ctx.user_data["gr_msg_links_buf"] = []
    add_log(f"👥 GroupReport flow started by user {update.effective_user.id}")
    await update.message.reply_text(
        f"👥 <b>GROUP REPORT FLOW</b> — Step 1/6\n\n"
        f"3-dot menu flow — reason anchored to specific message(s).\n\n"
        f"✅ Active: <b>{active}/{len(accounts)}</b> accounts\n\n"
        f"📥 Send <b>GROUP / CHANNEL LINK</b>:\n"
        f"  • Public  → <code>t.me/groupname</code>\n"
        f"  • Private → <code>t.me/+invitehash</code>\n\n"
        f"/cancel to abort.",
        parse_mode="HTML")
    return GR_GRP_LINK

async def gr_receive_grp_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, ltype, err = parse_group_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return GR_GRP_LINK
    ctx.user_data.update({"gr_grp_ident": ident, "gr_grp_type": ltype, "gr_grp_link": link})
    add_log(f"📥 GroupReport group: {link} (type: {ltype})")
    if ltype == "username":
        await update.message.reply_text(
            f"ℹ️ Public group — direct report.\n\n"
            f"📥 <b>Step 2/6</b> — Send MESSAGE LINK(s) you want to anchor reports to:\n"
            f"💡 Multiple links (newline/space) OR one by one. Type <code>skip</code> when done.\n"
            f"Max {MAX_MSG_LINKS} links.",
            parse_mode="HTML")
    else:
        await update.message.reply_text(f"🔄 Joining private group...\n{link}", parse_mode="HTML")
        ok, fail = await join_group_all(ident, ltype)
        if ok == 0:
            await update.message.reply_text("❌ No accounts could join!"); return ConversationHandler.END
        await update.message.reply_text(
            f"✅ Join complete!\n✅ {ok} | ❌ {fail}\n\n"
            f"📥 <b>Step 2/6</b> — Send MESSAGE LINK(s):\n"
            f"💡 Multiple links OR one by one. Type <code>skip</code> when done. Max {MAX_MSG_LINKS}.",
            parse_mode="HTML")
    return GR_MSG_LINK

async def gr_receive_msg_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw_text = update.message.text.strip()
    buf: List[Tuple[str, int, str]] = ctx.user_data.get("gr_msg_links_buf", [])

    if raw_text.lower() in ("skip", "done", "/skip", "/done"):
        if not buf:
            await update.message.reply_text(
                "⚠️ You haven't added any message link yet!\n"
                "Send at least one and then type <code>skip</code>.",
                parse_mode="HTML")
            return GR_MSG_LINK
        ctx.user_data["gr_msg_links_buf"] = buf
        summary = "\n".join(f"  {i+1}. <code>{ln}</code>" for i, (_,_,ln) in enumerate(buf))
        await update.message.reply_text(
            f"✅ Collected <b>{len(buf)}</b> message link(s):\n{summary}\n\n"
            f"📋 <b>Step 3/6</b> — Select group-report reason:",
            reply_markup=_build_full_cat_keyboard("GRCAT"),
            parse_mode="HTML")
        return GR_REASON_CAT

    new_valid, invalid = parse_multi_msg_links(raw_text)
    if not new_valid:
        await update.message.reply_text(
            "❌ No valid message link found.\nSend a link or type <code>skip</code>.",
            parse_mode="HTML")
        return GR_MSG_LINK

    existing_keys = {f"{i}:{m}" for i, m, _ in buf}
    added = 0
    for ident, mid, ln in new_valid:
        k = f"{ident}:{mid}"
        if k in existing_keys: continue
        if len(buf) >= MAX_MSG_LINKS: break
        buf.append((ident, mid, ln))
        existing_keys.add(k)
        added += 1
    ctx.user_data["gr_msg_links_buf"] = buf
    add_log(f"📥 GR Msg links: +{added} (total {len(buf)})")
    invalid_note = f"\n⚠️ Skipped {len(invalid)} invalid line(s)." if invalid else ""
    reached_cap = f"\n🚫 Cap reached: {MAX_MSG_LINKS} max." if len(buf) >= MAX_MSG_LINKS else ""
    await update.message.reply_text(
        f"✅ Added <b>{added}</b> new link(s). Total queued: <b>{len(buf)}</b>{invalid_note}{reached_cap}\n\n"
        f"➕ Send more, OR type <code>skip</code> to continue.",
        parse_mode="HTML")
    return GR_MSG_LINK

async def gr_category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2: return GR_REASON_CAT
    cat_key = parts[1]
    if cat_key == "back":
        await query.edit_message_text("📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("GRCAT"))
        return GR_REASON_CAT
    if cat_key not in FULL_REPORT_CATEGORIES: return GR_REASON_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data["gr_cat_key"] = cat_key
    ctx.user_data["gr_cat_label"] = cat["label"]
    ctx.user_data["gr_reason_api"] = cat["api"]
    if not cat["subs"]:
        ctx.user_data["gr_sub_key"]   = "N/A"
        ctx.user_data["gr_sub_label"] = "N/A"
        await query.edit_message_text(
            f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
            f"📝 <b>Step 5/6</b> — Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return GR_CUSTOM_MSG
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n"
        f"📋 <b>Step 4/6</b> — Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "GRSUB"),
        parse_mode="HTML")
    return GR_REASON_SUB

async def gr_subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text("📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("GRCAT"))
        return GR_REASON_CAT
    if len(parts) < 3: return GR_REASON_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return GR_REASON_SUB
    sub_label = next((s[1] for s in cat["subs"] if s[0] == sub_key), "N/A")
    ctx.user_data["gr_sub_key"]   = sub_key
    ctx.user_data["gr_sub_label"] = sub_label
    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']} → <b>{sub_label}</b>\n\n"
        f"📝 <b>Step 5/6</b> — Optional message or send <code>skip</code>:",
        parse_mode="HTML")
    return GR_CUSTOM_MSG

async def gr_receive_custom_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.lower() == "skip": text = ""
    ctx.user_data["gr_custom_msg"] = text
    add_log(f"📥 GR custom: {(text[:40] or '(pool)')}")
    await update.message.reply_text(
        f"✅ Saved!\n\n🔢 <b>Step 6/6</b> — Reports per account?\n\n"
        f"💡 1–2 = ✅ Safe | 3–10 = ⚠️ Moderate | 10+ = 🚨 Aggressive\n\n"
        f"Enter 1–{MAX_REPORTS_PER_ACCOUNT}:", parse_mode="HTML")
    return GR_COUNT

async def _send_groupreport_single(phone, chat_ident, msg_id, reason_api, custom_msg,
                                    link_type, sub_label) -> Tuple[bool, str]:
    client = await ensure_connected(phone)
    if not client:
        return (False, "Account disconnected / unauthorized")
    proxy = account_proxy_map.get(phone)
    methods_tried = []
    try:
        try:
            entity = await resolve_chat_entity(client, chat_ident, link_type)
        except Exception as e:
            mark_proxy_result(proxy, False)
            return (False, f"Entity error: {str(e)[:50]}")

        # M1: account.reportPeer
        try:
            await asyncio.sleep(random.uniform(0.1, 0.3))
            r = await client(functions.account.ReportPeerRequest(
                peer=entity, reason=reason_api,
                message=f"[GroupReport] Re: msg {msg_id} — {craft_report_message(custom_msg, sub_label)}"))
            if r:
                mark_proxy_result(proxy, True)
                add_log(f"✅ GR-M1 OK: {phone[-4:]} (msg {msg_id})")
                return (True, f"Success (M1: reportPeer @ msg {msg_id})")
            methods_tried.append("M1")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except errors.ChannelPrivateError:
            return (False, "Private channel — no access")
        except errors.UserBannedInChannelError:
            return (False, "Account banned in channel")
        except (ConnectionError, OSError):
            client = await ensure_connected(phone)
            if not client:
                return (False, "Reconnect failed")
        except Exception as e:
            methods_tried.append(f"M1-{type(e).__name__}")

        # M2: messages.report on specific msg_id
        try:
            await asyncio.sleep(random.uniform(0.15, 0.4))
            client = await ensure_connected(phone)
            if not client: return (False, "Disconnected mid-flow")
            r = await client(functions.messages.ReportRequest(
                peer=entity, id=[int(msg_id)],
                reason=reason_api,
                message=craft_report_message(custom_msg, sub_label)))
            if r:
                mark_proxy_result(proxy, True)
                add_log(f"✅ GR-M2 OK: {phone[-4:]} (msg {msg_id})")
                return (True, f"Success (M2: messages.report msg {msg_id})")
            methods_tried.append("M2")
        except errors.FloodWaitError as e:
            return (False, f"FloodWait {e.seconds}s")
        except Exception as e:
            methods_tried.append(f"M2-{type(e).__name__}")

        # M3: prefetch + reportPeer
        try:
            await asyncio.sleep(random.uniform(0.15, 0.4))
            client = await ensure_connected(phone)
            if client:
                try: await client.get_messages(entity, ids=int(msg_id))
                except Exception: pass
                r = await client(functions.account.ReportPeerRequest(
                    peer=entity, reason=reason_api,
                    message=craft_report_message(custom_msg, sub_label)))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "Success (M3: prefetch+reportPeer)")
                methods_tried.append("M3")
        except Exception as e:
            methods_tried.append(f"M3-{type(e).__name__}")

        # M4: re-resolve + reportPeer
        try:
            await asyncio.sleep(random.uniform(0.15, 0.4))
            client = await ensure_connected(phone)
            if client:
                entity = await resolve_chat_entity(client, chat_ident, link_type)
                r = await client(functions.account.ReportPeerRequest(
                    peer=entity, reason=reason_api,
                    message=craft_report_message(custom_msg, sub_label)))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "Success (M4: re-resolve+reportPeer)")
                methods_tried.append("M4")
        except Exception as e:
            methods_tried.append(f"M4-{type(e).__name__}")

        # M5: reportSpam fallback
        try:
            await asyncio.sleep(random.uniform(0.1, 0.3))
            client = await ensure_connected(phone)
            if client:
                r = await client(functions.messages.ReportSpamRequest(peer=entity))
                if r:
                    mark_proxy_result(proxy, True)
                    return (True, "Success (M5: ReportSpam fallback)")
                methods_tried.append("M5")
        except Exception as e:
            methods_tried.append(f"M5-{type(e).__name__}")

        mark_proxy_result(proxy, False)
        return (False, f"All failed ({','.join(methods_tried)})")
    except errors.ChannelPrivateError:
        return (False, "Private channel — no access")
    except errors.UserBannedInChannelError:
        return (False, "Account banned in channel")
    except Exception as e:
        mark_proxy_result(proxy, False)
        return (False, f"{type(e).__name__}: {str(e)[:40]}")

async def gr_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT: raise ValueError
    except:
        await update.message.reply_text(f"❌ Invalid! 1–{MAX_REPORTS_PER_ACCOUNT}:"); return GR_COUNT

    lock = get_user_lock(uid)
    if lock.locked():
        await update.message.reply_text("⚠️ You already have a job running. /cancel to abort it.")
        return ConversationHandler.END
    async with lock:
        return await _gr_execute_inner(update, ctx, count)

async def _gr_execute_inner(update, ctx, count):
    uid = update.effective_user.id
    cat_lbl    = ctx.user_data["gr_cat_label"]
    sub_lbl    = ctx.user_data.get("gr_sub_label", "N/A")
    reason_api = ctx.user_data["gr_reason_api"]
    custom_msg = ctx.user_data.get("gr_custom_msg", "")
    link_type  = ctx.user_data["gr_grp_type"]
    buf: List[Tuple[str,int,str]] = ctx.user_data.get("gr_msg_links_buf", [])
    if not buf:
        await update.message.reply_text("⚠️ No message links queued.")
        return ConversationHandler.END

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total_planned = count * len(auth_pairs) * len(buf)
    s = _stats_for(uid); s["total"] = total_planned; s["start_time"] = datetime.now()
    join_note = "Already joined" if link_type != "username" else "Public — no join"

    summary = "\n".join(f"  • <code>{ln}</code>" for (_,_,ln) in buf)
    await update.message.reply_text(
        f"🚀 <b>GROUP REPORTING STARTED</b>\n\n"
        f"📊 Total: <b>{total_planned}</b>\n"
        f"🔗 Anchor msgs: {len(buf)}\n"
        f"📱 Accounts: {len(auth_pairs)} × {count}\n"
        f"⚠️ <b>{cat_lbl}</b> → {sub_lbl}\n"
        f"🌐 {join_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n{summary}\n━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            for chat_ident, msg_id, ln in buf:
                shot_num += 1
                ok, status = await _send_groupreport_single(
                    phone, chat_ident, msg_id, reason_api, custom_msg,
                    link_type, sub_lbl)
                if ok:
                    total_ok += 1; per_acc_ok[phone] += 1; update_stats(uid, True)
                    log_report_file(phone, f"{chat_ident}/{msg_id}", f"GR-{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                    try:
                        await update.message.reply_text(
                            f"✅ GR {shot_num}/{total_planned} | R{r+1} | 📱 <code>{phone[-4:]}</code> | msg {msg_id} → {status}",
                            parse_mode="HTML")
                    except: pass
                else:
                    total_fail += 1; per_acc_fail[phone] += 1; update_stats(uid, False)
                    log_report_file(phone, f"{chat_ident}/{msg_id}", f"GR-{cat_lbl}/{sub_lbl}", "FAILED", status)
                    try:
                        await update.message.reply_text(
                            f"❌ GR {shot_num}/{total_planned} | R{r+1} | 📱 <code>{phone[-4:]}</code> | msg {msg_id} → {status}",
                            parse_mode="HTML")
                    except: pass
                    if "FloodWait" in status:
                        try:
                            wait = int(status.split()[1].replace("s",""))
                            await update.message.reply_text(f"⏳ FloodWait {wait}s — waiting...")
                            await asyncio.sleep(min(wait + 2, 300))
                        except: await asyncio.sleep(60)
            if acc_idx < len(auth_pairs) - 1:
                await asyncio.sleep(round_robin_delay())
        if r < count - 1:
            await asyncio.sleep(account_switch_delay())

    elapsed = (datetime.now() - s["start_time"]).seconds
    rate = (total_ok * 100 / total_planned) if total_planned > 0 else 0
    add_log(f"🎉 GroupReport done (user {uid}): {total_ok}/{total_planned} ({rate:.1f}%)")
    breakdown = "\n".join(
        f"  📱 <code>{p[-4:]}</code> → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>GROUP REPORT COMPLETE</b>\n\n"
        f"✅ Success: {total_ok}\n"
        f"❌ Failed: {total_fail}\n"
        f"📈 Rate: {rate:.1f}%\n"
        f"⏱ Time: {elapsed//60}m {elapsed%60}s\n\n"
        f"Per-account:\n{breakdown}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}",
        parse_mode="HTML")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 📸 PFP REPORT FLOW
# ══════════════════════════════════════════════════════════════════════
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
        f"✅ Active: {active}/{len(accounts)}\n💀 6 methods + fallbacks\n\n"
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

    ctx.user_data.update({"ar_uid": uid, "ar_name": dname, "ar_uname": uname, "ar_entity_id": raw})
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
    uid = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT: raise ValueError
    except:
        await update.message.reply_text(f"❌ Invalid! 1–{MAX_REPORTS_PER_ACCOUNT}:"); return AR_COUNT

    lock = get_user_lock(uid)
    if lock.locked():
        await update.message.reply_text("⚠️ You already have a job running.")
        return ConversationHandler.END
    async with lock:
        return await _ar_execute_inner(update, ctx, count)

async def _ar_execute_inner(update, ctx, count):
    target_raw  = ctx.user_data["ar_entity_id"]
    target_name = ctx.user_data.get("ar_name", target_raw)
    reason_api  = ctx.user_data["ar_reason_api"]
    reason_label= ctx.user_data["ar_reason_label"]
    custom_msg  = ctx.user_data.get("ar_custom_msg", "")

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total_reports = count * len(auth_pairs)
    await update.message.reply_text(
        f"🚀 <b>NUCLEAR PFP REPORT</b>\n👤 {target_name}\n⚠️ {reason_label}\n"
        f"📊 {total_reports} total ({len(auth_pairs)} × {count})\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    resolved: Dict[str, Tuple[object, list]] = {}
    for phone, client in auth_pairs:
        try:
            identifier = target_raw.lstrip("@")
            ent = await client.get_entity(int(identifier) if identifier.isdigit() else identifier)
            try: ph = await client.get_profile_photos(ent)
            except Exception: ph = []
            resolved[phone] = (ent, ph)
        except Exception as e:
            await update.message.reply_text(f"❌ <code>{phone[-4:]}</code>: Resolve — {str(e)[:40]}", parse_mode="HTML")
            resolved[phone] = (None, [])

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            shot_num += 1
            ent, photos = resolved.get(phone, (None, []))
            if ent is None:
                total_fail += 1; per_acc_fail[phone] += 1
                await update.message.reply_text(
                    f"❌ PFP {shot_num}/{total_reports} | R{r+1} | <code>{phone[-4:]}</code> → resolve failed",
                    parse_mode="HTML")
                continue
            ok, status = await report_profile_photo_nuclear(phone, ent, photos, reason_api, custom_msg)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ PFP {shot_num}/{total_reports} | R{r+1} | <code>{phone[-4:]}</code> → {status}",
                    parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ PFP {shot_num}/{total_reports} | R{r+1} | <code>{phone[-4:]}</code> → {status}",
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

    rate = (total_ok * 100 / total_reports) if total_reports > 0 else 0
    add_log(f"🎉 PFP done: {total_ok}/{total_reports} ({rate:.1f}%)")
    breakdown = "\n".join(
        f"  📱 <code>{p[-4:]}</code> → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>PFP COMPLETE</b>\n\n"
        f"👤 {target_name}\n⚠️ {reason_label}\n"
        f"✅ {total_ok} | ❌ {total_fail} | 📈 {rate:.1f}%\n\n"
        f"Per-account:\n{breakdown}",
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
        f"✅ Active: {active}/{len(accounts)}\n\n"
        f"🤖 Enter @bot_username:\n/cancel to abort.",
        parse_mode="HTML")
    return BR_USER

async def br_receive_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    add_log(f"🤖 Bot target: {raw}")
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
        await wait_msg.edit_text("⚠️ Not a bot. Use /accountreport for users.")
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
    cat_key = parts[1]
    if cat_key == "back":
        await query.edit_message_text("📋 Select reason:", reply_markup=_build_full_cat_keyboard("BCAT"))
        return BR_CAT
    if cat_key not in FULL_REPORT_CATEGORIES: return BR_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data["br_cat_key"] = cat_key
    ctx.user_data["br_cat_label"] = cat["label"]
    ctx.user_data["br_reason_api"] = cat["api"]
    if not cat["subs"]:
        ctx.user_data["br_sub_key"]   = "N/A"
        ctx.user_data["br_sub_label"] = "N/A"
        await query.edit_message_text(
            f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n📝 Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return BR_MSG
    await query.edit_message_text(
        f"✅ {cat['emoji']} <b>{cat['label']}</b>\n\n📋 Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "BSUB"), parse_mode="HTML")
    return BR_SUB

async def br_subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text("📋 Select reason:", reply_markup=_build_full_cat_keyboard("BCAT"))
        return BR_CAT
    if len(parts) < 3: return BR_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return BR_SUB
    sub_label = next((s[1] for s in cat["subs"] if s[0] == sub_key), "N/A")
    ctx.user_data["br_sub_key"]   = sub_key
    ctx.user_data["br_sub_label"] = sub_label
    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']} → <b>{sub_label}</b>\n\n📝 Optional message or send <code>skip</code>:",
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
    uid = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT: raise ValueError
    except:
        await update.message.reply_text(f"❌ Invalid! 1–{MAX_REPORTS_PER_ACCOUNT}:"); return BR_COUNT

    lock = get_user_lock(uid)
    if lock.locked():
        await update.message.reply_text("⚠️ You already have a job running.")
        return ConversationHandler.END
    async with lock:
        return await _br_execute_inner(update, ctx, count)

async def _br_execute_inner(update, ctx, count):
    target_raw = ctx.user_data["br_entity_id"]
    target_name= ctx.user_data.get("br_name", target_raw)
    cat_label  = ctx.user_data["br_cat_label"]
    sub_label  = ctx.user_data.get("br_sub_label", "N/A")
    reason_api = ctx.user_data["br_reason_api"]
    custom_msg = ctx.user_data.get("br_custom_msg", "")

    auth_pairs: List[Tuple[str, TelegramClient]] = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c: auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!"); return ConversationHandler.END

    total = count * len(auth_pairs)
    await update.message.reply_text(
        f"🚀 <b>BOT REPORT</b>\n🤖 {target_name}\n⚠️ {cat_label} → {sub_label}\n"
        f"📊 {total} ({len(auth_pairs)} × {count})\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    resolved: Dict[str, object] = {}
    for phone, client in auth_pairs:
        try:
            identifier = target_raw.lstrip("@")
            ent = await client.get_entity(identifier)
            resolved[phone] = ent
        except Exception as e:
            await update.message.reply_text(f"❌ <code>{phone[-4:]}</code>: {str(e)[:40]}", parse_mode="HTML")
            resolved[phone] = None

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0
    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            shot_num += 1
            bot_entity = resolved.get(phone)
            if bot_entity is None:
                total_fail += 1; per_acc_fail[phone] += 1; continue
            ok, status = await _report_bot_methods(phone, bot_entity, reason_api, custom_msg, sub_label)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ BOT {shot_num}/{total} | R{r+1} | <code>{phone[-4:]}</code> → {status}", parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ BOT {shot_num}/{total} | R{r+1} | <code>{phone[-4:]}</code> → {status}", parse_mode="HTML")
                if "FloodWait" in status:
                    try:
                        wait = int(status.split()[1].replace("s",""))
                        await asyncio.sleep(min(wait + 2, 300))
                    except: await asyncio.sleep(60)
            if acc_idx < len(auth_pairs) - 1:
                await asyncio.sleep(round_robin_delay())
        if r < count - 1:
            await asyncio.sleep(account_switch_delay())

    rate = (total_ok * 100 / total) if total > 0 else 0
    breakdown = "\n".join(
        f"  📱 <code>{p[-4:]}</code> → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>BOT REPORT COMPLETE</b>\n\n"
        f"🤖 {target_name}\n⚠️ {cat_label} → {sub_label}\n"
        f"✅ {total_ok} | ❌ {total_fail} | 📈 {rate:.1f}%\n\nPer-account:\n{breakdown}",
        parse_mode="HTML")
    return ConversationHandler.END

async def _report_bot_methods(phone, bot_entity, reason_api, custom_msg, sub_label="") -> Tuple[bool, str]:
    client = await ensure_connected(phone)
    if not client:
        return (False, "Account disconnected")
    proxy = account_proxy_map.get(phone)
    methods_tried = []
    try:
        await asyncio.sleep(random.uniform(0.15, 0.4))
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

    try:
        await asyncio.sleep(random.uniform(0.2, 0.5))
        client = await ensure_connected(phone)
        if client:
            r = await client(functions.messages.ReportSpamRequest(peer=bot_entity))
            if r:
                mark_proxy_result(proxy, True)
                return (True, "Success (M2: ReportSpam)")
            methods_tried.append("M2")
    except Exception as e:
        methods_tried.append(f"M2-{type(e).__name__}")

    try:
        await asyncio.sleep(random.uniform(0.2, 0.5))
        client = await ensure_connected(phone)
        if client:
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

    try:
        await asyncio.sleep(random.uniform(0.2, 0.5))
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
            "📧 <b>Gmail BLAST</b> — Step 1/5\n\n✏️ Enter Email Subject:", parse_mode="HTML")
    else:
        ctx.user_data.clear()
        await update.message.reply_text(
            "📧 <b>Gmail BLAST Mode</b> — Step 1/5\n\n✏️ Enter Email Subject:", parse_mode="HTML")
    return MAIL_SUBJECT

async def receive_mail_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["mail_subject"] = update.message.text.strip()
    await update.message.reply_text("📝 <b>Step 2/5</b> — Enter Email Body:", parse_mode="HTML")
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
        await update.message.reply_text("⚠️ Invalid email!"); return MAIL_RECIPIENT
    ctx.user_data["mail_recipient"] = recipient
    await update.message.reply_text(
        f"✅ Recipient: <code>{recipient}</code>\n\n"
        f"🔢 <b>Step 5/5</b> — Blast count?\n"
        f"(All {len(GMAIL_ACCOUNTS)} accounts fire each round)\n\nEnter 1–50:", parse_mode="HTML")
    return MAIL_BLAST_COUNT

async def receive_blast_count(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= 50: raise ValueError
    except:
        await update.message.reply_text("❌ Invalid! 1–50:"); return MAIL_BLAST_COUNT
    ctx.user_data["mail_blast_count"] = count
    recipient = ctx.user_data["mail_recipient"]

    lock = get_user_lock(uid)
    if lock.locked():
        await update.message.reply_text("⚠️ You already have a job running.")
        return ConversationHandler.END
    async with lock:
        await update.message.reply_text(
            f"🚀 <b>BLAST STARTING</b>\n📬 {recipient}\n🔁 Rounds: {count}\n"
            f"📧 Accounts/round: {len(GMAIL_ACCOUNTS)}\n📊 Total: {count*len(GMAIL_ACCOUNTS)}\n⏳ Firing...",
            parse_mode="HTML")
        total_ok, total_fail, details = await do_gmail_blast_n_times(ctx, count, update_msg=update.message)
        summary = (
            f"📬 <b>BLAST COMPLETE</b> → {recipient}\n\n"
            f"✅ Sent: {total_ok}\n❌ Failed: {total_fail}\n"
            f"📊 Total: {count*len(GMAIL_ACCOUNTS)}\n")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Blast Again", callback_data="RESEND"),
            InlineKeyboardButton("✅ Done",         callback_data="DONE")]])
        if len(details) > 3500: details = details[:3500] + "\n...(truncated)"
        await update.message.reply_text(summary + "\n" + details, reply_markup=keyboard, parse_mode="HTML")
    return MAIL_RESEND

async def gmail_resend_or_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    if query.data == "DONE":
        ctx.user_data.clear()
        await query.edit_message_text("✅ All done! Use /start.")
        return ConversationHandler.END
    recipient = ctx.user_data.get("mail_recipient","N/A")
    count     = ctx.user_data.get("mail_blast_count", 1)

    lock = get_user_lock(uid)
    if lock.locked():
        await query.edit_message_text("⚠️ You already have a job running.")
        return ConversationHandler.END
    async with lock:
        await query.edit_message_text(
            f"🔄 <b>RE-BLAST</b> → {recipient} × {count}\n⏳ Firing...", parse_mode="HTML")
        total_ok, total_fail, details = await do_gmail_blast_n_times(ctx, count)
        summary = (
            f"📬 <b>RE-BLAST COMPLETE</b> → {recipient}\n\n"
            f"✅ {total_ok} | ❌ {total_fail} | 📊 {count*len(GMAIL_ACCOUNTS)}\n")
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
    db_load_sudo()
    db_load_proxy_health()
    db_load_gmails()
    load_accounts_from_db()
    for phone in list(accounts.keys()):
        try:
            await ensure_connected(phone)
        except: pass
    add_log(f"✅ Startup complete — {len(accounts)} accounts, {len(GMAIL_ACCOUNTS)} gmails, {len(sudo_users)} sudo")

async def post_shutdown(application):
    add_log("🛑 Shutting down — disconnecting clients...")
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
    if not mongo_init():
        logger.error("❌ MongoDB connection failed. Aborting.")
        sys.exit(1)

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

    addmail_conv = ConversationHandler(
        entry_points=[CommandHandler("addmail", addmail_cmd)],
        states={
            AM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, am_email)],
            AM_PASS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, am_pass)],
            AM_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, am_name)],
        },
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

    groupreport_conv = ConversationHandler(
        entry_points=[CommandHandler("groupreport", groupreport_cmd)],
        states={
            GR_GRP_LINK:   [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_receive_grp_link)],
            GR_MSG_LINK:   [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_receive_msg_link)],
            GR_REASON_CAT: [CallbackQueryHandler(gr_category_selected, pattern="^GRCAT\\|")],
            GR_REASON_SUB: [CallbackQueryHandler(gr_subcategory_selected, pattern="^GRSUB\\|")],
            GR_CUSTOM_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_receive_custom_msg)],
            GR_COUNT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, gr_execute)],
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
    app.add_handler(CommandHandler("rmmail",        rmmail_cmd))
    app.add_handler(CommandHandler("maillist",      maillist_cmd))

    app.add_handler(add_conv)
    app.add_handler(rm_conv)
    app.add_handler(addmail_conv)
    app.add_handler(ar_conv)
    app.add_handler(br_conv)
    app.add_handler(report_conv)
    app.add_handler(groupreport_conv)
    app.add_handler(gmail_conv)
    app.add_handler(CallbackQueryHandler(menu_router, pattern="^MENU\\|"))

    logger.info(f"⚡ ULTIMATE REPORTER v{BOT_VERSION} — RUNNING")
    add_log(f"⚡ Bot v{BOT_VERSION} online (proxy={'ON' if PROXY_ENABLED else 'OFF'})")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
