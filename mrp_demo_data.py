"""Dados exclusivamente fictícios do módulo MRP DEMO."""
from dataclasses import asdict, dataclass
from typing import Literal
import unicodedata

Status = Literal["critico", "atencao", "no_prazo", "nao_apto"]
Sort = Literal["prioridade", "codigo", "descricao", "demanda", "estoque", "semana"]

@dataclass(frozen=True)
class Material:
    codigo: str
    descricao: str
    tipo: str
    demanda: int
    estoque: int
    sc: int
    pc: int
    semana: str
    status: Status

_NAMES = (
    ("Contator tripolar 32 A", "MP"), ("Fonte 24 VCC / 10 A", "MP"),
    ("Disjuntor tripolar 63 A", "MP"), ("Borne de passagem 6 mm²", "MP"),
    ("Relé de interface 24 VCC", "MP"), ("Chave seccionadora 250 A", "MP"),
    ("Cabo de controle 4 × 1,5 mm²", "MP"), ("Terminal olhal M6", "MP"),
    ("Trilho DIN 35 mm", "MP"), ("Bloco de contatos 1NA + 1NF", "MP"),
    ("Transformador de corrente", "PI"), ("Módulo de sinalização", "PI"),
    ("Duto ventilado 40 × 60 mm", "MP"), ("Painel de comando", "PA"),
    ("Sensor de temperatura", "MP"), ("Suporte de montagem", "PI"),
)
_ORDER = {"critico":0, "atencao":1, "no_prazo":2, "nao_apto":3}
_EXAMPLES = (
    (120,35,0,40,"2026-47","critico"), (48,12,8,24,"2026-47","critico"),
    (72,30,0,60,"2026-48","atencao"), (240,80,40,120,"2026-48","atencao"),
    (64,90,0,0,"2026-48","no_prazo"), (24,24,0,0,"2026-49","no_prazo"),
    (180,260,0,0,"2026-49","no_prazo"), (360,400,0,0,"2026-50","no_prazo"),
    (75,38,0,0,"2026-50","nao_apto"), (40,16,0,0,"2026-50","nao_apto"),
    (8,1,0,3,"2026-51","critico"), (12,12,0,0,"2026-51","no_prazo"),
    (70,37,20,50,"2026-51","atencao"), (9,10,0,0,"2026-52","no_prazo"),
    (60,62,0,8,"2026-52","no_prazo"), (15,13,0,0,"2026-52","nao_apto"),
)
MATERIALS = tuple(Material(f"00841{100*j+i+21:03}", f"{nome}{' · variante '+str(j+1) if j else ''}", tipo, *ex)
                  for j in range(3) for i, ((nome, tipo), ex) in enumerate(zip(_NAMES,_EXAMPLES))
                  if j == 0 or i not in (8,9,15))
BY_CODE = {m.codigo:m for m in MATERIALS}
COUNTS = {s:sum(m.status==s for m in MATERIALS) for s in _ORDER}


def normal(value: str):
    return "".join(c for c in unicodedata.normalize("NFKD",value.casefold()) if not unicodedata.combining(c))

def materials(q="", status=None, tipo=None, page=1, size=10,
              sort="prioridade", descending=False):
    term=normal(q.strip())
    all_rows=[m for m in MATERIALS if (not status or m.status==status) and (not tipo or m.tipo==tipo)
              and (not term or term in normal(f"{m.codigo} {m.descricao}"))]
    all_rows.sort(key=lambda item:(_ORDER[item.status],item.codigo))
    if sort!="prioridade":
        all_rows.sort(key=lambda item: normal(item.descricao) if sort=="descricao" else getattr(item,sort),reverse=descending)
    elif descending:
        all_rows.reverse()
    pages=max(1,(len(all_rows)+size-1)//size)
    page=min(page,pages)
    start=(page-1)*size
    return {"demo":True,"semana":"2026-47","counts":COUNTS,"total_demo":len(MATERIALS),
            "total":len(all_rows),"page":page,"pages":pages,"size":size,
            "rows":[asdict(x) for x in all_rows[start:start+size]]}

def material(codigo):
    m=BY_CODE.get(codigo)
    if m is None:
        return None
    metade=m.demanda//2
    return {**asdict(m),"demo":True,
            "necessidades":[{"projeto":"Projeto exemplo A","semana":m.semana,"quantidade":m.demanda-metade},
                           {"projeto":"Projeto exemplo B","semana":m.semana,"quantidade":metade}],
            "compras":[{"tipo":k,"quantidade":n} for k,n in (("S.C.",m.sc),("P.C.",m.pc)) if n],
            "saldo_referencia":m.estoque+m.pc-m.demanda}

