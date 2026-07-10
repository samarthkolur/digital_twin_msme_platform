# syntax=docker/dockerfile:1

FROM node:22-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/* \
	&& corepack enable
WORKDIR /workspace

# --- deps: install once, cached across dev/build ---------------------------
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/dashboard/package.json ./apps/dashboard/package.json
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
	pnpm config set store-dir /pnpm/store && \
	pnpm install --frozen-lockfile --filter @digital-cousin/dashboard...

# --- dev: hot-reload dev server, used by `docker compose watch` ------------
FROM deps AS dev
COPY apps/dashboard ./apps/dashboard
WORKDIR /workspace/apps/dashboard
EXPOSE 5173
CMD ["pnpm", "run", "dev"]

# --- build: production static bundle ----------------------------------------
FROM deps AS build
COPY apps/dashboard ./apps/dashboard
WORKDIR /workspace/apps/dashboard
RUN pnpm run build

# --- prod: nginx serving the static bundle, non-root, minimal image --------
FROM nginx:1.27-alpine AS prod
RUN addgroup -S dashboard && adduser -S dashboard -G dashboard
COPY apps/dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/dashboard/dist /usr/share/nginx/html
RUN chown -R dashboard:dashboard /usr/share/nginx/html /var/cache/nginx /var/run \
	&& touch /var/run/nginx.pid \
	&& chown dashboard:dashboard /var/run/nginx.pid
USER dashboard
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD wget -qO- http://localhost:8080/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
