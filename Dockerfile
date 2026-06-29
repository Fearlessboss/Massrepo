# ═══════════════════════════════════════════════════════════════
#  ⚡ Ultimate Telegram Reporter v16.0 — Dockerfile
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Kolkata

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

WORKDIR /app

# Install all required packages
RUN pip install --upgrade pip && \
    pip install \
        "python-telegram-bot==21.6" \
        "telethon==1.36.0" \
        "PySocks==1.7.1" \
        "pymongo==4.10.0" \
        "cryptg==0.4.0" \
        "pyaes==1.6.1" \
        "rsa==4.9"

# Copy bot
COPY ultimate_reporter.py /app/ultimate_reporter.py

# Create necessary directories
RUN mkdir -p /app/logs && \
    touch /app/accounts.json /app/sudo_users.json /app/proxy_health.json

VOLUME ["/app/logs", "/app"]

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "ultimate_reporter.py" || exit 1

# Final Run
CMD ["python", "-u", "ultimate_reporter.py"]
