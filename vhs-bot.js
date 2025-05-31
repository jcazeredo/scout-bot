require('dotenv').config();
const puppeteer = require('puppeteer');
const fetch = require('node-fetch'); // npm install node-fetch@2

const URL = process.env.URL;
const KEYWORD_SELECTION_VALUE = process.env.KEYWORD_SELECTION_VALUE;
const ONE_HOUR = Number(process.env.ONE_HOUR) || 60 * 60 * 1000;   // fallback 1h
const ONE_MINUTE = Number(process.env.ONE_MINUTE) || 60 * 1000;   // fallback 1min

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

function timestamp() {
  return new Date().toLocaleString();
}

function log(...args) {
  console.log(`[${timestamp()}]`, ...args);
}

async function sendTelegramMessage(text) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const body = {
    chat_id: TELEGRAM_CHAT_ID,
    text: text,
    parse_mode: 'Markdown'
  };
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      console.error(`Telegram API error: ${res.statusText}`);
    }
  } catch (error) {
    console.error('Erro ao enviar mensagem Telegram:', error);
  }
}

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function navigateAndSearch(page) {
  await page.goto(URL, { waitUntil: 'networkidle2' });
  await page.select('#ctl00_Content_KeywordsList1_cmbKeyword', KEYWORD_SELECTION_VALUE);
  await Promise.all([
    page.click('#ctl00_Content_btnSearch'),
    page.waitForNavigation({ waitUntil: 'networkidle2' }),
  ]);
}

async function extractCourses(page) {
  try {
    return await page.evaluate(() => {
      const errorEl = document.querySelector('#ctl00_Content_ErrorMessage1_lblError');
      if (errorEl && errorEl.innerText.includes('Zu Ihrer Suche wurden keine Kurse gefunden.')) {
        return { hasCourses: false };
      }

      const titleEl = document.querySelector('#ctl00_Content_lblTitle');
      if (!titleEl || !titleEl.innerText.includes('Kursliste')) {
        return { hasCourses: false };
      }

      const countEl = document.querySelector('#ctl00_Content_lblMessage1All');
      const countText = countEl ? countEl.innerText.trim() : '';
      const countMatch = countText.match(/\d+/);
      const courseCount = countMatch ? parseInt(countMatch[0], 10) : 0;

      const rows = Array.from(document.querySelectorAll('#ctl00_Content_ILDataGrid1 tr.DataGridItem'));

      const courses = rows.map(row => {
        const safeText = (sel) => {
          try {
            const el = row.querySelector(sel);
            return el ? el.innerText.trim() : 'N/A';
          } catch {
            return 'N/A';
          }
        };
        return {
          bezirk: safeText('td.DataGridItemDistrict'),
          kurstitel: safeText('td.DataGridItemCourseTitle'),
          freiePlaetze: safeText('td.DataGridItemPlaces'),
        };
      });

      return { hasCourses: true, courseCount, courses };
    });
  } catch (error) {
    console.error(`[${new Date().toLocaleString()}] Error extracting courses:`, error);
    return { hasCourses: false };
  }
}

async function attemptSearch(page, attemptNumber) {
  try {
    await navigateAndSearch(page);

    const result = await extractCourses(page);

    if (result.hasCourses) {
      log(`[Attempt #${attemptNumber}] ✅ Courses found! Total: ${result.courseCount}`);
      result.courses.forEach((c, i) => {
        log(`  ${i + 1}. Bezirk: ${c.bezirk}, Kurstitel: ${c.kurstitel}, freie Plätze: ${c.freiePlaetze}`);
      });
      return result;
    } else {
      log(`[Attempt #${attemptNumber}] ❌ No courses found.`);
      return null;
    }
  } catch (error) {
    const errorMsg = `[${timestamp()}] Error in attempt #${attemptNumber}: ${error.message || error}`;
    console.error(errorMsg);
    await sendTelegramMessage(`⚠️ *Erro na busca (attempt #${attemptNumber}):*\n\`${error.message || error}\``);
    return null;
  }
}

async function run() {
  let runNumber = 0;

  while (true) {
    runNumber++;

    start_message = `🚀 Starting run #${runNumber}`
    log(start_message);
    await sendTelegramMessage(start_message);

    const browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage'
      ],
      // Use environment variable if set, otherwise default
      executablePath: process.env.CHROME_PATH || undefined
    });  
    const pages = await browser.pages();
    await pages[0].close();
    const page = await browser.newPage();

    let attemptNumber = 0;
    let foundCourses = null;

    while (!foundCourses) {
      attemptNumber++;
      foundCourses = await attemptSearch(page, attemptNumber);
      if (!foundCourses) {
        await delay(ONE_MINUTE);
      }
    }

    // Cursos encontrados
    let message = `🎉 *Cursos disponíveis encontrados na run #${runNumber}!* \nQuantidade: *${foundCourses.courseCount}*\nLink: ${URL}\n\n`;

    foundCourses.courses.forEach((c, i) => {
      message += `${i + 1}. Bezirk: ${c.bezirk}\n   Kurstitel: ${c.kurstitel}\n   freie Plätze: ${c.freiePlaetze}\n\n`;
    });

    await sendTelegramMessage(message);

    log(`Courses found on run #${runNumber}, closing browser and waiting 1 hour before next run...`);
    await browser.close();

    await delay(ONE_HOUR);
  }
}

run();

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Scout Bot is running!');
});

// Health check (Render verifica esse endpoint)
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

app.listen(PORT, '0.0.0.0', () => {
  log(`Server running on PORT: ${PORT}`);
});
