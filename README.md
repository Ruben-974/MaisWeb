# AACI — site e materiais de apoio

O site pronto está em **[`AACI/`](AACI/)**. Essa pasta contém 20 páginas HTML, estilos, scripts, imagens, quatro vídeos locais, 26 PDFs públicos e as bibliotecas com suas licenças.

Imagens, documentos e MP4 usam primeiro os endereços públicos da AACI, Wix e YouTube. As imagens e os vídeos retornam automaticamente à cópia local se a fonte externa falhar; os PDFs oferecem o link “Baixar cópia local”. A imagem principal fornecida no modelo e o favicon continuam locais por não terem uma fonte pública equivalente. Todos os arquivos locais foram mantidos.

Os demais materiais estão isolados em **[`arquivos/`](arquivos/README.md)**: espelho HTTrack, catálogo, modelos, relatórios, dados de edição, ferramentas e temporários. O site funciona sem essa pasta.

## Abrir o site

No VS Code, abra [`AACI/index.html`](AACI/index.html) com Live Server. Ou execute na raiz do projeto:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory AACI
```

Acesse **http://127.0.0.1:5500**. Para hospedar, envie somente o conteúdo de `AACI/`, mantendo suas subpastas.

## Manutenção

As páginas já estão prontas; não precisam de instalação ou build para funcionar. As instruções para editar, regenerar e validar estão em [`arquivos/README.md`](arquivos/README.md). A documentação completa está em [`arquivos/DOCUMENTACAO.md`](arquivos/DOCUMENTACAO.md).

## O que vai para o GitHub

O `.gitignore` prioriza HTML, CSS, JavaScript, ferramentas, templates, configurações JSON e documentação. Cópias de mídia, PDFs, acervo HTTrack, relatórios gerados e temporários ficam no computador.

As únicas imagens mantidas no Git são `AACI/assets/hero.webp` e `AACI/assets/favicon.png`, cerca de 220 KB no total: elas ainda não têm uma fonte externa e preservam a apresentação da página. As demais mídias usam os links públicos configurados; suas cópias locais são opcionais no repositório. Para disponibilizar também os botões de download local em uma hospedagem, envie essas cópias separadamente.

O gerador usa os pequenos arquivos de `arquivos/dados/` e os templates de `arquivos/tools/`; não precisa do espelho HTTrack para regenerar as páginas. Os arquivos já enviados em commits anteriores continuam no histórico. As regras de exclusão passam a valer nos próximos commits.
