"""
╔══════════════════════════════════════════════════════════════════════╗
║   ⚡ ULTIMATE TELEGRAM REPORTER v15.0 — CYBER JUSTICE ELITE++ ⚡     ║
║──────────────────────────────────────────────────────────────────────║
║   ✅ /report — MULTIPLE message links + skip (all at once batch)     ║
║   ✅ /groupreport — NEW! Report msg via group's 3-dot menu flow       ║
║   ✅ Faster reporting (smart reduced delays)                         ║
║   ✅ Zero "Cannot send requests while disconnected" errors           ║
║   ✅ Auto-reconnect on every report attempt                          ║
║   ✅ /addaccount → Phone+OTP OR Pyrogram/Telethon session string     ║
║   ✅ POWERFUL multi-paragraph contextual report messages             ║
║   ✅ /logs sends actual log FILE                                     ║
║   ✅ /restart command + button (sessions preserved)                  ║
║   ✅ Round-robin firing, 6 PFP methods, full TG category tree        ║
║   ✅ Atomic JSON, sudo system, gmail blast                           ║
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
MAX_MSG_LINKS           = 50  # max message links accepted per /report or /groupreport session
BOT_VERSION             = "15.0"

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
        return f"{C.DIM}{ts}{C.RESET} {lvl} {record.getMessage()}"

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColorFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("UltimateReporter")

# ══════════════════════════════════════════════════════════════════════
# 🌐 GLOBALS
# ══════════════════════════════════════════════════════════════════════
accounts: Dict[str, TelegramClient] = {}
account_proxy_map: Dict[str, dict]  = {}
proxy_cursor = 0
proxy_health: Dict[str, dict]       = {}

sudo_users: set = set()
sudo_info: Dict[int, dict] = {}

live_logs: List[str] = []
report_stats = {"total": 0, "success": 0, "failed": 0, "start_time": None}

# ══════════════════════════════════════════════════════════════════════
# 🎯 POWERFUL REPORT MESSAGES (SAME AS OLD — DO NOT CHANGE)
# ══════════════════════════════════════════════════════════════════════
REPORT_PREFIXES = [
    "URGENT — Immediate moderation review required.",
    "FORMAL COMPLAINT — Multiple users affected.",
    "SAFETY ALERT — Vulnerable users (minors/elderly) targeted.",
    "LEGAL NOTICE — Content violates Telegram ToS and applicable laws.",
    "ESCALATION — Previous reports apparently ignored, repeat offender.",
    "MASS REPORT — Filed on behalf of affected community members.",
    "CHILD SAFETY — Immediate intervention requested.",
    "CYBERSECURITY THREAT — Phishing/malware actively distributed.",
    "FRAUD ALERT — Victims have suffered financial loss.",
    "HUMAN RIGHTS VIOLATION — Hate speech and incitement documented.",
]

REALISTIC_REPORT_MSGS = [
    "This account/content is actively engaged in distributing harmful material that violates Telegram's Terms of Service. I have personally witnessed multiple violations and documented evidence is available upon request. Several users in my community have already been victimized. Immediate removal is critical to prevent further harm.",
    "I am submitting this report as a deeply concerned member of the Telegram community. The behavior I am reporting is not an isolated incident — it is a recurring pattern that has caused measurable harm to real users, including minors. The content/account in question must be reviewed and terminated under Telegram's community guidelines without delay.",
    "Multiple verified victims have reached out to me regarding this account/content. The violations include deception, manipulation, and outright illegal activity. Screenshots, chat logs, and transaction records are available. As a long-standing Telegram user, I urge the trust & safety team to escalate this case to the highest priority queue.",
    "This is a coordinated abuse case that I have been tracking for several weeks. The reported entity has changed identities multiple times to evade enforcement but continues the same pattern of violation. I request that the moderation team review the full activity history, not just the most recent posts, before making a decision.",
    "The content reported here is causing real-world harm. Vulnerable users — including children, elderly people, and victims of previous scams — are being actively targeted. Telegram's responsibility under EU DSA, US Section 230 voluntary moderation, and Indian IT Rules 2021 makes immediate removal mandatory. Please act now.",
    "I work in cybersecurity and have professionally analyzed this content. It contains clear indicators of malicious intent — phishing links, malware payloads, social-engineering scripts, or coordinated inauthentic behavior. I am willing to share my full forensic report with the Telegram trust & safety team upon request.",
    "This report is filed on behalf of myself and at least a dozen other users in my circle who have been directly affected. The violations are systematic and the perpetrator shows no intention of stopping. We have collectively decided that escalation through the official report channel is the only remaining option before involving law-enforcement.",
    "The reported account/channel is operating in clear violation of Telegram's published rules on prohibited content. As a paying Telegram Premium user, I expect the platform to enforce its own policies consistently. Please confirm that this report has been reviewed by a human moderator and not auto-dismissed by an algorithm.",
    "I have already reported this content through in-app channels with no visible action taken. This is my escalated complaint. If no action is taken within a reasonable timeframe, I and other affected users will be forced to file complaints with national regulators (CERT-In, FBI IC3, EU DSA coordinators) and pursue civil remedies.",
    "The reported entity is part of an organized network — not a lone actor. Removing only this surface-level account will not solve the problem. I urge the moderation team to investigate the linked accounts, channels, and bots that operate together. I can provide a full network map if requested.",
]

CONTEXT_PHRASES = [
    "Evidence has been preserved and timestamped.",
    "Multiple witnesses are willing to provide statements.",
    "This violates clauses regarding harmful content, harassment, and illegal activity.",
    "The pattern of behavior shows clear malicious intent, not accidental violation.",
    "I am available for follow-up questions from the moderation team.",
    "A full chronological log of incidents can be provided on request.",
    "This is my third report on this exact entity — prior reports yielded no action.",
    "Affected users include minors, which elevates this to a child-safety issue.",
    "Financial damages from this entity are already in five figures across known victims.",
    "The reported account is using stolen identity/photos of real people.",
]

# ══════════════════════════════════════════════════════════════════════
# 📋 FULL TELEGRAM REPORT CATEGORY TREE (SAME AS OLD — DO NOT CHANGE)
# ══════════════════════════════════════════════════════════════════════
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
 # New states for /groupreport
 GR_GRP_LINK, GR_MSG_LINK, GR_REASON_CAT, GR_REASON_SUB, GR_CUSTOM_MSG, GR_COUNT,
) = range(31)

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
            parts.append(f"{base_msg.strip()} {pool_msg}")
        else:
            parts.append(f"{pool_msg} Additional context from reporter: {base_msg.strip()}")
    else:
        parts.append(pool_msg)

    parts.append(context)
    parts.append(f"Reference ID: TG-{random.randint(100000, 999999)}-{int(time.time()) % 10000}")

    final = " ".join(parts)
    if len(final) > 480:
        final = final[:477] + "..."
    return final

# ══════════════════════════════════════════════════════════════════════
# 🔧 TELETHON CLIENT BUILDER + CONNECT
# ══════════════════════════════════════════════════════════════════════
def build_client(session, proxy_cfg: Optional[dict]) -> TelegramClient:
    kwargs = dict(
        device_model="iPhone 14 Pro",
        system_version="iOS 16.5",
        app_version="9.6.3",
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
                new_client = build_client(sess, None)
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

    try:
        client = build_client(StringSession(session_str), proxy)
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
            client = build_client(StringSession(telethon_str), proxy)
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
    """Parse multiple message links from a single text input.
       Returns: (valid_list[(ident, msg_id, raw_link)], invalid_lines[])"""
    valid: List[Tuple[str, int, str]] = []
    invalid: List[str] = []
    # split by whitespace OR newline
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
            await asyncio.sleep(random.uniform(0.8, 2.0))  # faster
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
# 🚀 CORE MESSAGE REPORT ENGINE — MULTI-MSG BATCH SUPPORT
# ══════════════════════════════════════════════════════════════════════
async def send_report_batch(phone, channel_id, msg_ids: List[int], reason_api, custom_msg,
                             link_type="username", sub_label="") -> Tuple[bool, str]:
    """
    Report MULTIPLE message IDs from the same chat in ONE API call.
    This is much faster than reporting them one-by-one and Telegram supports it natively.
    """
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
        await asyncio.sleep(random.uniform(0.15, 0.5))  # faster

        # M1: standard messages.report with batch of IDs
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

        # M2: prefetch + report batch
        await asyncio.sleep(random.uniform(0.3, 0.7))
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

        # M3: account.reportPeer (peer-level fallback)
        await asyncio.sleep(random.uniform(0.3, 0.7))
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

        # M4: re-resolve + report
        await asyncio.sleep(random.uniform(0.3, 0.7))
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

        # M5: per-message fallback (last resort)
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
                        await asyncio.sleep(random.uniform(0.2, 0.5))
                    except errors.FloodWaitError as e:
                        return (False, f"FloodWait {e.seconds}s")
                    except Exception:
                        continue
            if per_msg_ok > 0:
                mark_proxy_result(proxy, True)
                add_log(f"✅ M5 OK: {phone[-4:]} ({per_msg_ok}/{len(msg_ids_int)} per-msg)")
                return (True, f"Success (M5: per-msg fallback, {per_msg_ok}/{len(msg_ids_int)})")
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
# 📸 NUCLEAR PFP REPORT (unchanged behavior)
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
            await asyncio.sleep(random.uniform(0.2, 0.6))
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
                await asyncio.sleep(random.uniform(0.3, 0.7))
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
        await asyncio.sleep(random.uniform(0.3, 0.8))
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
        await asyncio.sleep(random.uniform(0.4, 0.9))
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
        await asyncio.sleep(random.uniform(0.3, 0.7))
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
        await asyncio.sleep(random.uniform(0.3, 0.6))
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
# ⏱ DELAYS — Slightly faster than v14, still safe
# ══════════════════════════════════════════════════════════════════════
def smart_delay(i, total) -> float:
    base  = random.uniform(2.5, 6)
    extra = random.uniform(0, 3) if random.random() < 0.3 else 0
    if i > total * 0.7: extra += random.uniform(1, 2.5)
    return base + extra

def account_switch_delay() -> float:
    return random.uniform(2.5, 6)   # was 5–12

def round_robin_delay() -> float:
    return random.uniform(1.5, 3.5) # was 3–7

# ══════════════════════════════════════════════════════════════════════
# 📧 GMAIL (unchanged)
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
            await asyncio.sleep(random.uniform(1.5, 3))
    return (total_ok, total_fail, "\n\n".join(details_all))

# ══════════════════════════════════════════════════════════════════════
# 🎬 ANIMATED START + MAIN MENU
# ══════════════════════════════════════════════════════════════════════
async def animated_start(message):
    frames = [
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▱▱▱▱▱▱▱▱▱▱  0%",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▱▱▱▱▱▱▱▱  20%\n\n🔧 Loading core modules...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▱▱▱▱▱▱  40%\n\n🌐 Verifying network...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▱▱▱▱  60%\n\n📸 Arming PFP nuclear engine...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▰▰▱▱  80%\n\n🛡️ Engaging stealth mode...",
        "✨ <b>Booting Cyber-Justice Engine...</b>\n\n▰▰▰▰▰▰▰▰▰▰  100%\n\n🚀 ONLINE — ready to strike 😎",
    ]
    msg = await message.reply_text(frames[0], parse_mode="HTML")
    for f in frames[1:]:
        await asyncio.sleep(0.35)
        try:
            await msg.edit_text(f, parse_mode="HTML")
        except Exception:
            pass
    await asyncio.sleep(0.25)
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
         InlineKeyboardButton("🌐 Proxy Status",   callback_data="MENU|proxystatus")],
        [InlineKeyboardButton("🔄 Reload Proxies", callback_data="MENU|reloadproxies"),
         InlineKeyboardButton("ℹ️ Help",           callback_data="MENU|help")],
        [InlineKeyboardButton("🧹 Clear Logs",     callback_data="MENU|clearlogs"),
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
        f"<i>CYBER JUSTICE ELITE++</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ Access  : {owner_tag}\n"
        f"🌐 Proxy   : {proxy_status}\n"
        f"📱 Accounts: {len(accounts)}\n"
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
        "groupreport":   ("👥 <b>Group Report</b>\n\nUse /groupreport — reports via group's 3-dot menu flow with selected message context.", "/groupreport"),
        "accountreport": ("👤 <b>Account / PFP Report</b>\n\nUse /accountreport — 6-method nuclear PFP.", "/accountreport"),
        "botreport":     ("🤖 <b>Bot Report</b>\n\nUse /botreport — full Telegram report categories.", "/botreport"),
        "massgmail":     ("📧 <b>Mass Gmail Blast</b>\n\nUse /massgmail — fires all Gmail accounts × N rounds.", "/massgmail"),
        "addaccount":    ("➕ <b>Add Telegram Account</b>\n\nUse /addaccount — supports phone+OTP <b>OR</b> session string.", "/addaccount"),
        "rmaccount":     ("🗑️ <b>Remove Account</b>\n\nUse /rmaccount.", "/rmaccount"),
        "allaccounts":   ("📋 Use /allaccounts.", "/allaccounts"),
        "logs":          ("📊 Use /logs — sends actual log <b>FILE</b>.", "/logs"),
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
            f"🌐 Proxy: {proxy_status} | 📱 Accounts: {len(accounts)}\n"
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
        "🎯 /report — Report messages (MULTI-LINK + skip, batched per chat)\n"
        "👥 /groupreport — Group-level report via 3-dot menu flow\n"
        "📸 /accountreport — Nuclear PFP report\n"
        "🤖 /botreport — Report a bot (full TG categories)\n"
        "📧 /massgmail — Gmail blast × N\n"
        "➕ /addaccount — Add account (Phone+OTP <b>OR</b> Session String)\n"
        "🗑️ /rmaccount — Remove account\n"
        "📋 /allaccounts — List accounts\n"
        "🌐 /proxystatus — Proxy health\n"
        "🔄 /reloadproxies — Refresh proxy pool\n"
        "⚙️ /proxyon /proxyoff — Toggle proxy (owner)\n"
        "📊 /logs — Send activity log <b>FILE</b>\n"
        "🧹 /clearlogs — Clear logs & stats\n"
        "♻️ /restart — Restart bot (sessions preserved)\n"
        "❌ /cancel — Cancel current flow\n\n"
        "👑 Owner: /sudo /rmsudo /sudolist\n\n"
        "💡 <b>/report multi-link tip:</b>\n"
        "  • Paste multiple message links (newline or space-separated)\n"
        "  • Send <code>skip</code> when done OR if you only had one link\n",
        parse_mode="HTML"
    )

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    add_log("❌ User cancelled flow")
    await update.message.reply_text("❌ Cancelled.\nUse /start to open the menu again.")
    return ConversationHandler.END

async def logs_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    txt = f"📊 <b>ACTIVITY STATS</b>\n\n{get_stats()}\n\n<b>Recent logs:</b>\n<pre>{get_logs(30)}</pre>"
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
                    document=f,
                    filename=activity_file.name,
                    caption=f"📋 Activity log — {today}\nSize: {activity_file.stat().st_size} bytes"
                )
            sent_any = True
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not send activity log: {e}")

    if reports_file.exists() and reports_file.stat().st_size > 0:
        try:
            with open(reports_file, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=reports_file.name,
                    caption=f"🎯 Reports log — {today}\nSize: {reports_file.stat().st_size} bytes"
                )
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
                try: await asyncio.wait_for(client.connect(), timeout=8)
                except: pass
            auth   = await client.is_user_authorized() if client.is_connected() else False
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
    txt += f"Pool: {len(PROXY_LIST)} total\n\n"
    shown = 0
    for p in PROXY_LIST:
        if shown >= 20:
            txt += f"\n…and {len(PROXY_LIST) - shown} more"
            break
        k = _proxy_key(p)
        h = proxy_health.get(k, {"ok": 0, "fail": 0, "bad": False})
        flag = "🚫 BAD" if h.get("bad") else "🟢 OK"
        txt += f"{flag} {k}\n   ✅ {h.get('ok',0)} | ❌ {h.get('fail',0)}\n"
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
        "🟢 Proxy mode: ENABLED\n\n"
        "⚠️ Free proxies are often dead — if you see connection errors, run /proxyoff.",
        parse_mode="HTML")

async def proxyoff_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    global PROXY_ENABLED
    PROXY_ENABLED = False
    account_proxy_map.clear()
    await update.message.reply_text(
        "⚡ Proxy mode: DISABLED\n\n"
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
        f"✅ Sudo Granted!\n👤 <b>{target_name}</b>\n🆔 <code>{target_id}</code>", parse_mode="HTML")

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
        f"🔒 Sudo Revoked!\n👤 <b>{name}</b>\n🆔 <code>{target_id}</code>", parse_mode="HTML")

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
        save_accounts()
        add_log(f"✅ Added via session string: {ident}")
        await wait_msg.edit_text(
            f"✅ <b>Logged in via session string!</b>\n"
            f"📱 {ident}\n"
            f"📊 Total accounts: {len(accounts)}",
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
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=p_hash)
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        save_accounts(); add_log(f"✅ Added: {phone}")
        await update.message.reply_text(f"✅ <b>Added!</b>\n📱 {phone}\nTotal: {len(accounts)}", parse_mode="HTML")
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
    proxy  = ctx.user_data.get("temp_proxy")
    try:
        await client.sign_in(password=update.message.text.strip())
        accounts[phone] = client
        if proxy: account_proxy_map[phone] = proxy
        save_accounts(); add_log(f"✅ Added (2FA): {phone}")
        await update.message.reply_text(f"✅ <b>Added (2FA)!</b>\n📱 {phone}", parse_mode="HTML")
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
        save_accounts(); add_log(f"🗑 Removed: {phone}")
        await update.message.reply_text(f"✅ Removed <code>{phone}</code>\nRemaining: {len(accounts)}", parse_mode="HTML")
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
# 🎯 MESSAGE REPORT FLOW  (/report)  — MULTI-LINK + SKIP
# ══════════════════════════════════════════════════════════════════════
async def report_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats()
    ctx.user_data["msg_links_buf"] = []  # list of (ident, msg_id, raw)
    add_log("🎯 Report flow started")
    await update.message.reply_text(
        f"🎯 <b>REPORT FLOW — Step 1/7</b>\n\n"
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
            f"📥 <b>Step 2/7</b> — Send <b>MESSAGE LINK(s)</b>:\n\n"
            f"  • <code>t.me/groupname/123</code>\n"
            f"  • <code>t.me/c/1234567890/123</code>\n\n"
            f"💡 You can paste <b>multiple links</b> at once (newline/space separated),\n"
            f"or send them one by one — when done, type <code>skip</code> (or <code>done</code>) to continue.\n"
            f"Max {MAX_MSG_LINKS} links.",
            parse_mode="HTML")
    else:
        await update.message.reply_text(f"🔄 Joining private group...\n<code>{link}</code>", parse_mode="HTML")
        ok, fail = await join_group_all(ident, ltype)
        if ok == 0:
            await update.message.reply_text("❌ No accounts could join! Check link/invite."); return ConversationHandler.END
        await update.message.reply_text(
            f"✅ Join complete!\n✅ {ok} | ❌ {fail}\n\n"
            f"📥 <b>Step 2/7</b> — Send <b>MESSAGE LINK(s)</b>:\n\n"
            f"💡 You can paste <b>multiple links</b> at once (newline/space separated),\n"
            f"or send them one by one — when done, type <code>skip</code> (or <code>done</code>) to continue.\n"
            f"Max {MAX_MSG_LINKS} links.",
            parse_mode="HTML")
    return MSG_LINK

async def receive_msg_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw_text = update.message.text.strip()
    buf: List[Tuple[str, int, str]] = ctx.user_data.get("msg_links_buf", [])

    # User wants to finish adding links
    if raw_text.lower() in ("skip", "done", "/skip", "/done"):
        if not buf:
            await update.message.reply_text(
                "⚠️ You haven't added any message link yet!\n"
                "Send at least one message link, then type <code>skip</code>.",
                parse_mode="HTML")
            return MSG_LINK
        # Proceed to reason
        ctx.user_data["msg_links_buf"] = buf
        summary = "\n".join(f"  {i+1}. <code>{ln}</code>" for i, (_,_,ln) in enumerate(buf))
        await update.message.reply_text(
            f"✅ Collected <b>{len(buf)}</b> message link(s):\n{summary}\n\n"
            f"📋 <b>Step 3/7</b> — Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"),
            parse_mode="HTML")
        return REASON_CAT

    # Otherwise, parse links from this message (could be 1 or many)
    new_valid, invalid = parse_multi_msg_links(raw_text)
    if not new_valid:
        await update.message.reply_text(
            "❌ No valid message link found in your input.\n"
            "Send a link like <code>t.me/groupname/123</code> or type <code>skip</code> to finish.",
            parse_mode="HTML")
        return MSG_LINK

    # Dedup against existing buf
    existing_keys = {f"{i}:{m}" for i, m, _ in buf}
    added = 0
    for ident, mid, ln in new_valid:
        k = f"{ident}:{mid}"
        if k in existing_keys:
            continue
        if len(buf) >= MAX_MSG_LINKS:
            break
        buf.append((ident, mid, ln))
        existing_keys.add(k)
        added += 1

    ctx.user_data["msg_links_buf"] = buf
    add_log(f"📥 Msg links: +{added} (total {len(buf)})")

    invalid_note = ""
    if invalid:
        invalid_note = f"\n⚠️ Skipped {len(invalid)} invalid line(s)."
    reached_cap = ""
    if len(buf) >= MAX_MSG_LINKS:
        reached_cap = f"\n🚫 Cap reached: {MAX_MSG_LINKS} links max."

    await update.message.reply_text(
        f"✅ Added {added} new link(s). Total queued: <b>{len(buf)}</b>{invalid_note}{reached_cap}\n\n"
        f"➕ Send more message links, OR type <code>skip</code> (or <code>done</code>) to continue.",
        parse_mode="HTML")
    return MSG_LINK

async def category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2:
        return REASON_CAT
    cat_key = parts[1]
    if cat_key not in FULL_REPORT_CATEGORIES:
        return REASON_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data["reason_cat"] = cat_key
    ctx.user_data["reason_api"] = cat["api"]
    ctx.user_data["cat_label"]  = f"{cat['emoji']} {cat['label']}"
    ctx.user_data["sub_label"]  = ""

    if cat["direct"]:
        if not cat["needs_msg"]:
            ctx.user_data["custom_msg"] = ""
            await query.edit_message_text(
                f"✅ {cat['emoji']} {cat['label']}\n\n"
                f"🔢 <b>Step 6/7</b> — Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
                parse_mode="HTML")
            return COUNT
        await query.edit_message_text(
            f"✅ {cat['emoji']} {cat['label']}\n\n"
            f"📝 <b>Step 5/7</b> — Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return CUSTOM_MSG

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
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("CAT"))
        return REASON_CAT
    if len(parts) < 3:
        return REASON_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return REASON_SUB
    sub_label = next((lbl for k, lbl in (cat["subs"] or []) if k == sub_key), "N/A")
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
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1–{MAX_REPORTS_PER_ACCOUNT}:")
            return COUNT
    except ValueError:
        await update.message.reply_text("⚠️ Numbers only:"); return COUNT

    buf: List[Tuple[str, int, str]] = ctx.user_data.get("msg_links_buf", [])
    if not buf:
        await update.message.reply_text("❌ No message links queued. Restart with /report.")
        return ConversationHandler.END

    # Group msg_ids by chat ident (in case user pasted links from multiple chats)
    grouped: Dict[str, List[Tuple[int, str]]] = {}
    for ident, mid, ln in buf:
        grouped.setdefault(ident, []).append((mid, ln))

    link_type  = ctx.user_data["grp_type"]
    reason_api = ctx.user_data["reason_api"]
    custom_msg = ctx.user_data.get("custom_msg", "")
    cat_lbl    = ctx.user_data.get("cat_label", "Reason")
    sub_lbl    = ctx.user_data.get("sub_label", "")

    auth_pairs = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c:
            auth_pairs.append((phone, c))

    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!")
        return ConversationHandler.END

    # Each (chat × round × account) = 1 batched report containing ALL msg_ids for that chat
    chats_count    = len(grouped)
    total_planned  = chats_count * len(auth_pairs) * count
    total_msgs     = len(buf)
    report_stats["total"] = total_planned
    report_stats["start_time"] = datetime.now()
    join_note = "Public (no join)" if link_type == "username" else "Private (joined)"

    msg_summary = "\n".join(
        f"  • Chat <code>{ident}</code> → {len(mids)} msg(s)"
        for ident, mids in grouped.items())

    await update.message.reply_text(
        f"🚀 <b>REPORTING STARTED (BATCHED + ROUND-ROBIN) — Step 7/7</b>\n\n"
        f"📊 Total report calls: {total_planned}\n"
        f"📩 Total messages reported per call (max): up to {max(len(v) for v in grouped.values())}\n"
        f"🗂 Chats: {chats_count} | 📨 Messages queued: {total_msgs}\n"
        f"📱 Accounts: {len(auth_pairs)} × {count} rounds\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
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
                    total_ok += 1; per_acc_ok[phone] += 1; update_stats(True)
                    log_report_file(phone, f"{chat_ident}/{msg_ids_only}", f"{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                    try:
                        await update.message.reply_text(
                            f"✅ {shot_num}/{total_planned} | R{r+1} | 📱 {phone[-4:]} | {len(msg_ids_only)} msg → {status}",
                            parse_mode="HTML")
                    except: pass
                else:
                    total_fail += 1; per_acc_fail[phone] += 1; update_stats(False)
                    log_report_file(phone, f"{chat_ident}/{msg_ids_only}", f"{cat_lbl}/{sub_lbl}", "FAILED", status)
                    try:
                        await update.message.reply_text(
                            f"❌ {shot_num}/{total_planned} | R{r+1} | 📱 {phone[-4:]} | {len(msg_ids_only)} msg → {status}",
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

    elapsed = (datetime.now() - report_stats["start_time"]).seconds
    rate    = (total_ok / total_planned) * 100 if total_planned > 0 else 0
    add_log(f"🎉 Done: {total_ok}/{total_planned} ({rate:.1f}%)")

    breakdown = "\n".join(
        f"  📱 {p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
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
        f"⏱ Time: {elapsed//60}m {elapsed%60}s\n"
        f"📨 Total messages targeted: {total_msgs}\n\n"
        f"<b>Per-account breakdown:</b>\n{breakdown}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n\n"
        f"📧 Want to also blast Gmail?",
        reply_markup=keyboard, parse_mode="HTML")
    return MAIL_SUBJECT

# ══════════════════════════════════════════════════════════════════════
# 👥 /groupreport — Group-level 3-dot menu flow, ties reason to specific msg
# ══════════════════════════════════════════════════════════════════════
async def groupreport_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_authorized(update.effective_user.id): return ConversationHandler.END
    if not accounts:
        await update.message.reply_text("⚠️ No accounts! Use /addaccount."); return ConversationHandler.END
    active = await count_active()
    if active == 0:
        await update.message.reply_text("⚠️ No active accounts!"); return ConversationHandler.END
    ctx.user_data.clear(); reset_stats()
    add_log("👥 Group report flow started")
    await update.message.reply_text(
        f"👥 <b>GROUP REPORT FLOW — Step 1/6</b>\n\n"
        f"This flow mimics the group's 3-dot menu → Report option,\n"
        f"so the chosen reason is anchored to the <b>specific message</b> you provide.\n\n"
        f"✅ Active: {active}/{len(accounts)} accounts\n\n"
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
            f"ℹ️ Public group — direct report (no join needed).\n\n"
            f"📥 <b>Step 2/6</b> — Send <b>MESSAGE LINK</b> (the message you want to anchor the report to):\n"
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
            f"📥 <b>Step 2/6</b> — Send <b>MESSAGE LINK</b>:", parse_mode="HTML")
    return GR_MSG_LINK

async def gr_receive_msg_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    link  = update.message.text.strip()
    ident, msg_id, err = parse_message_link(link)
    if err:
        await update.message.reply_text(f"❌ {err}\nTry again or /cancel"); return GR_MSG_LINK
    ctx.user_data.update({"gr_msg_ident": ident, "gr_msg_id": msg_id, "gr_msg_link": link})
    add_log(f"📥 GroupReport msg: {link} (ID:{msg_id})")
    await update.message.reply_text(
        "📋 <b>Step 3/6</b> — Select group-report reason (same options as /report):",
        reply_markup=_build_full_cat_keyboard("GRCAT"),
        parse_mode="HTML")
    return GR_REASON_CAT

async def gr_category_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) < 2: return GR_REASON_CAT
    cat_key = parts[1]
    if cat_key not in FULL_REPORT_CATEGORIES: return GR_REASON_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data["gr_reason_cat"] = cat_key
    ctx.user_data["gr_reason_api"] = cat["api"]
    ctx.user_data["gr_cat_label"]  = f"{cat['emoji']} {cat['label']}"
    ctx.user_data["gr_sub_label"]  = ""

    if cat["direct"]:
        if not cat["needs_msg"]:
            ctx.user_data["gr_custom_msg"] = ""
            await query.edit_message_text(
                f"✅ {cat['emoji']} {cat['label']}\n\n"
                f"🔢 <b>Step 6/6</b> — Reports per account (1–{MAX_REPORTS_PER_ACCOUNT}):",
                parse_mode="HTML")
            return GR_COUNT
        await query.edit_message_text(
            f"✅ {cat['emoji']} {cat['label']}\n\n"
            f"📝 <b>Step 5/6</b> — Optional message or send <code>skip</code>:",
            parse_mode="HTML")
        return GR_CUSTOM_MSG

    await query.edit_message_text(
        f"✅ {cat['emoji']} {cat['label']}\n\n"
        f"📋 <b>Step 4/6</b> — Select sub-category:",
        reply_markup=_build_sub_keyboard(cat_key, "GRSUB"),
        parse_mode="HTML")
    return GR_REASON_SUB

async def gr_subcategory_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("GRCAT"))
        return GR_REASON_CAT
    if len(parts) < 3: return GR_REASON_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return GR_REASON_SUB
    sub_label = next((lbl for k, lbl in (cat["subs"] or []) if k == sub_key), "N/A")
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
    add_log(f"📥 GroupReport custom msg: {(text[:40] or '(pool)')}")
    await update.message.reply_text(
        f"✅ Saved!\n\n🔢 <b>Step 6/6</b> — Reports per account?\n\n"
        f"💡 1–2 = ✅ Safe | 3–10 = ⚠️ Moderate | 10+ = 🚨 Aggressive\n\n"
        f"Enter 1–{MAX_REPORTS_PER_ACCOUNT}:", parse_mode="HTML")
    return GR_COUNT

async def _send_groupreport_single(phone, chat_ident, msg_id, reason_api, custom_msg,
                                    link_type, sub_label) -> Tuple[bool, str]:
    """
    GROUP REPORT method:
      1) account.reportPeer (peer-level, like group's 3-dot menu → Report)
      2) messages.report with the specific msg_id (to anchor reason to that exact message)
      3) Fallbacks (re-resolve, reportSpam)
    """
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

        # --- M1: account.reportPeer (group-level menu equivalent) ---
        try:
            await asyncio.sleep(random.uniform(0.15, 0.4))
            r = await client(functions.account.ReportPeerRequest(
                peer=entity, reason=reason_api,
                message=f"[GroupReport] Re: msg {msg_id} — {craft_report_message(custom_msg, sub_label)}"))
            if r:
                mark_proxy_result(proxy, True)
                add_log(f"✅ GR-M1 OK: {phone[-4:]} (msg {msg_id})")
                return (True, f"Success (M1: account.reportPeer @ msg {msg_id})")
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

        # --- M2: messages.report on the specific msg_id (anchored selection) ---
        try:
            await asyncio.sleep(random.uniform(0.2, 0.5))
            client = await ensure_connected(phone)
            if not client:
                return (False, "Disconnected mid-flow")
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

        # --- M3: prefetch + report (refresh msg context, then report peer) ---
        try:
            await asyncio.sleep(random.uniform(0.2, 0.5))
            client = await ensure_connected(phone)
            if client:
                try:
                    await client.get_messages(entity, ids=int(msg_id))
                except Exception:
                    pass
                r = await client(functions.account.ReportPeerRequest(
                    peer=entity, reason=reason_api,
                    message=craft_report_message(custom_msg, sub_label)))
                if r:
                    mark_proxy_result(proxy, True)
                    add_log(f"✅ GR-M3 OK: {phone[-4:]}")
                    return (True, "Success (M3: prefetch + reportPeer)")
                methods_tried.append("M3")
        except Exception as e:
            methods_tried.append(f"M3-{type(e).__name__}")

        # --- M4: re-resolve + reportPeer ---
        try:
            await asyncio.sleep(random.uniform(0.2, 0.5))
            client = await ensure_connected(phone)
            if client:
                entity = await resolve_chat_entity(client, chat_ident, link_type)
                r = await client(functions.account.ReportPeerRequest(
                    peer=entity, reason=reason_api,
                    message=craft_report_message(custom_msg, sub_label)))
                if r:
                    mark_proxy_result(proxy, True)
                    add_log(f"✅ GR-M4 OK: {phone[-4:]}")
                    return (True, "Success (M4: re-resolve + reportPeer)")
                methods_tried.append("M4")
        except Exception as e:
            methods_tried.append(f"M4-{type(e).__name__}")

        # --- M5: messages.reportSpam fallback ---
        try:
            await asyncio.sleep(random.uniform(0.2, 0.4))
            client = await ensure_connected(phone)
            if client:
                r = await client(functions.messages.ReportSpamRequest(peer=entity))
                if r:
                    mark_proxy_result(proxy, True)
                    add_log(f"✅ GR-M5 OK: {phone[-4:]}")
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
    try:
        count = int(update.message.text.strip())
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1–{MAX_REPORTS_PER_ACCOUNT}:")
            return GR_COUNT
    except ValueError:
        await update.message.reply_text("⚠️ Numbers only:"); return GR_COUNT

    chat_ident = ctx.user_data["gr_msg_ident"]
    msg_id     = ctx.user_data["gr_msg_id"]
    link_type  = ctx.user_data["gr_grp_type"]
    reason_api = ctx.user_data["gr_reason_api"]
    custom_msg = ctx.user_data.get("gr_custom_msg", "")
    cat_lbl    = ctx.user_data.get("gr_cat_label", "Reason")
    sub_lbl    = ctx.user_data.get("gr_sub_label", "")
    msg_link   = ctx.user_data.get("gr_msg_link", "")

    auth_pairs = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c:
            auth_pairs.append((phone, c))

    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!")
        return ConversationHandler.END

    total_planned = len(auth_pairs) * count
    report_stats["total"] = total_planned
    report_stats["start_time"] = datetime.now()
    join_note = "Public (no join)" if link_type == "username" else "Private (joined)"

    await update.message.reply_text(
        f"🚀 <b>GROUP REPORTING STARTED (3-dot menu flow)</b>\n\n"
        f"📊 Total: {total_planned}\n"
        f"📱 Accounts: {len(auth_pairs)} × {count}\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
        f"🔗 Anchor msg: <code>{msg_link}</code>\n"
        f"🌐 {join_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━", parse_mode="HTML")

    total_ok = total_fail = 0
    per_acc_ok: Dict[str, int]   = {p: 0 for p, _ in auth_pairs}
    per_acc_fail: Dict[str, int] = {p: 0 for p, _ in auth_pairs}
    shot_num = 0

    for r in range(count):
        for acc_idx, (phone, _) in enumerate(auth_pairs):
            shot_num += 1
            ok, status = await _send_groupreport_single(
                phone, chat_ident, msg_id, reason_api, custom_msg,
                link_type, sub_lbl)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1; update_stats(True)
                log_report_file(phone, f"{chat_ident}/{msg_id}", f"GR-{cat_lbl}/{sub_lbl}", "SUCCESS", status)
                try:
                    await update.message.reply_text(
                        f"✅ GR {shot_num}/{total_planned} | R{r+1} | 📱 {phone[-4:]} → {status}",
                        parse_mode="HTML")
                except: pass
            else:
                total_fail += 1; per_acc_fail[phone] += 1; update_stats(False)
                log_report_file(phone, f"{chat_ident}/{msg_id}", f"GR-{cat_lbl}/{sub_lbl}", "FAILED", status)
                try:
                    await update.message.reply_text(
                        f"❌ GR {shot_num}/{total_planned} | R{r+1} | 📱 {phone[-4:]} → {status}",
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

    elapsed = (datetime.now() - report_stats["start_time"]).seconds
    rate    = (total_ok / total_planned) * 100 if total_planned > 0 else 0
    add_log(f"🎉 GroupReport done: {total_ok}/{total_planned} ({rate:.1f}%)")

    breakdown = "\n".join(
        f"  📱 {p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)

    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>GROUP REPORT COMPLETE</b>\n\n"
        f"✅ Success: {total_ok}\n"
        f"❌ Failed: {total_fail}\n"
        f"📈 Rate: {rate:.1f}%\n"
        f"⏱ Time: {elapsed//60}m {elapsed%60}s\n\n"
        f"<b>Per-account breakdown:</b>\n{breakdown}\n\n"
        f"⚠️ {cat_lbl} → {sub_lbl}\n"
        f"🔗 {msg_link}",
        parse_mode="HTML")
    return ConversationHandler.END

# ══════════════════════════════════════════════════════════════════════
# 📸 PFP REPORT FLOW (unchanged from old)
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
        f"👤 Enter <code>@username</code> or user ID:\n/cancel to abort.",
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
            await update.message.reply_text(f"⚠️ Enter 1–{MAX_REPORTS_PER_ACCOUNT}:"); return AR_COUNT
    except ValueError:
        await update.message.reply_text("⚠️ Numbers only:"); return AR_COUNT

    target_raw    = ctx.user_data.get("ar_entity_id", "")
    target_name   = ctx.user_data.get("ar_name", "Target")
    reason_label  = ctx.user_data.get("ar_reason_label", "Reason")
    reason_api    = ctx.user_data.get("ar_reason_api")
    custom_msg    = ctx.user_data.get("ar_custom_msg", "")

    auth_pairs = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c:
            auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!")
        return ConversationHandler.END

    total_reports = len(auth_pairs) * count
    await update.message.reply_text(
        f"🚀 <b>NUCLEAR PFP REPORT (ROUND-ROBIN)</b>\n👤 {target_name}\n⚠️ {reason_label}\n"
        f"📊 {total_reports} total ({len(auth_pairs)} × {count})\n"
        f"🔁 Pattern: acc1→acc2→...→accN→acc1→...\n━━━━━━━━━━━━━━━━",
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
            await update.message.reply_text(f"❌ {phone[-4:]}: Resolve — {str(e)[:40]}", parse_mode="HTML")
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
                    f"❌ PFP {shot_num}/{total_reports} | R{r+1} | 📱 {phone[-4:]} → resolve failed",
                    parse_mode="HTML")
                continue
            ok, status = await report_profile_photo_nuclear(phone, ent, photos, reason_api, custom_msg)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ PFP {shot_num}/{total_reports} | R{r+1} | 📱 {phone[-4:]} → {status}",
                    parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"PFP-{reason_label}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ PFP {shot_num}/{total_reports} | R{r+1} | 📱 {phone[-4:]} → {status}",
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
        f"  📱 {p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
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
# 🤖 BOT REPORT FLOW (unchanged from old)
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
        f"✅ Active: {active}/{len(accounts)}\n"
        f"💀 Full Telegram report category tree\n"
        f"🔁 Round-robin firing\n\n"
        f"🤖 Enter <code>@bot_username</code> (must end with <code>bot</code>):\n"
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
    if cat_key not in FULL_REPORT_CATEGORIES: return BR_CAT
    cat = FULL_REPORT_CATEGORIES[cat_key]
    ctx.user_data["br_cat_key"]   = cat_key
    ctx.user_data["br_reason_api"]= cat["api"]
    ctx.user_data["br_cat_label"] = f"{cat['emoji']} {cat['label']}"
    ctx.user_data["br_sub_label"] = ""

    if cat["direct"]:
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
    if len(parts) >= 2 and parts[1] == "back":
        await query.edit_message_text(
            "📋 Select report reason:",
            reply_markup=_build_full_cat_keyboard("BCAT"))
        return BR_CAT
    if len(parts) < 3: return BR_SUB
    cat_key, sub_key = parts[1], parts[2]
    cat = FULL_REPORT_CATEGORIES.get(cat_key)
    if not cat: return BR_SUB
    sub_label = next((lbl for k, lbl in (cat["subs"] or []) if k == sub_key), "N/A")
    ctx.user_data["br_sub_label"] = sub_label
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
        if not 1 <= count <= MAX_REPORTS_PER_ACCOUNT:
            await update.message.reply_text(f"⚠️ Enter 1–{MAX_REPORTS_PER_ACCOUNT}:"); return BR_COUNT
    except ValueError:
        await update.message.reply_text("⚠️ Numbers only:"); return BR_COUNT

    target_raw  = ctx.user_data.get("br_entity_id", "")
    target_name = ctx.user_data.get("br_name", "Bot")
    cat_label   = ctx.user_data.get("br_cat_label", "Reason")
    sub_label   = ctx.user_data.get("br_sub_label", "")
    reason_api  = ctx.user_data.get("br_reason_api")
    custom_msg  = ctx.user_data.get("br_custom_msg", "")

    auth_pairs = []
    for phone in list(accounts.keys()):
        c = await ensure_connected(phone)
        if c:
            auth_pairs.append((phone, c))
    if not auth_pairs:
        await update.message.reply_text("❌ No active accounts!")
        return ConversationHandler.END

    total = len(auth_pairs) * count
    await update.message.reply_text(
        f"🚀 <b>BOT REPORT STARTING (ROUND-ROBIN)</b>\n"
        f"🤖 {target_name}\n"
        f"⚠️ {cat_label} → {sub_label}\n"
        f"📊 {total} total ({len(auth_pairs)} × {count})\n"
        f"🔁 Pattern: acc1→acc2→...→accN→acc1→...\n━━━━━━━━━━━━━━━━",
        parse_mode="HTML")

    resolved: Dict[str, object] = {}
    for phone, client in auth_pairs:
        try:
            identifier = target_raw.lstrip("@")
            ent = await client.get_entity(identifier)
            resolved[phone] = ent
        except Exception as e:
            await update.message.reply_text(f"❌ {phone[-4:]}: Resolve — {str(e)[:40]}", parse_mode="HTML")
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
                total_fail += 1; per_acc_fail[phone] += 1
                await update.message.reply_text(
                    f"❌ BOT {shot_num}/{total} | R{r+1} | 📱 {phone[-4:]} → resolve failed",
                    parse_mode="HTML")
                continue
            ok, status = await _report_bot_methods(phone, bot_entity, reason_api, custom_msg, sub_label)
            if ok:
                total_ok += 1; per_acc_ok[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "SUCCESS", status)
                await update.message.reply_text(
                    f"✅ BOT {shot_num}/{total} | R{r+1} | 📱 {phone[-4:]} → {status}",
                    parse_mode="HTML")
            else:
                total_fail += 1; per_acc_fail[phone] += 1
                log_report_file(phone, target_raw, f"BOT-{cat_label}/{sub_label}", "FAILED", status)
                await update.message.reply_text(
                    f"❌ BOT {shot_num}/{total} | R{r+1} | 📱 {phone[-4:]} → {status}",
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
        f"  📱 {p[-4:]} → ✅ {per_acc_ok[p]} | ❌ {per_acc_fail[p]}"
        for p, _ in auth_pairs)
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━\n🎉 <b>BOT REPORT COMPLETE</b>\n\n"
        f"🤖 {target_name}\n⚠️ {cat_label} → {sub_label}\n"
        f"✅ {total_ok} | ❌ {total_fail} | 📈 {rate:.1f}%\n\n"
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
        await asyncio.sleep(random.uniform(0.2, 0.6))
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
        await asyncio.sleep(random.uniform(0.3, 0.7))
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
        await asyncio.sleep(random.uniform(0.3, 0.8))
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
        await asyncio.sleep(random.uniform(0.3, 0.7))
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
# 📧 GMAIL FLOW (unchanged)
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
            "✏️ Enter Email Subject:", parse_mode="HTML")
    else:
        ctx.user_data.clear()
        await update.message.reply_text(
            "📧 <b>Gmail BLAST Mode — Step 1/5</b>\n\n"
            "🔥 All accounts fire at once + repeat N times!\n\n"
            "✏️ Enter Email Subject:", parse_mode="HTML")
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
            await update.message.reply_text("⚠️ Enter 1–50:"); return MAIL_BLAST_COUNT
    except ValueError:
        await update.message.reply_text("⚠️ Numbers only:"); return MAIL_BLAST_COUNT
    ctx.user_data["mail_blast_count"] = count
    recipient = ctx.user_data.get("mail_recipient","N/A")
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
# 🔄 POST INIT / SHUTDOWN
# ══════════════════════════════════════════════════════════════════════
async def post_init(application):
    load_sudo()
    load_proxy_health()
    load_accounts()
    for phone in list(accounts.keys()):
        try:
            await ensure_connected(phone)
        except: pass
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
    app.add_handler(add_conv)
    app.add_handler(rm_conv)
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
