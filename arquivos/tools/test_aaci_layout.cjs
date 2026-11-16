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
    for (const width of [320, 375, 768, 950, 1200, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(`${base}/index.html`, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const overflow = () => page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(await overflow(), false, `${width}px: horizontal overflow`);
      const menu = ['Quem somos', 'O que fazemos', 'Como ajudar', 'Transparência', 'Acontece', 'AACI na mídia', 'Contato', 'Quero doar'];
      assert.deepEqual(await page.locator('.navbar-nav > .nav-item').evaluateAll(items => items.map(item => (item.querySelector(':scope > .nav-link') || item.querySelector('.donate-trigger')).textContent.trim())), menu);
      assert.deepEqual((await page.locator('.footer-nav > li').allTextContents()).map(text => text.trim()), menu);
      assert.equal(await page.locator('.statistic-card').count(), 6);
      if (width < 480) {
        const separated = await page.locator('.statistic-card').evaluateAll(cards => cards.every(card => card.querySelector('.statistic-value').getBoundingClientRect().right <= card.querySelector('h3').getBoundingClientRect().left - 6));
        assert.ok(separated, 'Valores e rótulos dos indicadores não devem se sobrepor');
      }
      const statistics = await page.locator('.home-statistics').boundingBox();
      const about = await page.locator('.home-about').boundingBox();
      assert.ok(statistics.y + statistics.height <= about.y + 1, 'Quantitativos antes da história');
      assert.ok((await page.locator('.home-about .rounded-photo').boundingBox()).height <= 320, 'Foto da história compacta');
      assert.equal(await page.locator('.whatsapp-float').evaluate(element => getComputedStyle(element).position), 'fixed');
      assert.equal(new URL(await page.locator('.whatsapp-float').getAttribute('href')).pathname, '/5532988559201');

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
        await page.locator('.home-statistics').screenshot({ path: path.join(output, `statistics-${suffix}.png`) });
        await page.locator('.home-about').screenshot({ path: path.join(output, `about-compact-${suffix}.png`) });
      }

      await page.locator('[data-impact-donate]').click();
      await page.locator('#donationModal.show').waitFor();
      assert.match(await page.locator('#donationAmountLabel').textContent(), /100/);
      await page.locator('#donationModal .btn-close').click();
      await page.locator('#donationModal').waitFor({ state: 'hidden' });
      const whatsapp = await page.locator('.whatsapp-float').boundingBox();
      const top = await page.locator('.back-to-top').boundingBox();
      assert.ok(top.y + top.height <= whatsapp.y || whatsapp.y + whatsapp.height <= top.y, 'Atalhos fixos separados');
      await page.locator('.footer-donate').click();
      await page.locator('#donationModal.show').waitFor();
      await page.locator('#donationModal .btn-close').click();
      await page.locator('#donationModal').waitFor({ state: 'hidden' });
      if (width < 1200) {
        await page.locator('.navbar-toggler').click();
        await page.locator('#mainNav.show').waitFor();
      }
      await page.locator('.site-header a[href="aaci-na-midia.html"]').click();
      await page.waitForURL('**/aaci-na-midia.html');
      assert.equal(await page.locator('h1').textContent(), 'AACI na mídia');
      assert.equal(await page.locator('[data-youtube]').count(), 4);
      await page.evaluate(async () => {
        const images = [...document.querySelectorAll('.video-facade img')];
        await Promise.all(images.map(async image => { image.loading = 'eager'; await image.decode(); }));
      });
      assert.equal(await page.locator('.video-facade img').evaluateAll(images => images.every(image => image.naturalWidth > 0)), true);
      assert.equal(await overflow(), false, 'Reportagens sem rolagem horizontal');
      if ([375, 1440].includes(width)) await page.screenshot({ path: path.join(output, `press-${width === 375 ? 'mobile' : 'desktop'}.png`), fullPage: true });
      assert.equal(errors.length, 0, errors.join('\n'));
      results.push({ largura: width, estado: 'aprovado' });
      console.log(`PASS: ${width}px — menus, quantitativos, história, WhatsApp, doação e página de reportagens`);
      await context.close();
    }
    fs.writeFileSync(path.join(output, 'site-layout-tests.json'), JSON.stringify({ navegador: 'Chrome headless', resultados: results, capturas: ['donation-impact-desktop.png', 'donation-impact-mobile.png', 'donation-hero-desktop.png', 'donation-hero-mobile.png', 'statistics-desktop.png', 'statistics-mobile.png', 'about-compact-desktop.png', 'about-compact-mobile.png', 'press-desktop.png', 'press-mobile.png'] }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
