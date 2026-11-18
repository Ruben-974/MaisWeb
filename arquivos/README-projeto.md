# AACI — site e materiais de apoio

O site está diretamente na raiz do projeto:

```text
+Web/
├── index.html
├── robots.txt
├── sitemap.xml
├── pages/              # demais páginas HTML e artigos
├── assets/
│   ├── css/            # reset.css, style.css, pages.css e Bootstrap
│   ├── js/             # main.js, módulos e bibliotecas
│   ├── img/            # imagens e miniaturas
│   ├── fonts/          # reservada para fontes locais
│   ├── documents/      # cópias locais dos PDFs
│   ├── media/          # cópias locais dos vídeos
│   └── licenses/       # licenças das bibliotecas
└── arquivos/           # apoio: dados, ferramentas, acervo e relatórios
```

`.git/`, `.gitignore` e `.gitattributes` permanecem na raiz para o controle de versão. Os materiais de apoio, relatórios e temporários foram reunidos em `arquivos/`. As antigas pastas `output/` e `tmp/` estão preservadas em `output/raiz-anterior/` e `tmp/raiz-anterior/`, dentro desta pasta. Os relatórios de reuniões estão em `relatorios/Relatorio +Web/`.

## Abrir o site

Abra [index.html](../index.html) com Live Server, ou execute na raiz do projeto:

```powershell
python -m http.server 5500 --bind 127.0.0.1
```

Acesse http://127.0.0.1:5500. Para hospedar, envie somente `index.html`, `robots.txt`, `sitemap.xml`, `pages/` e `assets/`. `arquivos/` contém materiais de trabalho e não deve ser publicado.

## Conteúdo e manutenção

São 21 páginas, com navegação, notícias, vídeos, documentos e doações via Pix. As fontes externas das mídias continuam prioritárias; as cópias locais são mantidas como alternativa. As fontes atuais são Arial e Georgia, sem necessidade de arquivo de fonte adicional.

O domínio de `robots.txt` e `sitemap.xml` é configurado em [dados/site-config.json](dados/site-config.json), inicialmente como `https://www.aaci.org.br`.

As instruções de edição e validação estão em [README.md](README.md) e [DOCUMENTACAO.md](DOCUMENTACAO.md). O gerador e as ferramentas usam a raiz atual do projeto, sem recriar uma pasta `AACI/`.

## GitHub

O `.gitignore` prioriza HTML, CSS, JavaScript, ferramentas, dados JSON e documentação. Mídias, documentos, acervo, relatórios e temporários continuam locais. As imagens essenciais `assets/img/banner.webp` e `assets/img/favicon.png` são as exceções para preservar a apresentação sem uma fonte externa equivalente.
