# Opera Hub — Arquitetura Multiempresa

## Objetivo

Manter uma única aplicação Opera Hub com ambientes totalmente separados por organização.

A hierarquia definida é:

1. **Opera Hub** — base oficial, padrão do produto e demonstração.
2. **Cliente** — cópia lógica do padrão com identidade, usuários, links e módulos próprios.

## Organizações iniciais

### opera-hub-demo

Nome exibido: **Opera Hub**

Função:

- matriz do produto;
- ambiente comercial de demonstração;
- referência para criação de novos clientes.

Não contém URLs, usuários ou configurações da Setta.

### setta

Nome exibido: **Setta**

Função:

- ambiente do cliente atual;
- contém os itens que já existiam antes da migração;
- preserva links, identidade, aplicações e usuário existentes.

## Isolamento

Toda informação operacional do Hub é vinculada a `organization_id`:

- configurações;
- navegação;
- aplicações;
- usuários;
- logos, favicons, banners, imagens de login e imagens dos módulos.

O navegador não escolhe livremente um `organization_id`. O servidor resolve a organização a partir do ambiente configurado e da sessão autenticada.

O login é validado dentro da organização do deploy. Credenciais de um cliente não autenticam em outro ambiente.

## Seleção do ambiente

Variável:

```env
OPERAHUB_DEFAULT_ORG=<slug>
```

Valores iniciais:

- `setta`
- `opera-hub-demo`

O fallback no código é `setta` exclusivamente para proteger o deploy existente durante a migração.

## Banco

Tabelas:

```text
operahub_organizations
operahub_tenant_settings
operahub_tenant_nav_items
operahub_tenant_applications
operahub_tenant_users
```

Chaves funcionais são compostas por organização, por exemplo:

```text
(organization_id, key)
(organization_id, id)
```

Usuários possuem unicidade de usuário/e-mail dentro da própria organização.

## Migração

A migração foi aditiva.

- Nenhuma tabela antiga foi apagada.
- Nenhum dado existente foi removido.
- Os registros anteriores foram copiados para `setta`.
- A base Opera Hub foi criada separadamente.
- As tabelas antigas permanecem disponíveis como segurança da transição.

## Cache e arquivos

As chaves de cache incluem o identificador da organização. Isso impede que logo, favicon, banner, avatar ou imagem de aplicação de um tenant seja reaproveitado por outro.

## Segurança

As novas tabelas têm RLS habilitado e não concedem acesso direto a `anon` ou `authenticated`.

O Flask acessa os dados por RPCs protegidas pelo segredo de servidor `SUPABASE_WRITE_TOKEN`.

As RPCs recebem e validam a organização no servidor antes de ler ou alterar registros.

## Regra de produto

A matriz para novos clientes é sempre **Opera Hub (`opera-hub-demo`)**.

Fluxo futuro de provisionamento:

```text
Opera Hub base
    ↓
nova organização cliente
    ↓
cópia da estrutura padrão
    ↓
branding + usuários + links + módulos do cliente
```

A Setta nunca deve ser clonada como base de outro cliente.
