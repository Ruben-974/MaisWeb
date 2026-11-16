// Testes de comportamento em DOM. Não substituem renderização em navegador.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { JSDOM, VirtualConsole } = require('jsdom');
const support = path.resolve(__dirname, '..');
const root = path.join(support, '../AACI');
const pageList = JSON.parse(fs.readFileSync(path.join(support, 'dados/site-pages.json'), 'utf8')).paginas;
const passed = [];
const log = message => { passed.push(message); console.log(`PASS: ${message}`); };

async function open(file, protocol = 'http:') {
  const errors = [];
  const console = new VirtualConsole();
  console.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(fs.readFileSync(path.join(root, file), 'utf8'), {
    runScripts: 'outside-only', pretendToBeVisual: true,
    url: protocol === 'file:' ? `file:///${path.join(root, file).replaceAll('\\', '/')}` : `http://aaci.test/${file}`,
    virtualConsole: console,
  });
  const w = dom.window;
  const copied = []; const opened = [];
  w.matchMedia = media => ({ matches: true, media, addEventListener() {}, removeEventListener() {} });
  Object.defineProperty(w.navigator, 'clipboard', { value: { writeText: async text => { copied.push(text); } } });
  Object.defineProperty(w.HTMLElement.prototype, 'inert', {
    get() { return this.hasAttribute('inert'); }, set(value) { this.toggleAttribute('inert', Boolean(value)); },
  });
  w.HTMLElement.prototype.getClientRects = function () {
    for (let el = this; el instanceof w.HTMLElement; el = el.parentElement) {
      if (el.hidden || w.getComputedStyle(el).display === 'none') return [];
      if (el.classList.contains('collapse') && !el.classList.contains('show')) return [];
    }
    return [{ x: 0, y: 0, width: 100, height: 44 }];
  };
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.open = (...args) => { opened.push(args); return null; };
  for (const script of ['assets/js/media.js', 'assets/vendor/bootstrap.bundle.min.js', 'assets/vendor/qrcode.js', 'assets/js/pix.js', 'script.js', 'assets/js/site.js']) {
    w.eval(fs.readFileSync(path.join(root, script), 'utf8'));
  }
  if (w.document.readyState !== 'complete') await new Promise(resolve => w.addEventListener('load', resolve, { once: true }));
  const $ = selector => w.document.querySelector(selector);
  return { dom, w, d: w.document, $, errors, copied, opened, close: () => dom.window.close() };
}

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
async function eventAction(element, name, action) {
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Event timeout: ${name}`)), 1500);
    element.addEventListener(name, () => { clearTimeout(timer); resolve(); }, { once: true });
    action();
  });
}

(async () => {
  for (const file of pageList) {
    const p = await open(file);
    assert.equal(p.errors.length, 0, `${file}: ${p.errors.join('\n')}`);
    assert.ok(p.w.bootstrap?.Modal);
    assert.equal(p.d.querySelectorAll('iframe').length, 0, 'No embedded YouTube player before click');
    p.close();
  }
  log(`${pageList.length} páginas carregam seus scripts sem erros; players do YouTube são incorporados apenas após clique`);

  let p = await open('index.html');
  p.$('[data-donation-next]').click();
  assert.equal(p.$('.donation-stack').dataset.donationIndex, '1');
  assert.ok(p.d.querySelectorAll('.donation-dots span')[1].classList.contains('is-active'));
  assert.equal([...p.d.querySelectorAll('.donation-card')].filter(card => !card.inert).length, 1);
  p.$('[data-donation-next]').click(); p.$('[data-donation-next]').click();
  assert.equal(p.$('.donation-stack').dataset.donationIndex, '0');
  assert.equal(p.$('[data-impact-amount="100"]').getAttribute('aria-pressed'), 'true');
  assert.match(p.$('#impactSummary').textContent, /1 cesta básica compacta/);
  assert.equal(p.$('.donation-card.is-active .donate-trigger').dataset.amount, '100');
  for (const [amount, title] of [[25, /1 kit para desenhar/], [50, /1 kit de materiais escolares/], [100, /1 cesta básica compacta/], [200, /2 cestas básicas compactas/]]) {
    p.$(`[data-impact-amount="${amount}"]`).click();
    assert.match(p.$('#impactAmount').textContent, new RegExp(String(amount)));
    assert.match(p.$('#impactSummary').textContent, title);
    assert.equal(p.$('#impactDescription').textContent, p.$(`[data-impact-amount="${amount}"]`).dataset.impactDescription);
    assert.equal(p.$('[data-impact-donate]').dataset.amount, String(amount));
    assert.match(p.$('[data-impact-donate]').textContent, new RegExp(String(amount)));
    assert.equal(p.d.querySelectorAll('[data-impact-amount][aria-pressed="true"]').length, 1);
    assert.equal(p.d.querySelectorAll('[data-impact-example].is-selected').length, 1);
    assert.equal(p.$('[data-impact-example].is-selected').dataset.impactExample, String(amount));
    assert.equal(p.d.querySelectorAll('[data-impact-selected]:not([hidden])').length, 1);
  }
  log('Carrossel e quatro valores de contribuição sincronizam exemplo, destaque, acessibilidade e botão');
  const opener = p.$('[data-impact-donate]');
  await eventAction(p.$('#donationModal'), 'shown.bs.modal', () => opener.click());
  assert.match(p.$('#donationAmountLabel').textContent, /200/);
  assert.equal(p.$('[data-donation-amount="200"]').getAttribute('aria-pressed'), 'true');
  assert.ok(p.$('#donationModal .pix-qr').src.startsWith('data:image/gif;base64,'));
  assert.equal(p.$('#pixPayment').hidden, false);
  assert.match(p.$('#pixQrHelp').textContent, /200/);
  p.$('#copyPixPayload').click(); await wait(0);
  assert.match(p.copied.at(-1), /5406200\.00/);
  for (const invalid of ['0', '-1', '1000001', '1.001', '']) {
    p.$('#donationCustomAmount').value = invalid;
    p.$('#donationCustomAmount').dispatchEvent(new p.w.Event('input', { bubbles: true }));
    assert.equal(p.$('#donationWhatsapp').getAttribute('aria-disabled'), 'true', invalid);
    assert.ok(!p.$('#donationWhatsapp').hasAttribute('href'));
    assert.equal(p.$('#pixPayment').hidden, true);
    assert.equal(p.$('#copyPixPayload').disabled, true);
    assert.equal(p.$('.pix-qr').hasAttribute('src'), false);
  }
  p.$('#donationCustomAmount').value = '75.50';
  p.$('#donationCustomAmount').dispatchEvent(new p.w.Event('input', { bubbles: true }));
  assert.equal(p.$('#donationWhatsapp').getAttribute('aria-disabled'), 'false');
  assert.match(decodeURIComponent(p.$('#donationWhatsapp').href), /75,5/);
  assert.equal(p.$('#pixPayment').hidden, false);
  p.$('#copyPixPayload').click(); await wait(0);
  assert.match(p.copied.at(-1), /540575\.50/);
  assert.match(p.$('#copyPixPayloadStatus').textContent, /Pix com valor copiado/);
  // Fallback de cópia em file:// ou quando a API de clipboard não está disponível.
  const writeText = p.w.navigator.clipboard.writeText;
  p.w.navigator.clipboard.writeText = async () => { throw new Error('Unavailable'); };
  p.d.execCommand = command => command === 'copy' && p.d.activeElement.value === p.copied.at(-1);
  p.$('#copyPixPayload').click(); await wait(0);
  assert.match(p.$('#copyPixPayloadStatus').textContent, /Pix com valor copiado/);
  assert.equal(p.d.activeElement, p.$('#copyPixPayload'));
  p.w.navigator.clipboard.writeText = writeText;
  p.$('#copyPix').click(); await wait(0);
  assert.equal(p.copied.at(-1), '11550709000187');
  await eventAction(p.$('#donationModal'), 'hidden.bs.modal', () => p.$('#donationModal .btn-close').click());
  assert.equal(p.d.activeElement, opener);
  log('Modal real do Bootstrap, valores inválidos, link de doação, QR, cópia de Pix e retorno de foco');
  p.$('.navbar-toggler').style.display = 'block';
  await eventAction(p.$('#mainNav'), 'shown.bs.collapse', () => p.$('.navbar-toggler').click());
  assert.equal(p.$('.navbar-toggler').getAttribute('aria-expanded'), 'true');
  await eventAction(p.$('#donationModal'), 'shown.bs.modal', () => p.$('#mainNav .donate-trigger').click());
  assert.ok(!p.$('#mainNav').classList.contains('show'));
  await eventAction(p.$('#donationModal'), 'hidden.bs.modal', () => p.$('#donationModal .btn-close').click());
  assert.equal(p.d.activeElement, p.$('.navbar-toggler'));
  log('Menu móvel abre, fecha ao doar e recebe o foco após fechar o modal');
  assert.equal(p.errors.length, 0, p.errors.join('\n')); p.close();

  p = await open('transparencia.html');
  const docs = () => [...p.d.querySelectorAll('[data-filter-item]')].filter(el => !el.hidden);
  assert.equal(docs().length, 26);
  p.$('[data-filter-search]').value = 'estatuto';
  p.$('[data-filter-search]').dispatchEvent(new p.w.Event('input'));
  assert.equal(docs().length, 1);
  p.$('[data-filter-year]').value = '2025'; p.$('[data-filter-year]').dispatchEvent(new p.w.Event('change'));
  assert.equal(docs().length, 1);
  p.$('[data-filter-search]').value = 'termo inexistente zz'; p.$('[data-filter-search]').dispatchEvent(new p.w.Event('input'));
  assert.equal(docs().length, 0); assert.ok(!p.$('[data-filter-empty]').hidden);
  log('Biblioteca: 26 PDFs, pesquisa, ano e estado sem resultados'); p.close();

  p = await open('noticias.html');
  p.$('[data-filter-search]').value = 'fisioterapia'; p.$('[data-filter-search]').dispatchEvent(new p.w.Event('input'));
  assert.equal([...p.d.querySelectorAll('[data-filter-item]')].filter(el => !el.hidden).length, 1);
  log('Pesquisa de notícias apresenta a reportagem correspondente'); p.close();

  p = await open('fisioterapia.html');
  p.$('.video-facade').click();
  assert.match(p.$('iframe').src, /^https:\/\/www.youtube-nocookie.com\/embed\/uDHRizneRKA/);
  assert.match(p.$('iframe').title, /Fisioterapia/);
  assert.equal(p.$('iframe').referrerPolicy, 'strict-origin-when-cross-origin');
  log('Player YouTube é incorporado no serviço correto somente após clique'); p.close();
  p = await open('fisioterapia.html', 'file:'); p.$('.video-facade').click();
  assert.equal(p.opened.length, 1); assert.match(p.opened[0][0], /youtube.com\/watch\?v=uDHRizneRKA/);
  assert.ok(!p.$('iframe'));
  log('Abertura direta por arquivo utiliza o link alternativo do YouTube'); p.close();

  p = await open('galeria.html');
  p.$('[data-filter-category="nossos espacos"]').click();
  const visible = [...p.d.querySelectorAll('[data-gallery-link]')].filter(el => !el.closest('[hidden]'));
  assert.ok(visible.length > 1 && visible.length < 18);
  await eventAction(p.$('#galleryModal'), 'shown.bs.modal', () => visible[0].click());
  assert.equal(p.$('#galleryFullImage').src, visible[0].href);
  p.$('[data-gallery-next]').click(); assert.equal(p.$('#galleryFullImage').src, visible[1].href);
  p.$('#galleryModal').dispatchEvent(new p.w.KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }));
  assert.equal(p.$('#galleryFullImage').src, visible[0].href);
  await eventAction(p.$('#galleryModal'), 'hidden.bs.modal', () => p.$('#galleryModal .btn-close').click());
  assert.equal(p.d.activeElement, visible[0]);
  log('Galeria filtra espaços, amplia a foto, navega por setas/teclado e restaura o foco'); p.close();

  p = await open('contato.html');
  assert.equal(p.$('#contactForm [type="submit"]').disabled, false);
  const submit = () => p.$('#contactForm').dispatchEvent(new p.w.Event('submit', { bubbles: true, cancelable: true }));
  submit(); assert.ok(p.$('#contactResult').hidden);
  for (const [id, value] of [['contactName','Pessoa de teste'],['contactEmail','teste@example.test'],['contactSubject','Atendimento e serviços'],['contactMessage','Gostaria de informações sobre as atividades.']]) {
    p.$(`#${id}`).value = value; p.$(`#${id}`).dispatchEvent(new p.w.Event('input', { bubbles: true }));
  }
  p.$('#contactConsent').checked = true; submit();
  assert.ok(!p.$('#contactResult').hidden);
  assert.match(decodeURIComponent(p.$('#contactWhatsapp').href), /Pessoa de teste/);
  assert.match(p.$('#contactWhatsapp').href, /^https:\/\/wa.me\/5532988559201/);
  assert.equal(p.opened.length, 0, 'No automatic external transmission');
  p.$('#contactMessage').value = 'Alterada'; p.$('#contactMessage').dispatchEvent(new p.w.Event('input', { bubbles: true }));
  assert.ok(p.$('#contactResult').hidden); assert.ok(!p.$('#contactWhatsapp').hasAttribute('href'));
  log('Contato valida os campos, prepara WhatsApp revisável e invalida rascunho após alterações'); p.close();

  p = await open('como-ajudar.html');
  p.$('[data-copy-pix]').click(); await wait(0); assert.equal(p.copied.at(-1), '11550709000187');
  await eventAction(p.$('#helpFaq1'), 'shown.bs.collapse', () => p.$('[data-bs-target="#helpFaq1"]').click());
  assert.ok(!p.$('#helpFaq0').classList.contains('show'));
  log('Pix da página de apoio e perguntas frequentes funcionam'); p.close();
  p = await open('noticias/cozinha-comunitaria.html');
  p.$('[data-share-page]').click(); await wait(0);
  assert.match(p.copied.at(-1), /noticias\/cozinha-comunitaria.html/);
  assert.equal(p.d.querySelectorAll('video source').length, 1);
  const video = p.$('video');
  const source = p.$('video source');
  assert.ok(source.src.startsWith('https://video.wixstatic.com/'));
  let loads = 0;
  video.load = () => { loads++; };
  source.dispatchEvent(new p.w.Event('error'));
  assert.equal(video.src, new URL(source.dataset.localSrc, p.w.location.href).href);
  assert.equal(loads, 1);
  video.dispatchEvent(new p.w.Event('error'));
  assert.equal(loads, 1, 'Sem repetição infinita quando a cópia local também falha');
  const image = p.$('img[data-local-src]');
  assert.ok(image.src.startsWith('https://'));
  image.dispatchEvent(new p.w.Event('error'));
  assert.equal(image.src, new URL(image.dataset.localSrc, p.w.location.href).href);
  assert.equal(p.errors.length, 0, p.errors.join('\n'));
  log('Notícia usa MP4 externo, imagens e vídeos retornam à cópia local após erro, sem repetição'); p.close();

  fs.mkdirSync(path.join(support, 'output'), { recursive: true });
  fs.writeFileSync(path.join(support, 'output/site-dom-tests.json'), JSON.stringify({ estado:'aprovado', ambiente:'jsdom; geometria simulada, sem teste visual', verificacoes:passed }, null, 2));
  console.log('ALL DOM TESTS PASSED');
})().catch(error => { console.error(error); process.exitCode = 1; });
