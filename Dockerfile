# --- Frontend Build Stage ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY apps/web-dashboard/package.json apps/web-dashboard/package-lock.json ./
RUN npm install
COPY apps/web-dashboard ./
RUN npm run build

# --- Backend Build Stage ---
FROM rust:1-slim-bookworm AS backend-builder
RUN apt-get update && apt-get install -y \
    pkg-config libssl-dev build-essential protobuf-compiler cmake clang \
    libwayland-dev libxkbcommon-dev libpango1.0-dev libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Cargo.toml ./
RUN sed -i '/\"apps\/desktop\/src-tauri\"/d' Cargo.toml
COPY apps/cli-server ./apps/cli-server
COPY transcoder-core ./transcoder-core
COPY ls-orchestrator ./ls-orchestrator
COPY ls-accounts ./ls-accounts
RUN cargo build --release --bin cli-server --no-default-features

# --- Final Runtime Stage ---
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y \
    libssl3 ca-certificates curl binutils xz-utils \
    libwayland-client0 libxkbcommon0 libwayland-cursor0 libwayland-egl1 \
    libnss3 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=backend-builder /app/target/release/cli-server ./antigravity-server
COPY --from=frontend-builder /app/dist ./dist

ENV ABV_DIST_PATH=/app/dist
ENV PORT=5173
ENV RUST_LOG=info

EXPOSE 5173
ENTRYPOINT ["/app/antigravity-server"]
