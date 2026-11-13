"""Curriculum-only links for a separately configured report exporter.

This module reads public curriculum data and constructs strings. It has no network,
student/result inputs, progress storage, or connection to a Studentdash workflow.
"""

from collections.abc import Collection, Mapping
from html import escape
from ipaddress import IPv4Address, IPv6Address
import json
from pathlib import Path
import re
from types import MappingProxyType
from unicodedata import category
from urllib.parse import quote, unquote, urlsplit, urlunsplit


MAP_VERSION = "2.0"
DEFAULT_MAP_PATH = Path(__file__).resolve().parents[1] / "src" / "data" / "map.json"
_NODE_ID = re.compile(r"ib-2025-(?:structure|reactivity)-[1-9]\d*\.[1-9]\d*\.[1-9]\d*\Z")
_HOST_LABEL = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\Z")
_BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
_ENCODED_SEPARATOR = re.compile(r"%(?:2f|5c)", re.IGNORECASE)
_BASE_ERROR = (
    "Use a generic HTTP(S) Chemistree base URL with a valid host and port, "
    "without credentials, query, fragment, control characters or ambiguous path syntax."
)


def _has_controls(value: str) -> bool:
    return any(category(character) in {"Cc", "Cf", "Cs"} for character in value)


def load_node_titles(map_path: str | Path = DEFAULT_MAP_PATH) -> Mapping[str, str]:
    """Load the reviewed, local map-2.0 ID/title registry; never fetch a URL.

    Copy the public map alongside this helper if a future exporter runs elsewhere.
    Unknown versions, duplicate IDs and malformed ID/title entries fail as a whole.
    """
    try:
        with Path(map_path).open(encoding="utf-8") as source:
            data = json.load(source)
    except (OSError, TypeError, ValueError):
        raise ValueError("Could not read the local public Chemistree curriculum registry.") from None
    if not isinstance(data, dict) or data.get("version") != MAP_VERSION:
        raise ValueError("Use the reviewed Chemistree map version 2.0 curriculum registry.")
    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("The public curriculum registry must contain curriculum nodes.")
    titles: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("The public curriculum registry contains an invalid node.")
        node_id, title = node.get("id"), node.get("title")
        if (
            not isinstance(node_id, str)
            or not _NODE_ID.fullmatch(node_id)
            or node_id in titles
            or not isinstance(title, str)
            or not title.strip()
            or _has_controls(title)
        ):
            raise ValueError("The public curriculum registry has an invalid or duplicate ID/title.")
        titles[node_id] = title
    return MappingProxyType(titles)


def load_node_ids(map_path: str | Path = DEFAULT_MAP_PATH) -> frozenset[str]:
    """Load only the known public node IDs from the same local registry."""
    return frozenset(load_node_titles(map_path))


def _base_parts(base_url: str) -> tuple[str, str, str]:
    # urlsplit strips some controls and leading spaces. Reject those before parsing.
    if (
        not isinstance(base_url, str)
        or not base_url
        or base_url[0].isspace()
        or _has_controls(base_url)
        or any(character in base_url for character in "\\?#")
    ):
        raise ValueError(_BASE_ERROR)
    try:
        base = urlsplit(base_url)
        host, port = base.hostname, base.port
    except ValueError:
        raise ValueError(_BASE_ERROR) from None
    if (
        base.scheme not in {"http", "https"}
        or not host
        or not base.netloc
        or base.username is not None
        or base.password is not None
        or any(character.isspace() for character in base.netloc)
        or "%" in base.netloc
    ):
        raise ValueError(_BASE_ERROR)

    # Validate the authority as browsers use it: no empty, signed or nondecimal port;
    # bracketed IPv6, strict dotted IPv4, or ASCII DNS labels (IDNA may be configured).
    if base.netloc.startswith("["):
        authority = re.fullmatch(r"\[([^\]]+)\](?::([0-9]+))?", base.netloc)
        try:
            if authority is None:
                raise ValueError
            IPv6Address(host)
        except ValueError:
            raise ValueError(_BASE_ERROR) from None
    else:
        authority = re.fullmatch(r"([^:]+)(?::([0-9]+))?", base.netloc)
        labels = host.split(".")
        if authority is None or len(host) > 253 or not all(_HOST_LABEL.fullmatch(label) for label in labels):
            raise ValueError(_BASE_ERROR)
        # Browsers also interpret a final hexadecimal label as an IPv4 number.
        # Accept IP hosts only in unambiguous dotted-decimal form.
        if re.fullmatch(r"(?:[0-9]+|0[xX][0-9a-fA-F]*)", labels[-1]):
            try:
                IPv4Address(host)
            except ValueError:
                raise ValueError(_BASE_ERROR) from None
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(_BASE_ERROR)

    path = base.path
    if _BAD_PERCENT.search(path) or _ENCODED_SEPARATOR.search(path):
        raise ValueError(_BASE_ERROR)
    try:
        decoded_path = unquote(path, encoding="utf-8", errors="strict")
    except UnicodeError:
        raise ValueError(_BASE_ERROR) from None
    if _has_controls(decoded_path) or any(segment in {".", ".."} for segment in decoded_path.split("/")):
        raise ValueError(_BASE_ERROR)
    # Preserve an existing subpath and valid escapes; encode spaces/non-ASCII locally.
    encoded_path = quote(path, safe="/%:@!$&'()*+,;=-._~")
    return base.scheme, base.netloc, encoded_path


def node_url(base_url: str, node_id: str, known_ids: Collection[str]) -> str:
    """Return a public curriculum-only URL after validating its complete inputs.

    Configure base_url once, outside report rows. known_ids must come from a reviewed
    public curriculum registry; no identity, score, status or assessment input is accepted.
    """
    scheme, authority, path = _base_parts(base_url)
    if not isinstance(known_ids, Collection) or isinstance(known_ids, (str, bytes)):
        raise ValueError("Supply known IDs from the reviewed public curriculum registry.")
    if not isinstance(node_id, str) or not _NODE_ID.fullmatch(node_id) or node_id not in known_ids:
        raise ValueError("Unknown Chemistree curriculum node ID; review the objective mapping.")
    return urlunsplit((scheme, authority, path, "", "node=" + quote(node_id, safe="")))


def node_anchor(base_url: str, node_id: str, node_titles: Mapping[str, str]) -> str:
    """Return escaped, referrer-suppressed HTML labelled with the public curriculum title."""
    if not isinstance(node_titles, Mapping):
        raise ValueError("Supply titles from the reviewed public curriculum registry.")
    destination = node_url(base_url, node_id, node_titles)
    title = node_titles[node_id]
    if not isinstance(title, str) or not title.strip() or _has_controls(title):
        raise ValueError("The public curriculum title must be nonempty text without control characters.")
    return f'<a href="{escape(destination, quote=True)}" referrerpolicy="no-referrer">{escape(title, quote=True)}</a>'
