# ── Build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy rest of source
COPY . .

# Ensure public dir exists (some projects may not have one)
RUN mkdir -p public

# NEXT_PUBLIC_* env vars are inlined into the client bundle at BUILD time, so the
# backend URL the browser calls must be provided as a build arg here. Setting it
# only at container runtime (docker-compose `environment:`) is too late and the
# client falls back to the hardcoded default. Override per environment via
# `--build-arg NEXT_PUBLIC_BACKEND_URL=...` or the compose `build.args`.
ARG NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL

# Build the Next.js application (standalone output)
RUN npm run build

# ── Runtime stage ────────────────────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Copy the standalone server and required assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Expose the Next.js port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

