"""Build verification companion: exercise installed wheel resources outside checkout.

Usage: python scripts/verify_package.py artifacts/wheels
The subprocess uses existing runtime dependencies, but imports app code and data
only from the extracted wheel. It never loads .env or makes provider calls.
"""

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROBE = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
installed_root = Path(sys.argv[1]).resolve()
import src
from src.paths import DATA, ROOT
from src.tools import SiparisDeposu, parasal_sinir_kontrol
from src.rag import MevzuatRetriever
from src.agent import AgentLimits, ButceliAjan
from src.config import load_configuration
from src.schemas import KararTaslagi
from src.llm_client import LLMClient
from src.tracing import write_trace
from src.costs import monthly_estimate
import maliyet_hesapla
from eval.eval_kosucu import load_cases, evaluate
assert Path(src.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
assert DATA.is_relative_to(Path(sys.argv[1]).resolve())
assert ROOT == Path.cwd()
assert str(SiparisDeposu().getir('SIP-2026-1001').fatura_tutari_tl) == '1200.00'
assert parasal_sinir_kontrol('186000.00', 2026).durum == 'HEYET_SINIRI_DISINDA'
assert MevzuatRetriever().search('14 günlük cayma hakkı')
assert len(load_cases()) == 30
assert evaluate(load_cases())['gecme_orani'] >= .85
from eval.retrieval import load_retrieval_cases, benchmark
assert len(load_retrieval_cases()) == 44
retrieval_report = benchmark(load_retrieval_cases(), MevzuatRetriever, name='lexical')
assert retrieval_report['summary']['completed'] == 44
assert retrieval_report['api']['request_count'] == 0
import contextlib, io, json
from src.cli import main
sys.argv = ['iadepusula', 'search', 'MSY Madde 15/1-ç']
with contextlib.redirect_stdout(io.StringIO()) as output:
    main()
assert [item['parca']['chunk_id'] for item in json.loads(output.getvalue())] == ['MSY-M15-ç']
print('Wheel verified outside checkout: CLI, orders, corpus, threshold, evaluation and retrieval benchmark.')
assert AgentLimits().max_model_calls == 2
assert Path(maliyet_hesapla.__file__).resolve().is_relative_to(installed_root)
print('Member 2 modules and cost entrypoint verified without credentials or API requests.')
"""


def verify(wheel: Path):
    with tempfile.TemporaryDirectory(prefix="iadepusula-package-") as temporary:
        destination = Path(temporary).resolve()
        installed = destination / "installed"
        installed.mkdir()
        with zipfile.ZipFile(wheel) as package:
            for name in package.namelist():
                target = (installed / name).resolve()
                if not target.is_relative_to(installed):
                    raise ValueError("Paket yolu kurulum dizininin dışına çıkıyor")
            package.extractall(installed)
        result = subprocess.run(
            [sys.executable, "-I", "-c", PROBE, str(installed)],
            cwd=destination,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
        )
        if result.returncode:
            print(result.stderr)
            raise SystemExit(result.returncode)
        print(result.stdout.strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    artifact = parser.parse_args().wheel.resolve()
    if artifact.is_dir():
        wheels = list(artifact.glob("iadepusula-*.whl"))
        if len(wheels) != 1:
            parser.error("Paket dizininde tam bir İadePusula wheel dosyası bulunmalıdır")
        artifact = wheels[0]
    verify(artifact)
