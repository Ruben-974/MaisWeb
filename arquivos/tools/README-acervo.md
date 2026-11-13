# Processamento do acervo AACI

O resultado pronto está em `arquivos/mapeamento AACI/AACI-organizado`. Abra `index.html`; não precisa executar estes scripts para consultar os arquivos.

Os scripts utilizam Python com Pillow, lxml, PyMuPDF, ReportLab e imageio-ffmpeg. A etapa OCR usa Windows com o reconhecimento de Português (Brasil) instalado. Os caminhos da origem e do resultado estão no início de `mapear_acervo_aaci.py`.

Os comandos abaixo s?o executados a partir da raiz do projeto, que cont?m `AACI/` e `arquivos/`.

## Etapas do processo

1. `python -X utf8 arquivos/tools/mapear_acervo_aaci.py`: lê e inventaria a captura, copia conteúdo único, extrai textos, valida vídeos e prepara OCR dos PDFs. Recusa iniciar uma extração completa se a coleção já existir, para evitar misturar versões.
2. `python -X utf8 arquivos/tools/finalizar_acervo_aaci.py --prepare-ocr`: acrescenta imagens representativas à fila OCR.
3. `powershell -NoProfile -File arquivos/tools/ocr_acervo_aaci.ps1 -QueuePath "CAMINHO_ABSOLUTO/arquivos/tmp/aaci-mapeamento/ocr-fila-completa.json"`: reconhece os textos em português.
4. `python -X utf8 arquivos/tools/finalizar_acervo_aaci.py`: incorpora OCR, resolve referências, atribui nomes e gera catálogos HTML/CSV/JSON.
5. `python -X utf8 arquivos/tools/relatorio_acervo_aaci.py`: gera a síntese editorial e o PDF em `arquivos/output/pdf`, com uma cópia na coleção.
6. `python -X utf8 arquivos/tools/verificar_acervo_aaci.py`: confere hashes de todos os originais e cópias, vínculos, cobertura e integridade estrutural do relatório.

Para uma captura nova, utilize outra pasta de destino ou preserve a coleção atual antes de repetir o processo. A origem não é modificada. As classificações usam as páginas de origem e uma revisão visual selecionada; os textos de OCR continuam identificados como tais.

As imagens intermediárias de OCR e de revisão do PDF são temporárias. Os textos resultantes, miniaturas de consulta e verificações permanecem na coleção organizada.
