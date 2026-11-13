/* BR Code Pix estático: preserva os dados oficiais e inclui o valor no campo 54. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AaciPix = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function checksum(text) {
    let crc = 0xffff;
    for (let index = 0; index < text.length; index++) {
      const code = text.charCodeAt(index);
      if (code < 32 || code > 126) throw new Error('Payload Pix com caracteres inválidos.');
      crc ^= code << 8;
      for (let bit = 0; bit < 8; bit++) {
        crc = ((crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1) & 0xffff;
      }
    }
    return crc.toString(16).toUpperCase().padStart(4, '0');
  }

  function readFields(payload) {
    const fields = [];
    const ids = new Set();
    for (let offset = 0; offset < payload.length;) {
      const header = payload.slice(offset, offset + 4);
      if (!/^\d{4}$/.test(header)) throw new Error('Formato Pix inválido.');
      const id = header.slice(0, 2);
      const size = Number(header.slice(2));
      const end = offset + 4 + size;
      if (end > payload.length || ids.has(id)) throw new Error('Campo Pix inválido.');
      fields.push({ id, value: payload.slice(offset + 4, end) });
      ids.add(id);
      offset = end;
    }
    return fields;
  }

  function buildPayload(basePayload, value) {
    if (typeof basePayload !== 'string') throw new Error('QR Pix de origem ausente.');
    const amount = Number(value);
    const cents = Math.round(amount * 100);
    if (!Number.isFinite(amount) || amount < 1 || amount > 1000000
      || !Number.isSafeInteger(cents) || Math.abs(amount * 100 - cents) > 0.000001) {
      throw new Error('Valor Pix inválido.');
    }

    const fields = readFields(basePayload);
    const crc = fields.pop();
    if (crc?.id !== '63' || !/^[\dA-F]{4}$/i.test(crc.value)
      || checksum(basePayload.slice(0, -4)) !== crc.value.toUpperCase()) {
      throw new Error('Integridade do QR Pix de origem inválida.');
    }
    const account = fields.find(field => field.id === '26');
    const accountFields = account ? readFields(account.value) : [];
    if (fields.find(field => field.id === '00')?.value !== '01'
      || fields.find(field => field.id === '53')?.value !== '986'
      || fields.find(field => field.id === '58')?.value !== 'BR'
      || accountFields.find(field => field.id === '00')?.value.toLowerCase() !== 'br.gov.bcb.pix'
      || !accountFields.some(field => field.id === '01' && field.value)) {
      throw new Error('QR de origem incompatível com Pix estático em reais.');
    }

    const transactionAmount = { id: '54', value: (cents / 100).toFixed(2) };
    const previousAmount = fields.findIndex(field => field.id === '54');
    if (previousAmount >= 0) fields[previousAmount] = transactionAmount;
    else {
      const insertion = fields.findIndex(field => Number(field.id) > 54);
      fields.splice(insertion < 0 ? fields.length : insertion, 0, transactionAmount);
    }
    const body = fields.map(field => field.id + String(field.value.length).padStart(2, '0') + field.value).join('') + '6304';
    return body + checksum(body);
  }

  return Object.freeze({ buildPayload });
});
