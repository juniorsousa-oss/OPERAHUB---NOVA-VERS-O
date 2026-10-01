# OPERA HUB — Nova versão

Aplicativo-base do Opera Hub para centralização de operações industriais e logísticas.

## Estado atual

- Layout principal responsivo conforme identidade Opera Hub.
- Menu lateral com atalhos para módulos existentes.
- Grade de aplicações com links configuráveis.
- Busca de aplicações.
- Painel de Configurações.
- Logo e favicon configuráveis pelo próprio app.
- Persistência permanente no Supabase.
- Deploy preparado para Render.
- Endpoint de saúde: `/healthz`.

## Supabase

A configuração foi migrada do SQLite para o Supabase.

Tabelas:

- `operahub_settings`
- `operahub_nav_items`
- `operahub_applications`
- `operahub_private`

As leituras são públicas para o app e as alterações são feitas por funções RPC protegidas por um token de escrita.

### Variáveis necessárias no Render

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_WRITE_TOKEN`
- `SECRET_KEY`
- `ADMIN_PASSWORD`

O `render.yaml` já contém URL e chave publishable do projeto. O token de escrita deve ser criado como variável secreta no Render.

## Render

Build:

```bash
pip install -r requirements.txt
```

Start:

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

## Configurações

Acesse:

```
/configuracoes
```

No painel é possível:

- enviar a logo principal;
- definir a escala da logo;
- enviar o favicon;
- informar os links do menu lateral;
- informar os links dos cartões de aplicações;
- escolher se cada destino abre em nova aba.

Todas essas alterações são persistidas no Supabase.
