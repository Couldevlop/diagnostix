# syntax=docker/dockerfile:1.7
# =============================================================================
# Nexus-Diagnostix — Frontend Dockerfile (multi-stage)
# =============================================================================

FROM node:20-alpine AS base
WORKDIR /app
RUN corepack enable

# -------- Development --------------------------------------------------------
FROM base AS development
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# -------- Build --------------------------------------------------------------
FROM base AS builder
# VITE_API_BASE_URL est baked à la compilation (Vite remplace import.meta.env.*)
# En prod K8s : /api/v1 (même domaine, routing ingress)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --prefer-offline
COPY . .
RUN npm run build

# -------- Production (Nginx) -------------------------------------------------
FROM nginx:1.27-alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
