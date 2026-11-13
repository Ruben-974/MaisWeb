"""Decodifica os QRs reais renderizados pelo Chrome e valida o BR Code com Python."""
import binascii
import json
from pathlib import Path
import cv2
import numpy as np

SUPPORT = Path(__file__).resolve().parents[1]


def read_image(path):
    # imread não lida com todos os caminhos Unicode no Windows.
    return cv2.imdecode(np.frombuffer(path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)


def fields(payload):
    result = {}
    offset = 0
    while offset < len(payload):
        tag = payload[offset:offset+2]
        size = int(payload[offset+2:offset+4])
        assert tag not in result
        result[tag] = payload[offset+4:offset+4+size]
        offset += 4 + size
    assert offset == len(payload)
    return result


def main():
    config = json.loads((SUPPORT/'dados/pix-config.json').read_text(encoding='utf-8'))
    detector = cv2.QRCodeDetector()
    original, _, _ = detector.detectAndDecode(read_image(SUPPORT/config['imagem_original']))
    assert original == config['payload_original'], 'O payload deve coincidir com o QR oficial arquivado.'
    baseline = fields(original)
    report = json.loads((SUPPORT/'output/site-pix-browser-tests.json').read_text(encoding='utf-8'))
    for case in report['capturas']:
        payload, _, _ = detector.detectAndDecode(read_image(SUPPORT/'output'/case['arquivo']))
        assert payload == case['payload'], f"QR não corresponde ao Pix copiado: {case['arquivo']}"
        parsed = fields(payload)
        assert parsed['54'] == f"{case['valor']:.2f}"
        assert fields(parsed['26'])['01'] == config['chave']
        for tag, value in baseline.items():
            if tag != '63':
                assert parsed[tag] == value, f'Campo oficial alterado: {tag}'
        crc = f"{binascii.crc_hqx(payload[:-4].encode('ascii'), 0xffff):04X}"
        assert parsed['63'] == crc, 'CRC16 inválido'
    result = {'estado': 'aprovado', 'qr_codes_decodificados': len(report['capturas']),
              'verificacoes': ['valor', 'chave e dados oficiais', 'CRC16 independente', 'QR igual ao Pix Copia e Cola'],
              'pagamento_bancario': 'não realizado'}
    (SUPPORT/'output/site-pix-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
