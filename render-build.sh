# Usa Debian bullseye slim
FROM debian:bullseye-slim

# Evita perguntas durante instalação
ENV DEBIAN_FRONTEND=noninteractive

# Variável para cache do Puppeteer (pode mudar se quiser)
ENV PUPPETEER_CACHE_DIR=/home/node/.cache/puppeteer

# Atualiza e instala dependências básicas, Node.js, npm, wget e libs necessárias para Chromium
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libxshmfence1 \
    libnss3 \
    libnspr4 \
    libx11-xcb1 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxfixes3 \
    libxrandr2 \
    libxcursor1 \
    libxtst6 \
    libatspi2.0-0 \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Cria pasta de trabalho
WORKDIR /app

# Copia package.json e package-lock.json (se existir)
COPY package*.json ./

# Instala dependências node (puppeteer, dotenv, etc)
RUN npm install

# Copia todo o código da app
COPY . .

# Cria cache do puppeteer
RUN mkdir -p ${PUPPETEER_CACHE_DIR}

# Baixa o Chromium com Puppeteer (como seu render-build.sh)
RUN npx puppeteer browsers install chrome

# Exponha a porta (se sua app usar alguma porta, tipo express)
EXPOSE 3000

# Comando default para rodar sua app (ajuste o nome do arquivo se precisar)
CMD ["npm", "start"]
