# Materiais de apoio — fora do site público

Esta pasta preserva os materiais de pesquisa, edição e conferência. Ela não precisa ser enviada à hospedagem.

| Pasta / arquivo | Conteúdo |
| --- | --- |
| `referencias/` | PDF do layout e imagem de exemplo |
| `mapeamento AACI/AACI/` | Captura original do HTTrack |
| `mapeamento AACI/AACI-organizado/` | Acervo organizado, catálogo e documentos extraídos |
| `dados/` | Manifestos de imagens, documentos, páginas, exemplos de contribuição e configuração Pix |
| `assets-nao-utilizados/` | Imagens que não são carregadas pelo site atual, incluindo o QR Pix original usado na conferência |
| `tools/` | Gerador das páginas, templates, ferramentas do acervo e verificações |
| `output/` | Relatórios PDF, capturas e resultados de validação |
| `tmp/` | Arquivos intermediários e temporários preservados |
| `DOCUMENTACAO.md` | Documentação técnica e fontes do conteúdo |

## Editar e regenerar

Execute os comandos a partir da raiz do projeto, que contém `AACI/` e `arquivos/`:

```powershell
python -X utf8 arquivos/tools/build_aaci_site.py
python -X utf8 arquivos/tools/validate_aaci_site.py
```

O gerador lê os dados e templates desta pasta e grava os HTMLs em `AACI/`. Para alterações permanentes de conteúdo, edite `tools/build_aaci_site.py` e `tools/site-templates/`. Os estilos e scripts usados pelo navegador ficam diretamente em `AACI/`.

As fontes externas e sua última conferência estão em `dados/external-media.json`. Com `"preferencia": "externo"`, o gerador coloca essas URLs nos HTMLs e mantém as cópias locais como alternativa. Para voltar a priorizar os arquivos locais, altere para `"preferencia": "local"` e regenere as páginas. Para atualizar a conferência das URLs, execute `python -X utf8 arquivos/tools/check_external_media.py` na raiz do projeto; depois regenere os HTMLs. A conferência atual encontrou 87 endereços de mídia disponíveis. O QR Pix com valor continua gerado no navegador.

## Verificações de interação e Pix

As ferramentas opcionais em JavaScript usam `jsdom` e `playwright-core`, disponíveis no `NODE_PATH`. Eles não são dependências do site publicado. É possível fornecer o caminho do Chrome por `AACI_BROWSER_PATH`.

```powershell
node arquivos/tools/test_aaci_site.cjs
node arquivos/tools/test_aaci_pix.cjs
node arquivos/tools/test_aaci_pix_browser.cjs
python -X utf8 arquivos/tools/validate_aaci_pix.py
```

Para a verificação de layout via HTTP, inicie o servidor com a pasta `AACI/` como raiz e informe seu endereço:

```powershell
$env:AACI_PREVIEW_URL = 'http://127.0.0.1:5500'
node arquivos/tools/test_aaci_layout.cjs
```

O inventário histórico da separação e os hashes SHA256 daquele momento estão em `output/organizacao-plano.json`. Nenhum arquivo de origem foi excluído durante a organização.

O Git acompanha as ferramentas, templates, dados JSON e documentação desta pasta. Acervo, referências, cópias de mídia, saídas de teste e temporários são ignorados. `dados/external-documents.json` conserva as seis referências adicionais de documentos, permitindo regenerar o site sem o acervo completo. As verificações de integridade do acervo e das cópias locais continuam destinadas ao ambiente que possui esses arquivos.
