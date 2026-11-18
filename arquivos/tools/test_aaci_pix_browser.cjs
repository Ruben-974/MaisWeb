const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright-core');

const support = path.resolve(__dirname, '..');
const root = path.resolve(support, '..');
const output = path.join(support, 'output');
const images = [];

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.AACI_BROWSER_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    for (const width of [320, 375, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.addInitScript(() => {
        window.pixCopies = [];
        Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async value => { window.pixCopies.push(value); } } });
      });
      // file:// também verifica a geração local, sem API ou servidor de pagamentos.
      await page.goto(pathToFileURL(path.join(root, 'index.html')).href);
      await page.locator('.donation-card.is-active .donate-trigger').click();
      await page.locator('#donationModal.show').waitFor();
      const image = page.locator('.pix-qr');
      const input = page.locator('#donationCustomAmount');
      const copy = page.locator('#copyPixPayload');
      for (const amount of [25, 50, 100, 200]) {
        await page.locator(`[data-donation-amount="${amount}"]`).click();
        await copy.click();
        const payload = await page.evaluate(() => window.pixCopies.at(-1));
        assert.ok(payload.includes(`54${String(amount.toFixed(2).length).padStart(2, '0')}${amount.toFixed(2)}`));
        assert.equal(await page.locator('#pixPayment').isVisible(), true);
      }
      await input.fill('100');
      const before = await image.getAttribute('src');
      await input.press('ArrowDown');
      assert.equal(await input.inputValue(), '99');
      assert.notEqual(await image.getAttribute('src'), before);
      await copy.click();
      assert.ok((await page.evaluate(() => window.pixCopies.at(-1))).includes('540599.00'));

      for (const amount of [100, 75.5, 1000000]) {
        await input.fill(String(amount));
        await copy.click();
        const payload = await page.evaluate(() => window.pixCopies.at(-1));
        const file = `pix-browser-${width}-${String(amount).replace('.', '-')}.png`;
        await image.screenshot({ path: path.join(output, file) });
        images.push({ arquivo: file, largura: width, valor: amount, payload });
      }
      await input.fill('0');
      assert.equal(await page.locator('#pixPayment').isVisible(), false);
      assert.equal(await copy.isDisabled(), true);
      assert.equal(await image.getAttribute('src'), null);
      await input.fill('50');
      assert.equal(await page.locator('#pixPayment').isVisible(), true);
      if (width === 375) await page.locator('#donationModal .modal-content').screenshot({ path: path.join(output, 'pix-modal-mobile.png') });
      assert.equal(errors.length, 0, errors.join('\n'));
      console.log(`PASS: Pix ${width}px — valores, setas de R$ 1, cópia, recuperação de erro e QR renderizado`);
      await context.close();
    }
    // Página interna confirma os caminhos relativos dos novos scripts.
    const page = await browser.newPage();
    await page.goto(pathToFileURL(path.join(root, 'pages/noticias/cozinha-comunitaria.html')).href);
    await page.locator('.nav-donate .donate-trigger').click();
    await page.locator('#pixPayment').waitFor({ state: 'visible' });
    assert.ok((await page.locator('.pix-qr').getAttribute('src')).startsWith('data:image/gif;'));
    await page.close();
    fs.writeFileSync(path.join(output, 'site-pix-browser-tests.json'), JSON.stringify({ estado: 'aprovado', navegador: 'Chrome headless', protocolo: 'file://', capturas: images }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
