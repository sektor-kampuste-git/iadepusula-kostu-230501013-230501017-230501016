"""Local stdio MCP server exposing only synthetic read-only fixtures and evidence.

Start with python -m src.mcp_server. No listening network port or credentials.
Production order access requires authentication/authorization by Member 2.
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from src.rag import MevzuatRetriever
from src.tools import SiparisDeposu
from src.tools import cayma_suresi_hesapla as calculate_deadline
from src.tools import parasal_sinir_kontrol as check_threshold

server = FastMCP("iadepusula-uye1")
_depo = SiparisDeposu()
_retriever = MevzuatRetriever()
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)


@server.tool(annotations=READ_ONLY)
def siparis_detay_getir(siparis_no: str) -> dict:
    """Yalnız tek bir sentetik siparişi getirir; listeleme veya güncelleme yapmaz."""
    value = _depo.getir(siparis_no)
    return value.model_dump(mode="json") if value else {"durum": "SIPARIS_BULUNAMADI"}


@server.tool(annotations=READ_ONLY)
def cayma_suresi_hesapla(
    teslim_tarihi: str | None,
    basvuru_tarihi: str,
    cayma_bilgilendirildi: bool | None = True,
) -> dict:
    """ISO tarihlerle 14 takvim gününü hesaplar; iade kabul/ret kararı vermez."""
    return calculate_deadline(
        teslim_tarihi, basvuru_tarihi, cayma_bilgilendirildi=cayma_bilgilendirildi
    ).model_dump(mode="json")


@server.tool(annotations=READ_ONLY)
def parasal_sinir_kontrol(tutar_tl: str, yil: int) -> dict:
    """Başvuru yılının doğrulanmış sınırını kontrol eder; TL tutarını metin olarak alır."""
    return check_threshold(tutar_tl, yil).model_dump(mode="json")


@server.tool(annotations=READ_ONLY)
def mevzuat_ara(sorgu: str, top_k: int = 3) -> list[dict]:
    """Ağsız yerel derlemden madde, URL ve birebir metinle kanıt getirir."""
    return [item.model_dump(mode="json") for item in _retriever.search(sorgu, top_k)]


if __name__ == "__main__":
    server.run(transport="stdio")
