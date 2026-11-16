"""Gera os ícones do OPERA HUB com o favicon vetorial já utilizado."""
from pathlib import Path
import io
import cairosvg
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"static/favicon.svg"
OUT=ROOT/"static/pwa"
OUT.mkdir(parents=True,exist_ok=True)
for size in (192,512):
    img=Image.open(io.BytesIO(cairosvg.svg2png(url=str(SOURCE),output_width=size,output_height=size))).convert("RGBA")
    path=OUT/f"icon-{size}.png"
    img.save(path,format="PNG",optimize=True)
    assert Image.open(path).size==(size,size)
    print(path.relative_to(ROOT))
