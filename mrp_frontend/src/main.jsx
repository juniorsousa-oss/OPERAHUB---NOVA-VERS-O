import React, {useEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import "./mrp.css";

const root=document.getElementById("mrp-root");
const endpoint=root.dataset.api;
const pt=new Intl.NumberFormat("pt-BR");
const num=x=>pt.format(x);
const statusLabels={critico:"Crítico",atencao:"Atenção",no_prazo:"No prazo",nao_apto:"Não apto"};
const indicatorLabels={critico:"Críticos",atencao:"Atenção",no_prazo:"No prazo",nao_apto:"Não aptos"};
const fields=[
 ["codigo","Código"],["descricao","Descrição"],["demanda","Demanda"],["estoque","Estoque"],
 ["sc","S.C."],["pc","P.C."],["semana","Necessidade"],["status","Atendimento"],
];
const sorts=new Set(["codigo","descricao","demanda","estoque","semana"]);
function Tag({status}) {return <span className={`mrp-tag ${status}`}>{statusLabels[status]}</span>}
function week(id){const [a,b]=id.split("-");return `${b}/${a}`;}
async function api(url,signal){
 const r=await fetch(url,{signal,credentials:"same-origin"});
 if(r.status===401)throw new Error("session");
 if(!r.ok)throw new Error("request");
 return r.json();
}
function ErrorLine({error,retry}){
 return error==="session" ? <div className="mrp-error" role="alert">Sua sessão terminou. <a href={root.dataset.login}>Entre novamente</a>.</div>
 : <div className="mrp-error" role="alert">Não foi possível carregar os dados. <button type="button" onClick={retry}>Tentar novamente</button></div>;
}
function Detail({material,close}){
 const dialog=useRef(null);
 const [data,setData]=useState(null),[error,setError]=useState(""),[retry,refresh]=useState(0),[tab,selectTab]=useState("Necessidades");
 useEffect(()=>{
  const el=dialog.current;
  el.showModal();
  return ()=>{if(el.open)el.close();};
 },[]);
 useEffect(()=>{
  const req=new AbortController();
  api(`${endpoint}/${encodeURIComponent(material.codigo)}`,req.signal).then(setData).catch(e=>{if(e.name!=="AbortError")setError(e.message);});
  return ()=>req.abort();
 },[material.codigo,retry]);
 const tabs=["Necessidades","Compras"];
 return <dialog className="mrp-dialog" ref={dialog} aria-labelledby="mrp-detail-title" onCancel={e=>{e.preventDefault();close();}} onClick={e=>{if(e.target===e.currentTarget)close();}}>
  <div className="mrp-detail">
   <header className="mrp-detail-head"><div><small>Detalhe do material · DEMO</small><h2 id="mrp-detail-title">{material.descricao}</h2><p>{material.codigo} · {material.tipo}</p></div><button type="button" autoFocus className="mrp-close" onClick={close} aria-label="Fechar detalhe">×</button></header>
   <div className="mrp-material-state"><Tag status={material.status}/><span>Primeira necessidade: semana {week(material.semana)}</span></div>
   <div className="mrp-summary">{[["Demanda","demanda"],["Estoque","estoque"],["S.C.","sc"],["P.C.","pc"]].map(([label,key])=><div key={key}><span>{label}</span><strong>{num(material[key])}</strong></div>)}</div>
   {error ? <ErrorLine error={error} retry={()=>{setError("");refresh(x=>x+1);}}/> : !data ? <p role="status">Carregando detalhe…</p> : <>
    <p className="mrp-detail-note">Saldo ilustrativo após estoque e pedidos: <strong>{num(data.saldo_referencia)} un.</strong></p>
    <div className="mrp-tabs" role="group" aria-label="Seções do material">{tabs.map(x=><button type="button" key={x} aria-pressed={tab===x} onClick={()=>selectTab(x)}>{x}</button>)}</div>
    {tab==="Necessidades" ? <table className="mrp-mini"><thead><tr><th>Projeto</th><th>Semana</th><th>Qtd.</th></tr></thead><tbody>{data.necessidades.map(x=><tr key={x.projeto}><td>{x.projeto}</td><td>{week(x.semana)}</td><td>{num(x.quantidade)}</td></tr>)}</tbody></table>
      : data.compras.length ? <table className="mrp-mini"><thead><tr><th>Tipo</th><th>Qtd.</th></tr></thead><tbody>{data.compras.map(x=><tr key={x.tipo}><td>{x.tipo}</td><td>{num(x.quantidade)}</td></tr>)}</tbody></table> : <p>Sem solicitações ou pedidos de compra neste exemplo.</p>}
   </>}
   <footer><button type="button" className="mrp-btn" onClick={close}>Voltar à consulta</button></footer>
  </div>
 </dialog>;
}
function App(){
 const [data,setData]=useState(null),[error,setError]=useState(""),[pending,busy]=useState(true),[retry,refresh]=useState(0);
 const [draft,setDraft]=useState(""),[term,search]=useState(""),[status,setStatus]=useState(""),[tipo,setTipo]=useState("");
 const [page,setPage]=useState(1),[size,setSize]=useState(10),[sorting,sort]=useState({sort:"prioridade",descending:false});
 const [selected,detail]=useState(null);
 useEffect(()=>{
  const req=new AbortController();
  busy(true);setError("");
  const opts=new URLSearchParams({q:term,status,tipo,page,size,...sorting});
  api(`${endpoint}?${opts}`,req.signal).then(x=>{setData(x);busy(false);}).catch(e=>{if(e.name!=="AbortError"){setError(e.message);busy(false);}});
  return ()=>req.abort();
 },[term,status,tipo,page,size,sorting,retry]);
 const reset=()=>{setDraft("");search("");setStatus("");setTipo("");setPage(1);};
 const chooseStatus=s=>{setStatus(s);setPage(1);};
 const order=k=>{sort(s=>({sort:k,descending:s.sort===k?!s.descending:false}));setPage(1);};
 const filters=!!(term||status||tipo);
 return <div className="mrp-page">
  <div className="mrp-title"><div><p>Planejamento de materiais <span aria-hidden="true">›</span> Consulta</p><h1>MRP atual</h1><span>Demanda, estoque e previsão por material.</span></div><div className="mrp-meta"><strong>DEMO · Somente consulta</strong><span>{data ? `Semana ${week(data.semana)} · ` : ""}Dados fictícios</span></div></div>
  <div className="mrp-indicators" role="group" aria-label="Filtrar por atendimento">
   {["","no_prazo","atencao","critico","nao_apto"].map(s=><button type="button" key={s} className={s} aria-pressed={status===s} onClick={()=>chooseStatus(s)}><strong>{data ? num(s?data.counts[s]:data.total_demo) : "—"}</strong><span>{s?indicatorLabels[s]:"Todos os materiais"}</span></button>)}
  </div>
  <section className="mrp-card" aria-label="Lista de materiais">
   <div className="mrp-card-title">Demanda geral</div>
   <form className="mrp-tools" onSubmit={e=>{e.preventDefault();search(draft.trim());setPage(1);}}>
    <label className="mrp-search"><span className="mrp-sr">Buscar por código ou descrição</span><input value={draft} onChange={e=>setDraft(e.target.value)} type="search" placeholder="Buscar por código ou descrição" maxLength={100}/></label>
    <button type="submit" className="mrp-btn mrp-primary">Buscar</button>
    <label className="mrp-filter" aria-label="Filtrar por tipo"><select value={tipo} onChange={e=>{setTipo(e.target.value);setPage(1);}}><option value="">Todos os tipos</option><option value="MP">Matéria-prima</option><option value="PI">Intermediário</option><option value="PA">Produto acabado</option></select></label>
    {filters && <button type="button" className="mrp-btn" onClick={reset}>Limpar filtros</button>}
   </form>
   {error ? <ErrorLine error={error} retry={()=>refresh(x=>x+1)}/> : !data ? <p role="status" className="mrp-empty">Carregando materiais…</p>
    : <div aria-busy={pending}>
    {pending&&<span className="mrp-sr" role="status">Atualizando a lista</span>}
    {data.rows.length ? <table className="mrp-table"><thead><tr>{fields.map(([k,n])=><th key={k} scope="col" aria-sort={sorting.sort===k?(sorting.descending?"descending":"ascending"):undefined}>{sorts.has(k)?<button type="button" onClick={()=>order(k)}>{n}{sorting.sort===k?(sorting.descending?" ↓":" ↑"):""}</button>:n}</th>)}<th scope="col">Detalhe</th></tr></thead><tbody>
     {data.rows.map(m=><tr key={m.codigo}><td className="mrp-code">{m.codigo}</td><td className="mrp-desc">{m.descricao}</td>{[["demanda","Demanda"],["estoque","Estoque"],["sc","S.C."],["pc","P.C."]].map(([k,label])=><td key={k} className="mrp-number" data-label={label}>{num(m[k])}</td>)}<td className="mrp-week" data-label="Necessidade">{week(m.semana)}</td><td className="mrp-status"><Tag status={m.status}/></td><td className="mrp-open-cell"><button type="button" className="mrp-open" aria-label={`Detalhar material ${m.codigo}`} onClick={()=>detail(m)}>Detalhe <span aria-hidden="true">›</span></button></td></tr>)}
    </tbody></table>:<p className="mrp-empty">Nenhum material encontrado para os filtros selecionados.</p>}
    <footer className="mrp-pagination"><span aria-live="polite">{data.total? `${num((data.page-1)*data.size+1)}–${num((data.page-1)*data.size+data.rows.length)} de ${num(data.total)} ${data.total===1?"material":"materiais"}` : "0 materiais"}</span><div>
     <label>Por página <select value={size} onChange={e=>{setSize(+e.target.value);setPage(1);}} aria-label="Materiais por página">{[10,20,50].map(n=><option key={n}>{n}</option>)}</select></label>
     <button type="button" aria-label="Página anterior" disabled={pending||data.page<=1} onClick={()=>setPage(data.page-1)}>‹</button><span>{data.page} / {data.pages}</span><button type="button" aria-label="Próxima página" disabled={pending||data.page>=data.pages} onClick={()=>setPage(data.page+1)}>›</button>
    </div></footer>
   </div>}
  </section>
  {selected&&<Detail key={selected.codigo} material={selected} close={()=>detail(null)}/>}
 </div>;
}
createRoot(root).render(<App/>);
