const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const support = path.resolve(__dirname, '..');
const root = path.resolve(support, '..');
const { buildPayload } = require(path.join(root, 'assets/js/pix.js'));
const config = require(path.join(support, 'dados/pix-config.json'));
const qrGenerator = require(path.join(root, 'assets/js/vendor/qrcode.js'));

const base = config.payload_original;
// Referência calculada independentemente com Python binascii.crc_hqx(..., 0xffff).
const golden = '00020126360014BR.GOV.BCB.PIX0114115507090001875204000053039865406100.005802BR5925ASSOCIACAO DE APOIO AS CR6009SAO.PAULO62080504AACI63049DB9';
assert.equal(buildPayload(base, 100), golden);
assert.equal(buildPayload(golden, 100), golden, 'Não duplica o campo de valor');

function fields(payload) {
  const result = new Map();
  for (let position = 0; position < payload.length;) {
    const id = payload.slice(position, position + 2);
    const length = Number(payload.slice(position + 2, position + 4));
    assert.ok(!result.has(id), `Campo duplicado: ${id}`);
    result.set(id, payload.slice(position + 4, position + 4 + length));
    position += length + 4;
    assert.ok(position <= payload.length);
  }
  return result;
}

const original = fields(base);
for (const amount of [1, 25, 50, 75.50, 99, 100, 200, 999999.99, 1000000]) {
  const payload = buildPayload(base, amount);
  const parsed = fields(payload);
  assert.equal(parsed.get('54'), amount.toFixed(2));
  for (const [id, value] of original) {
    if (id !== '63') assert.equal(parsed.get(id), value, `Preserva ${id}`);
  }
  assert.equal(fields(parsed.get('26')).get('01'), config.chave);
}
for (const value of [null, '', 0, -1, NaN, Infinity, 1000001, 1.001]) {
  assert.throws(() => buildPayload(base, value));
}
assert.throws(() => buildPayload(base.slice(0, -4) + '0000', 100), /Integridade/);
assert.throws(() => buildPayload('000201', 100));
assert.equal(fields(buildPayload(golden, 50)).get('54'), '50.00');

const qr = qrGenerator(0, 'M');
qr.addData(golden, 'Byte');
qr.make();
const output = path.join(support, 'output');
fs.mkdirSync(output, { recursive: true });
fs.writeFileSync(path.join(output, 'pix-100.gif'), Buffer.from(qr.createDataURL(4, 16).split(',')[1], 'base64'));
console.log('PASS: valor, precisão, limites, integridade, atualização e dados oficiais do Pix; QR de referência gerado.');
