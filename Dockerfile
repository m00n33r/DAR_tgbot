FROM python:3.11-slim

# Ensure Python runs in unbuffered mode and no .pyc files are written
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install locales and generate ru_RU.UTF-8 used by the bot
RUN apt-get update && apt-get install -y --no-install-recommends locales \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i 's/^# \(ru_RU.UTF-8\)/\1/' /etc/locale.gen || true \
    && locale-gen ru_RU.UTF-8 \
    && update-locale LANG=ru_RU.UTF-8

ENV LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default database path can be overridden by env var
# ENV DATABASE_PATH=/app/dar_bot.db

# Bot expects TELEGRAM_BOT_TOKEN in env (and optionally ADMIN_PASSWORD)
CMD ["python", "bot.py"]


