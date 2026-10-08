# OPERA HUB — Nova versão

Aplicativo-base do Opera Hub para centralização de operações industriais e logísticas.

## Modos / organizações

O Opera Hub usa **uma única base de código** e separa cada implantação por organização.

### Opera Hub — base oficial / demonstração

Slug técnico: `opera-hub-demo`.

- É o produto padrão.
- Serve como ambiente de demonstração comercial.
- É a referência para novos clientes.
- Possui navegação, aplicações, identidade, usuários e dados próprios.
- Não acessa configurações nem usuários de clientes.

### Cliente atual — Setta

Slug técnico: `setta`.

- Preserva exatamente os itens que já estavam configurados no Opera Hub.
- Mantém os 11 atalhos atuais, 9 aplicações, identidade visual e usuário já existente.
- URLs e customizações atuais foram mantidas.
- Alterações neste ambiente não afetam a base Opera Hub.

A seleção do ambiente é feita pela variável:

```env
OPERAHUB_DEFAULT_ORG=setta
```

Para o deploy oficial de demonstração:

```env
OPERAHUB_DEFAULT_ORG=opera-hub-demo
```

O código mantém `setta` como fallback por compatibilidade com o deploy já existente. Assim, publicar a nova versão não troca o cliente atual para o ambiente de demonstração acidentalmente.

## Arquitetura multiempresa

As tabelas multiempresa são:

- `operahub_organizations`
- `operahub_tenant_settings`
- `operahub_tenant_nav_items`
- `operahub_tenant_applications`
- `operahub_tenant_users`

Cada consulta e alteração usa a organização ativa. Imagens, configurações, navegação, aplicações, usuários e caches também são segmentados por organização.

As tabelas antigas foram mantidas intactas como camada de segurança da migração. Os dados atuais foram copiados para a organização Setta sem exclusões.

## Estado atual

- Layout principal responsivo conforme identidade Opera Hub.
- Menu lateral com atalhos para módulos existentes.
- Grade de aplicações com links configuráveis.
- Busca de aplicações.
- Painel de Configurações.
- Logo, favicon, banner e imagem de login configuráveis por organização.
- Usuários isolados por organização.
- Login restrito ao tenant do deploy.
- Identificação visual de **BASE / DEMO** ou **CLIENTE**.
- Persistência permanente no Supabase.
- Deploy preparado para Hostinger/Render.
- Endpoint de saúde: `/healthz`.

## Supabase

As leituras e gravações multiempresa passam por funções RPC protegidas pelo token de servidor `SUPABASE_WRITE_TOKEN`. As novas tabelas não são expostas diretamente aos papéis `anon` e `authenticated`.

Variáveis necessárias:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_WRITE_TOKEN`
- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `OPERAHUB_DEFAULT_ORG`

Nunca exponha `SUPABASE_WRITE_TOKEN` no navegador.

## Deploy

Build:

```bash
pip install -r requirements.txt
```

Start:

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

No ambiente do cliente atual:

```env
OPERAHUB_DEFAULT_ORG=setta
```

No ambiente base/demonstração:

```env
OPERAHUB_DEFAULT_ORG=opera-hub-demo
```

## Configurações

Acesse:

```text
/configuracoes
```

O painel altera somente a organização ativa. É possível configurar:

- logo principal;
- escala da logo;
- favicon;
- banner;
- imagem de login;
- links do menu lateral;
- links, status e imagens dos cartões;
- usuários e exigência de login.

## Regra para novos clientes

A organização `opera-hub-demo` é a **matriz funcional** do produto. Novos clientes devem nascer a partir dessa estrutura padrão e depois receber apenas suas customizações de marca, usuários, URLs, permissões e módulos contratados.

A organização Setta é um cliente e **não deve ser usada como matriz** para novos ambientes.

## Padrão visual de login

O Opera Hub segue a **referência visual de proporções do ATRIA** para telas de login, respeitando identidade própria e campos de acesso distintos.

O padrão de referência está documentado em [NEXONLABS/docs/PADRAO-VISUAL-LOGIN.md](https://github.com/juniorsousa-oss/NEXONLABS/blob/main/docs/PADRAO-VISUAL-LOGIN.md).

A versão mobile usa cartão centralizado com altura ajustada ao conteúdo, preservando imagem institucional, cores, identificação BASE/DEMO ou CLIENTE, usuário, senha e link de retorno. Alterações visuais não devem afetar os tenants, a autenticação nem o layout desktop validado.
