"""Public curriculum link contract; all URLs and synthetic records are fictional."""

from html.parser import HTMLParser
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from integration.chemistree_links import load_node_ids, load_node_titles, node_anchor, node_url


BASE_URL = "https://chemistry.example.edu/chemistree/"
NODE_ID = "ib-2025-structure-2.2.6"
ROOT = Path(__file__).resolve().parents[2]


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class RegistryTests(unittest.TestCase):
    def test_all_165_reviewed_map_ids_can_be_linked(self):
        curriculum = load_node_titles(ROOT / "src/data/map.json")
        self.assertEqual(len(curriculum), 165)
        self.assertEqual(load_node_ids(), frozenset(curriculum))
        for node_id in curriculum:
            with self.subTest(node=node_id):
                url = node_url(BASE_URL, node_id, curriculum)
                parts = urlsplit(url)
                self.assertEqual(parts.scheme, "https")
                self.assertEqual(parts.netloc, "chemistry.example.edu")
                self.assertEqual(parts.path, "/chemistree/")
                self.assertEqual(parts.query, "")
                self.assertEqual(parse_qs(parts.fragment, strict_parsing=True), {"node": [node_id]})

    def test_registry_is_immutable(self):
        with self.assertRaises(TypeError):
            load_node_titles()[NODE_ID] = "Changed objective"

    def test_incompatible_or_malformed_registry_is_rejected_as_a_whole(self):
        good = {"id": NODE_ID, "title": "Molecular polarity"}
        cases = [
            {"version": "1.0", "nodes": [good]},
            {"version": "2.0", "nodes": []},
            {"version": "2.0", "nodes": [good, good]},
            {"version": "2.0", "nodes": [good, {"id": "ct-old", "title": "Old map"}]},
            {"version": "2.0", "nodes": [good, {"id": "ib-2025-structure-1.1.1", "title": ""}]},
            {"version": "2.0", "nodes": [None]},
            {"version": "2.0", "nodes": [{"id": NODE_ID, "title": "Title\ncontrol"}]},
            [],
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "public-map.json"
            for data in cases:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_node_titles(path)
            path.write_text("not JSON", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Could not read"):
                load_node_titles(path)
            with self.assertRaisesRegex(ValueError, "Could not read"):
                load_node_titles(Path(directory) / "not-present.json")


class LinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum = load_node_titles()

    def test_subpaths_and_valid_existing_escapes_are_preserved(self):
        bases = {
            "https://chemistry.example.edu/school chemistry/": "https://chemistry.example.edu/school%20chemistry/",
            "https://chemistry.example.edu/school%20chemistry/": "https://chemistry.example.edu/school%20chemistry/",
            "https://chemistry.example.edu/kjemi/øving/": "https://chemistry.example.edu/kjemi/%C3%B8ving/",
            "http://localhost:4173/chemistree/": "http://localhost:4173/chemistree/",
            "https://127.0.0.1:8443/app/": "https://127.0.0.1:8443/app/",
            "http://[::1]:4173/app/": "http://[::1]:4173/app/",
            "https://chemistry.example.edu": "https://chemistry.example.edu",
        }
        for base, expected in bases.items():
            with self.subTest(base=base):
                self.assertEqual(node_url(base, NODE_ID, self.curriculum), expected + "#node=" + NODE_ID)

    def test_invalid_or_ambiguous_base_urls_are_rejected(self):
        bases = [
            "", "chemistry.example.edu/", "//chemistry.example.edu/", "ftp://chemistry.example.edu/",
            "https:///app/", "https://", " https://chemistry.example.edu/",
            "https://fictional-user:fictional-secret@chemistry.example.edu/",
            "https://chemistry.example.edu/?student=fictional-learner",
            "https://chemistry.example.edu/?", "https://chemistry.example.edu/#",
            "https://chemistry.example.edu/#node=" + NODE_ID,
            "https://chemistry.example.edu:/", "https://chemistry.example.edu:+443/",
            "https://chemistry.example.edu:0/", "https://chemistry.example.edu:65536/",
            "https://chemistry.example.edu:not-a-port/", "https://bad_host.example/",
            "https://-host.example/", "https://host..example/", "https://host.example./",
            "https://127.1/", "https://2130706433/", "https://0x7f000001/", "https://school.0x1/",
            "https://[not-ipv6]/",
            "https://[::1]junk/", "https://[::1]:/", "https://host%2eexample/",
            "https://host.example\\@other.example/", "https://host.example/../app/",
            "https://host.example/%2e%2e/app/", "https://host.example/app%2fextra/",
            "https://host.example/app%5cextra/", "https://host.example/bad%/",
            "https://host.example/bad%ff/", "https://host.example/%00/", "https://host.example/%0a/",
            "https://host.example/\napp/", "https://host.example/\tapp/", "https://host.example/\x7f/",
            "https://host.example/\u202eapp/", "https://bad host.example/",
            None, 42,
        ]
        for base in bases:
            with self.subTest(base=base):
                with self.assertRaisesRegex(ValueError, "generic HTTP\\(S\\)"):
                    node_url(base, NODE_ID, self.curriculum)

    def test_errors_do_not_repeat_potential_credentials_or_private_url_values(self):
        for base in [
            "https://fictional-secret@chemistry.example.edu/",
            "https://chemistry.example.edu/?student=fictional-secret",
            "https://chemistry.example.edu:fictional-secret/",
        ]:
            with self.subTest(base=base):
                try:
                    node_url(base, NODE_ID, self.curriculum)
                except ValueError as error:
                    self.assertNotIn("fictional-secret", str(error))
                    self.assertIsNone(error.__cause__)
                else:
                    self.fail("Invalid URL was accepted")

    def test_unknown_ids_and_malformed_ids_are_not_linked(self):
        invalid_ids = [
            "ib-2025-structure-9.9.9", "ct-old", "", None, 42,
            NODE_ID + "&student=fictional-learner", NODE_ID + "#status=confident",
        ]
        for node_id in invalid_ids:
            with self.subTest(node=node_id):
                with self.assertRaisesRegex(ValueError, "Unknown Chemistree curriculum node"):
                    node_url(BASE_URL, node_id, self.curriculum)
        # Even a caller-supplied registry cannot authorise fragment injection.
        with self.assertRaises(ValueError):
            node_url(BASE_URL, NODE_ID + "&score=4", {NODE_ID + "&score=4"})

    def test_registry_argument_cannot_be_a_string_or_missing_collection(self):
        for registry in [NODE_ID, NODE_ID.encode(), None, 42]:
            with self.subTest(registry=registry):
                with self.assertRaisesRegex(ValueError, "known IDs"):
                    node_url(BASE_URL, NODE_ID, registry)

    def test_api_has_no_report_fields_and_does_not_mutate_its_registry(self):
        self.assertEqual(list(inspect.signature(node_url).parameters), ["base_url", "node_id", "known_ids"])
        self.assertEqual(list(inspect.signature(node_anchor).parameters), ["base_url", "node_id", "node_titles"])
        registry = {NODE_ID: self.curriculum[NODE_ID]}
        before = registry.copy()
        node_url(BASE_URL, NODE_ID, registry)
        node_anchor(BASE_URL, NODE_ID, registry)
        self.assertEqual(registry, before)
        with self.assertRaises(TypeError):
            node_url(BASE_URL, NODE_ID, registry, student="fictional-learner")

    def test_html_anchor_escapes_public_title_and_url_without_inserting_markup(self):
        title = 'Model <A> & "B" \'C\''
        base = "https://chemistry.example.edu/chemistry&'study/"
        anchor = node_anchor(base, NODE_ID, {NODE_ID: title})
        self.assertIn("&amp;", anchor)
        self.assertIn("&#x27;", anchor)
        self.assertIn("&lt;A&gt;", anchor)
        self.assertNotIn("<A>", anchor)
        parser = AnchorParser()
        parser.feed(anchor)
        self.assertEqual(parser.elements, [("a", {"href": node_url(base, NODE_ID, {NODE_ID}), "referrerpolicy": "no-referrer"})])
        self.assertEqual("".join(parser.text), title)

    def test_report_anchor_suppresses_source_report_referrer(self):
        parser = AnchorParser()
        parser.feed(node_anchor(BASE_URL, NODE_ID, self.curriculum))
        self.assertEqual(parser.elements[0][1]["referrerpolicy"], "no-referrer")
        self.assertEqual(urlsplit(parser.elements[0][1]["href"]).query, "")

    def test_anchor_uses_loaded_curriculum_title_and_rejects_invalid_titles(self):
        parser = AnchorParser()
        parser.feed(node_anchor(BASE_URL, NODE_ID, self.curriculum))
        self.assertEqual("".join(parser.text), self.curriculum[NODE_ID])
        for titles in [{NODE_ID: ""}, {NODE_ID: None}, {NODE_ID: "Title\ncontrol"}, {NODE_ID}]:
            with self.subTest(titles=titles):
                with self.assertRaises(ValueError):
                    node_anchor(BASE_URL, NODE_ID, titles)


if __name__ == "__main__":
    unittest.main()
