/* Executar com o servidor local ativo e playwright-core disponível no NODE_PATH. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright-core');

const support = path.resolve(__dirname, '..');
const root = path.join(support, '../AACI');
const output = path.join(support, 'output');
const base = process.env.AACI_PREVIEW_URL || 'http://127.0.0.1:8765';
const executablePath = process.env.AACI_BROWSER_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

(async () => {
  const browser = await chromium.launch({ executablePath, headless: true });
  const results = [];
  try {
    for (const width of [320, 375, 768, 950, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(`${base}/index.html`, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const overflow = () => page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(await overflow(), false, `${width}px: horizontal overflow`);

      // O texto e o botão devem caber no cartão, inclusive nos três exemplos.
      for (let index = 0; index < 3; index++) {
        const geometry = await page.locator('.donation-card.is-active').evaluate(card => {
          const rect = card.getBoundingClientRect();
          const copy = card.querySelector('.donation-impact-copy').getBoundingClientRect();
          const button = card.querySelector('.donate-trigger').getBoundingClientRect();
          const hero = card.closest('.hero').getBoundingClientRect();
          return { inside: button.bottom <= rect.bottom && button.right <= rect.right && button.bottom <= hero.bottom, separated: copy.bottom <= button.top };
        });
        assert.ok(geometry.inside && geometry.separated, `${width}px: donation card ${index}`);
        await page.locator('[data-donation-next]').click();
      }

      for (const amount of [25, 50, 200, 100]) {
        await page.locator(`[data-impact-amount="${amount}"]`).click();
        await page.locator(`[data-impact-example="${amount}"].is-selected`).waitFor();
        assert.equal(await page.locator('[data-impact-donate]').getAttribute('data-amount'), String(amount));
        assert.equal(await overflow(), false, `${width}px: overflow after selecting ${amount}`);
      }

      if ([375, 1440].includes(width)) {
        const suffix = width === 375 ? 'mobile' : 'desktop';
        await page.locator('.home-impact').screenshot({ path: path.join(output, `donation-impact-${suffix}.png`) });
        await page.locator('.hero').screenshot({ path: path.join(output, `donation-hero-${suffix}.png`) });
      }

      await page.locator('[data-impact-donate]').click();
      await page.locator('#donationModal.show').waitFor();
      assert.match(await page.locator('#donationAmountLabel').textContent(), /100/);
      await page.locator('#donationModal .btn-close').click();
      await page.locator('#donationModal').waitFor({ state: 'hidden' });
      assert.equal(errors.length, 0, errors.join('\n'));
      results.push({ largura: width, estado: 'aprovado' });
      console.log(`PASS: ${width}px — cartões, quatro valores, modal e ausência de rolagem horizontal`);
      await context.close();
    }
    fs.writeFileSync(path.join(output, 'site-layout-tests.json'), JSON.stringify({ navegador: 'Chrome headless', resultados: results, capturas: ['donation-impact-desktop.png', 'donation-impact-mobile.png', 'donation-hero-desktop.png', 'donation-hero-mobile.png'] }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
