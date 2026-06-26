# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS dev

# pnpm via corepack
ENV PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH" \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0

RUN corepack enable && corepack prepare pnpm@9.12.3 --activate

WORKDIR /app

# Pre-install for layer cache
COPY package.json pnpm-lock.yaml* .npmrc ./
RUN pnpm install

COPY . .

EXPOSE 5173

# Dev: vite dev server with HMR over 0.0.0.0
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]
