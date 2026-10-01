# OPERA HUB — Nova versão

Aplicativo-base do Opera Hub, seguindo a identidade visual validada para operações industriais e logísticas.

## Estrutura inicial

- Dashboard principal responsivo.
- Menu lateral no padrão Opera Hub.
- Banner institucional.
- Cards de indicadores preparados para futuras integrações.
- Grade de aplicações no layout aprovado.
- Busca de aplicações.
- Painel de **Configurações** para informar links externos de:
  - módulos do menu lateral;
  - cartões de aplicações.
- Links podem abrir na mesma aba ou em uma nova aba.
- Senha administrativa opcional via variável de ambiente.
- Endpoint de saúde: `/healthz`.

Os módulos ainda não são implementados internamente. Nesta fase, o Opera Hub funciona como central de acesso aos aplicativos existentes. Conforme cada módulo for desenvolvido, o link externo poderá ser substituído pela rota interna correspondente.

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

No Windows:

```powershell
.venv\Scripts\activate
```

Acesse:

- Aplicação: `http://localhost:5000`
- Configurações: `http://localhost:5000/configuracoes`

## Render

O repositório já contém `render.yaml`.

No Render, crie um **Blueprint** a partir deste repositório ou um novo **Web Service** com:

- Build: `pip install -r requirements.txt`
- Start: `gunicorn --bind 0.0.0.0:$PORT app:app`

### Variáveis

- `SECRET_KEY`: segredo da sessão.
- `ADMIN_PASSWORD`: senha para proteger o menu de configurações.
- `DATA_DIR`: opcional. Diretório do SQLite.

Sem `ADMIN_PASSWORD`, a tela de configurações fica aberta para facilitar a validação inicial.

## Persistência

Os links são salvos em SQLite. Em um serviço Render sem disco persistente, alterações feitas pela interface podem ser perdidas quando a instância for recriada.

Para produção, use uma destas opções:

1. Render Persistent Disk e defina `DATA_DIR` para o ponto de montagem.
2. Migrar a configuração para Supabase/PostgreSQL.

A interface foi estruturada para permitir essa migração sem alterar o layout principal.
