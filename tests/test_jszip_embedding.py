import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- BEGIN LIPOSCOPE_JSZIP -->"
END = "<!-- END LIPOSCOPE_JSZIP -->"


def test_official_jszip_bundle_is_embedded(html_text):
    vendor = (ROOT / "vendor/jszip/jszip.min.js").read_text(encoding="utf-8").strip()
    assert "JSZip v3.10.1" in vendor
    assert hashlib.sha256((ROOT / "vendor/jszip/jszip.min.js").read_bytes()).hexdigest() == "acc7e41455a80765b5fd9c7ee1b8078a6d160bbbca455aeae854de65c947d59e"
    assert "</script>" not in vendor.lower()
    expected = f"{START}\n<script>\n{vendor}\n</script>\n{END}"
    assert html_text.count(START) == html_text.count(END) == 1
    assert expected in html_text


def test_jszip_licence_and_distributed_copies():
    licence = (ROOT / "vendor/jszip/LICENSE.markdown").read_text(encoding="utf-8")
    assert "The MIT License" in licence
    active = (ROOT / "LipoScope.html").read_bytes()
    assert (ROOT / "templates/LipoScope.template.html").read_bytes() == active
    assert (ROOT / "releases/LipoScope_v1.0.0.html").read_bytes() == active
