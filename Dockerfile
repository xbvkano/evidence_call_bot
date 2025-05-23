# ─── Base: Python + venv ──────────────────────────────────────────────────
FROM python:3.11-slim

# Install venv & git (Prisma Python CLI needs git for some operations)
RUN apt-get update \
 && apt-get install -y python3-venv git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── 1) Copy and install Python deps ─────────────────────────────────────
COPY requirements.txt ./

# Create & activate venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install everything (including prisma CLI, flask, gunicorn, requests, twilio, python-dotenv)
RUN pip install --no-cache-dir -r requirements.txt

# ─── 2) Copy your Prisma schema & generate Python client ────────────────
COPY prisma_schema/schema.prisma ./prisma/schema.prisma
RUN prisma generate

# ─── 3) Copy the rest of your app & clean up ─────────────────────────────
COPY . .
RUN rm -rf prisma_schema

# ─── 4) Expose & run ─────────────────────────────────────────────────────
EXPOSE 5000
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
