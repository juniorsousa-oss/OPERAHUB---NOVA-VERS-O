-- Opera Hub: assinatura institucional própria por organização.
-- Migração aditiva; não altera logos, módulos ou dados de outros clientes.
alter table public.operahub_tenant_settings
  add column if not exists institutional_logo_data text not null default '';

create or replace function public.operahub_get_asset_v2(
  p_token text,
  p_organization_id bigint,
  p_asset_type text,
  p_key text default null
)
returns text
language plpgsql
security definer
set search_path to 'public', 'extensions'
as $function$
declare v_value text := '';
begin
  if not public.operahub_token_ok(p_token) then
    raise exception 'unauthorized';
  end if;
  if not exists (
    select 1 from public.operahub_organizations
    where id=p_organization_id and active=true
  ) then
    raise exception 'organization_not_found';
  end if;

  case p_asset_type
    when 'logo' then
      select logo_data into v_value from public.operahub_tenant_settings
      where organization_id=p_organization_id and id='main';
    when 'favicon' then
      select favicon_data into v_value from public.operahub_tenant_settings
      where organization_id=p_organization_id and id='main';
    when 'hero' then
      select hero_data into v_value from public.operahub_tenant_settings
      where organization_id=p_organization_id and id='main';
    when 'login' then
      select login_image_data into v_value from public.operahub_tenant_settings
      where organization_id=p_organization_id and id='main';
    when 'institutional_logo' then
      select institutional_logo_data into v_value from public.operahub_tenant_settings
      where organization_id=p_organization_id and id='main';
    when 'app_image' then
      select image_data into v_value from public.operahub_tenant_applications
      where organization_id=p_organization_id and key=p_key;
    when 'user_avatar' then
      select avatar_data into v_value from public.operahub_tenant_users
      where organization_id=p_organization_id
        and id=p_key::uuid
        and is_active=true;
    else
      raise exception 'asset_type_invalid';
  end case;

  return coalesce(v_value,'');
end;
$function$;

create or replace function public.operahub_set_institutional_brand_v1(
  p_token text,
  p_organization_id bigint,
  p_image_data text
)
returns void
language plpgsql
security definer
set search_path to 'public', 'extensions'
as $function$
begin
  if not public.operahub_token_ok(p_token) then
    raise exception 'unauthorized';
  end if;
  if not exists (
    select 1 from public.operahub_organizations
    where id=p_organization_id and active=true
  ) then
    raise exception 'organization_not_found';
  end if;
  if length(coalesce(p_image_data,'')) > 10500000 then
    raise exception 'image_too_large';
  end if;
  if coalesce(p_image_data,'') <> '' and
     p_image_data not like 'data:image/png;base64,%' and
     p_image_data not like 'data:image/jpeg;base64,%' and
     p_image_data not like 'data:image/webp;base64,%' then
    raise exception 'image_type_invalid';
  end if;

  insert into public.operahub_tenant_settings (
    organization_id,id,institutional_logo_data,updated_at
  ) values (
    p_organization_id,'main',coalesce(p_image_data,''),now()
  )
  on conflict(organization_id,id) do update set
    institutional_logo_data=excluded.institutional_logo_data,
    updated_at=now();
end;
$function$;

-- O endpoint REST usa a chave pública + token de gravação interno,
-- verificado dentro das funções SECURITY DEFINER.
grant execute on function public.operahub_get_asset_v2(text,bigint,text,text)
  to anon, authenticated, service_role;
grant execute on function public.operahub_set_institutional_brand_v1(text,bigint,text)
  to anon, authenticated, service_role;
notify pgrst, 'reload schema';
