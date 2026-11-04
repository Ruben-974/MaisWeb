# AACI — página institucional

Página responsiva em HTML, CSS e JavaScript, baseada no arquivo `Homepage AACI - Desktop.pdf` e na fotografia `imagem-exemplo.png` fornecidos no projeto. Utiliza Bootstrap 5.3.8 com arquivos locais, sem etapa de build ou instalação de dependências.

## Como abrir

No Visual Studio Code, abra `Teste1/index.html` usando a extensão Live Server.

Também é possível executar, a partir da raiz do repositório:

```powershell
python -m http.server 5500 --directory Teste1
```

Depois, acesse <http://localhost:5500>. Os links para serviços externos precisam de conexão à internet.

## Conteúdo e funcionamento

- A navegação, os componentes de doação e as perguntas frequentes funcionam no navegador com JavaScript e Bootstrap.
- A chave Pix exibida é o CNPJ publicado pela AACI: `11550709000187`. O contato para doações usa o WhatsApp `(32) 98855-9201`, informado na página oficial de como ajudar.
- A newsletter direciona o visitante ao formulário do site oficial. Esta página local não possui backend nem armazena inscrições.
- Os documentos de transparência abrem PDFs hospedados no domínio oficial da AACI. Notícias e vídeos direcionam aos canais oficiais correspondentes.
- Foram omitidos depoimentos e contadores que não puderam ser confirmados nas fontes oficiais.

## Fontes consultadas em 2026-11-03

- [Página inicial da AACI](https://www.aaci.org.br/)
- [Serviços](https://www.aaci.org.br/servicos)
- [Como ajudar](https://www.aaci.org.br/comoajudar)
- [Contato](https://www.aaci.org.br/contato)
- [Prestação de contas](https://www.aaci.org.br/presta%C3%A7%C3%A3o-de-contas)
- [Vídeos](https://www.aaci.org.br/v%C3%ADdeos)
- [Política de Privacidade](https://www.aaci.org.br/politicadeprivacidade)

Na data da consulta, os dados de contato divergiam entre a página inicial e algumas subpáginas. Para o rodapé, foram priorizados o endereço e o telefone da página inicial: Rua Doutor Dias da Cruz, 487, Nova Era, Juiz de Fora/MG, e Social `(32) 98476-7527`. O WhatsApp de doações foi mantido conforme a página de como ajudar. O e-mail de contato é `aaci-@hotmail.com`.

Esta implementação é uma reprodução local do material de referência. Alterações futuras nos canais oficiais podem exigir atualização dos dados e links.

## Validação realizada

Conferidos a sintaxe do JavaScript, os arquivos locais, os IDs, as referências ARIA e os destinos das âncoras. Os testes com jsdom carregaram o Bootstrap real e verificaram carrosséis, modal, valores, cópia de Pix, perguntas frequentes, fechamento do menu móvel e restauração de foco. O jsdom não renderiza o layout: a automação do Chrome não foi autorizada no ambiente, portanto a conferência visual em navegador permanece pendente.
