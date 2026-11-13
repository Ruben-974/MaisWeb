const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright-core');
const support = path.resolve(__dirname, '..');
const base = process.env.AACI_PREVIEW_URL || 'http://127.0.0.1:8767';

async function loadImages(page) {
  return page.evaluate(async () => {
    const images = [...document.querySelectorAll('img[src]')];
    await Promise.all(images.map(async image => {
      image.loading = 'eager';
      try { await image.decode(); } catch { /* A falha será verificada abaixo. */ }
    }));
    return images.filter(image => image.dataset.localSrc && (!image.naturalWidth || !image.src.startsWith('https://')))
      .map(image => ({ src: image.src, local: image.dataset.localSrc }));
  });
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.AACI_BROWSER_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const online = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
    // Prova que as mídias públicas funcionam sem as cópias locais.
    await online.route('**/*', route => {
      const url = route.request().url();
      const localMedia = url.startsWith(base) && /\/assets\/(?:images\/|media\/|documents\/|aaci-logo\.png)/.test(url);
      return localMedia ? route.abort() : route.continue();
    });
    const page = await online.newPage();
    for (const file of ['index.html', 'quem-somos.html', 'galeria.html', 'transparencia.html', 'videos.html']) {
      await page.goto(`${base}/${file}`, { waitUntil: 'domcontentloaded' });
      assert.deepEqual(await loadImages(page), [], `Mídia externa falhou em ${file}`);
      if (file === 'index.html') await page.locator('.hero').screenshot({ path: path.join(support, 'output/external-media-hero.png') });
      if (file === 'transparencia.html') {
        assert.equal(await page.locator('.document-actions a[data-local-href][href^="https://"]').count(), 26);
        assert.equal(await page.locator('.document-actions a[download][href^="assets/documents/"]').count(), 26);
      }
      console.log(`PASS: ${file} carrega imagens externas com os arquivos locais bloqueados`);
    }
    await page.goto(`${base}/noticias/cozinha-comunitaria.html`, { waitUntil: 'domcontentloaded' });
    await page.locator('video').evaluate(async video => { video.muted = true; await video.play(); });
    await page.waitForFunction(() => document.querySelector('video').currentTime > .1);
    assert.ok((await page.locator('video').evaluate(video => video.currentSrc)).startsWith('https://video.wixstatic.com/'));
    await page.locator('video').evaluate(video => video.pause());
    console.log('PASS: MP4 externo reproduz sem acesso ao arquivo local');
    await online.close();

    const offline = await browser.newContext({ viewport: { width: 375, height: 900 }, reducedMotion: 'reduce' });
    await offline.route('**/*', route => route.request().url().startsWith(base) ? route.continue() : route.abort());
    const fallback = await offline.newPage();
    await fallback.goto(`${base}/galeria.html`, { waitUntil: 'domcontentloaded' });
    await fallback.locator('.gallery-tile img').first().waitFor();
    await fallback.waitForFunction(() => [...document.querySelectorAll('img[data-local-src]')].filter(image => image.loading !== 'lazy').every(image => image.complete && image.naturalWidth));
    await fallback.locator('[data-gallery-link]').first().click();
    await fallback.waitForFunction(() => document.getElementById('galleryFullImage').naturalWidth > 0);
    assert.ok((await fallback.locator('#galleryFullImage').getAttribute('src')).startsWith('assets/images/'));
    await fallback.goto(`${base}/noticias/cozinha-comunitaria.html`, { waitUntil: 'domcontentloaded' });
    await fallback.locator('video').evaluate(video => video.load());
    await fallback.waitForFunction(() => document.querySelector('video').readyState >= 1);
    assert.ok((await fallback.locator('video').evaluate(video => video.currentSrc)).includes('/assets/media/cozinha-comunitaria.mp4'));
    assert.ok((await fallback.locator('video').getAttribute('poster')).includes('assets/media/'));
    console.log('PASS: imagens, galeria, MP4 e capa retornam à cópia local com os endereços externos bloqueados');
    await offline.close();
    fs.writeFileSync(path.join(support, 'output/site-external-media-tests.json'), JSON.stringify({ estado: 'aprovado', verificacoes: ['Imagens públicas sem acesso às cópias locais', '26 PDFs externos com download local', 'Reprodução real do MP4 externo', 'Alternativas locais de imagem, galeria, vídeo e capa sem rede externa'] }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
