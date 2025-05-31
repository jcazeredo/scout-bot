#!/bin/bash

set -e # Exit immediately if any command fails

echo "### Starting build ###"
echo "Using Puppeteer cache directory: ${PUPPETEER_CACHE_DIR}"

# Create cache directory from environment variable
mkdir -p "${PUPPETEER_CACHE_DIR}"

echo "Installing Chrome..."
npx puppeteer browsers install chrome

echo "Verifying installation..."
ls -la "${PUPPETEER_CACHE_DIR}/chrome"

echo "### Build complete ###"
