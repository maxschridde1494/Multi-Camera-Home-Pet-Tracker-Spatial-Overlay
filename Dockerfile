FROM python:3.11-slim AS python-base

# Install system packages needed by opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

FROM python-base AS server-base
COPY ./server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./server/app ./app

FROM server-base AS server-dev

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM node:20-slim AS client-base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
WORKDIR /usr/local/app
COPY ./client/package.json ./client/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.pnpm-store \
    pnpm install --frozen-lockfile

FROM client-base AS client-dev
COPY ./client ./
EXPOSE 5173 3036

CMD ["pnpm", "run", "dev"]
