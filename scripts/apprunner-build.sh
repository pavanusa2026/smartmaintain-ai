#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NODE_VERSION="${NODE_VERSION:-v22.12.0}"
NODE_DIR="node-${NODE_VERSION}-linux-x64"

if ! command -v node >/dev/null 2>&1; then
  echo "Installing Node.js ${NODE_VERSION}..."
  curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/${NODE_DIR}.tar.gz" -o /tmp/node.tar.gz
  tar -xzf /tmp/node.tar.gz -C /tmp
  export PATH="/tmp/${NODE_DIR}/bin:$PATH"
fi

echo "Node: $(node --version)"
echo "npm: $(npm --version)"

echo "Building frontend..."
cd frontend
npm ci
npm run build

echo "Copying static assets into backend..."
mkdir -p "$ROOT/backend/app/static"
cp -r dist/* "$ROOT/backend/app/static/"

echo "Installing Python dependencies..."
cd "$ROOT/backend"
pip install -r requirements.txt

echo "Build complete."
