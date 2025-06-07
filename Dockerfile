FROM node:20-slim

# Instala dependências do Chromium e o próprio Chromium
RUN apt-get update && apt-get install -y \
    ca-certificates \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    wget \
    unzip \
    chromium \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Cria diretório da aplicação
WORKDIR /app

# Configura o Puppeteer para usar o Chromium instalado
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copia apenas os arquivos de dependência e instala
COPY package*.json ./
RUN npm install --omit=dev

# Copia o restante do app
COPY . .

# Executa
CMD ["npm", "start"]