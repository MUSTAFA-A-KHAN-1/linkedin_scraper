FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wget \
       gnupg \
       curl \
       libnss3 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libcups2 \
       libdrm2 \
       libx11-xcb1 \
       libxcomposite1 \
       libxrandr2 \
       libxdamage1 \
       libxfixes3 \
       libxkbcommon0 \
       libgbm1 \
       libgtk-3-0 \
       libxss1 \
       libasound2 \
       libxshmfence1 \
       libpangocairo-1.0-0 \
       libpango-1.0-0 \
       libglib2.0-0 \
       libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py requirements.txt README.md ./
COPY linkedin_scraper ./linkedin_scraper

RUN pip install --upgrade pip \
    && pip install . flask \
    && python -m playwright install chromium

COPY . .

CMD ["python", "app.py"]
