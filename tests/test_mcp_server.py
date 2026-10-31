import asyncio
import sys

import pytest

pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

from src.paths import ROOT  # noqa: E402


def test_stdio_server_lists_only_four_readonly_tools_and_serves_real_requests():
    async def run():
        config = StdioServerParameters(
            command=sys.executable, args=["-m", "src.mcp_server"], cwd=str(ROOT)
        )
        async with (
            stdio_client(config) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            await session.initialize()
            response = await session.list_tools()
            assert {tool.name for tool in response.tools} == {
                "siparis_detay_getir",
                "cayma_suresi_hesapla",
                "parasal_sinir_kontrol",
                "mevzuat_ara",
            }
            order = await session.call_tool("siparis_detay_getir", {"siparis_no": "SIP-2026-1001"})
            assert not order.isError and "1200.00" in order.content[0].text
            limit = await session.call_tool(
                "parasal_sinir_kontrol", {"tutar_tl": "186000.00", "yil": 2026}
            )
            assert not limit.isError and "HEYET_SINIRI_DISINDA" in limit.content[0].text
            invalid = await session.call_tool("siparis_detay_getir", {"siparis_no": "ALL"})
            assert invalid.isError

    asyncio.run(asyncio.wait_for(run(), timeout=25))
