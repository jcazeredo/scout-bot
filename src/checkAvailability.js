const puppeteer = require('puppeteer');

async function checkAvailability() {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Go to VHS Berlin course search page
  await page.goto('https://www.vhsit.berlin.de/VHSKURSE/BusinessPages/CourseSearch.aspx', {
    waitUntil: 'networkidle2'
  });

  // Select "Einbürgerungstest" from dropdown
  await page.select('#ctl00_Content_KeywordsList1_cmbKeyword', '2419'); // value for Einbürgerungstest

  // Click the search button and wait for page reload
  await Promise.all([
    page.click('#ctl00_Content_btnSearch'),
    page.waitForNavigation({ waitUntil: 'networkidle2' })
  ]);

  // Check if the error message appears
  const noCourses = await page.evaluate(() => {
    const el = document.querySelector('#ctl00_Content_ErrorMessage1_lblError');
    return el && el.innerText.includes('Zu Ihrer Suche wurden keine Kurse gefunden.');
  });

  await browser.close();

  return !noCourses; // true if courses available
}

module.exports = checkAvailability;
