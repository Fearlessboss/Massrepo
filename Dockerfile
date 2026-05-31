# ═══════════════════════════════════════════════════════════════
#  ⚡ Ultimate Telegram Reporter v13.0 — Dockerfile
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim

# Prevent .pyc & enable real-time logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Kolkata

# System deps (timezone + ssl + build tools for cryptg/pysocks)
RUN apt-get update && apt-get install -y --no-install-recommends \
        tzdata \
        ca-certificates \
        build-essential \
        libssl-dev \
        libffi-dev \
        gcc \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps (pin major versions for stability)
RUN pip install --upgrade pip && \
    pip install \
        "python-telegram-bot==21.6" \
        "telethon==1.36.0" \
        "PySocks==1.7.1" \
        "cryptg==0.4.0" \
        "pyaes==1.6.1" \
        "rsa==4.9"

# Copy bot source
COPY ultimate_reporter.py /app/ultimate_reporter.py

# Persistent dirs for sessions / logs / sudo / proxy health
RUN mkdir -p /app/logs && \
    touch /app/accounts.json /app/sudo_users.json /app/proxy_health.json

# Declare volumes so data survives container restarts
VOLUME ["/app/logs", "/app"]

# Healthcheck (basic — process alive)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "ultimate_reporter.py" || exit 1

# Run
CMD ["python", "-u", "massrepo.py"]
