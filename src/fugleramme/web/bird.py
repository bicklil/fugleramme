"""The page a bird on the kiosk links to: its names, its plate, and what
Wikipedia says about it.

The description is fetched by the browser, not the frame: the frame keeps no
text of its own about a species, and a kiosk viewer is online where a Pi on a
quiet LAN might not be.
"""

from __future__ import annotations

import html
import io
import json
import re
from pathlib import Path
from string import Template
from urllib.parse import quote_plus

import segno

from ..languages import NONE, SCIENTIFIC, STATION, Namer, station_locale
from ..names import origin_of
from . import STATIC_DIR

# Language codes whose Wikipedia goes by another: Bokmål's is no.wikipedia.org.
_WIKIS = {"nb": "no"}


def wiki_language(namer: Namer) -> str:
    """The Wikipedia edition for the frame's primary language, English when it names none."""
    code = station_locale() if namer.primary == STATION else namer.primary
    if code in (SCIENTIFIC, NONE):
        return "en"
    base = code.replace("_", "-").split("-")[0].lower()
    return _WIKIS.get(base, base)


def page(scientific: str, art: Path, namer: Namer, plate_name: str) -> str:
    """`plate_name`: how the admin names the work the artwork was cut from."""
    first, *rest = namer.parts(scientific)
    plate = html.escape(plate_name)
    if url := origin_of(art):
        plate = f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{plate}</a>'
    data = {"scientific": scientific, "wiki": wiki_language(namer)}
    return Template((STATIC_DIR / "bird.html").read_text()).substitute(
        name=html.escape(first),
        also="".join(f'<p class="also">{html.escape(r)}</p>' for r in rest),
        # Unless the frame already names its birds that way.
        sci="" if first == scientific else f'<p class="sci">{html.escape(scientific)}</p>',
        art="/art?name=" + quote_plus(scientific),
        plate=plate,
        # `</` cannot close the script it sits in.
        data=json.dumps(data).replace("</", "<\\/"),
    )


_EBIRD_CODE = re.compile(r"[a-z0-9]{1,16}")


def ebird_qr(code: str) -> bytes | None:
    """A QR code to the eBird page for species `code`, as SVG, or None for a
    string that is not an eBird code - the route must not encode any URL asked of it."""
    if not _EBIRD_CODE.fullmatch(code):
        return None
    out = io.BytesIO()
    segno.make(f"https://ebird.org/species/{code}").save(
        out, kind="svg", scale=4, border=2, dark="#2b2a26", light=None
    )
    return out.getvalue()
