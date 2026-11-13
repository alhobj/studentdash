"""Optional real-browser smoke test, using only fictional files and loopback HTTP."""
from io import BytesIO
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from zipfile import ZipFile

from werkzeug.serving import make_server

from app.teacher import create_app
from test_local_app import workbook

BROWSER = os.environ.get('STUDENTDASH_BROWSER_EXECUTABLE') or shutil.which('chromium')


@unittest.skipUnless(importlib.util.find_spec('playwright') and BROWSER,
                     'Optional browser smoke test needs requirements-dev.txt and STUDENTDASH_BROWSER_EXECUTABLE or system Chromium')
class LocalBrowserTests(unittest.TestCase):
    def test_results_classifications_exports_and_offline_document(self):
        from playwright.sync_api import sync_playwright, expect
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = create_app(root / 'private', root / 'generated')
            server = make_server('127.0.0.1', 0, app)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as runtime:
                    browser = runtime.chromium.launch(executable_path=BROWSER, headless=True)
                    try:
                        page = browser.new_page()
                        errors = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        base = f'http://127.0.0.1:{server.server_port}'
                        page.goto(base)
                        page.get_by_label('ClassID', exact=True).fill('Fictional_Class')
                        page.get_by_label('Grading workbook (.xlsx)').set_input_files(dict(name='fictional.xlsx', mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', buffer=workbook()))
                        page.get_by_role('button', name='Preview workbook', exact=True).click()
                        expect(page.get_by_role('heading', name='Preview results · Fictional_Class')).to_be_visible()
                        page.get_by_role('button', name='Confirm results import', exact=True).click()
                        expect(page.get_by_role('heading', name='Student overview · Fictional_Class')).to_be_visible()
                        expect(page.get_by_text('Missing classifications', exact=True)).to_have_count(2)
                        page.get_by_role('link', name='Import classifications', exact=True).click()
                        csv = b'ClassID,AssessmentID,QuestionID,CommandTerm,Skill\nFictional_Class,2026-09-25,1a,Explain,Chemical reasoning\n'
                        page.get_by_label('Classification file (.xlsx or UTF-8 CSV)').set_input_files(dict(name='classifications.csv', mimeType='text/csv', buffer=csv))
                        page.get_by_role('button', name='Preview classifications', exact=True).click()
                        expect(page.get_by_text('Proposed classifications', exact=True)).to_be_visible()
                        page.get_by_role('button', name='Confirm classification import', exact=True).click()
                        expect(page.get_by_text('Partial classifications', exact=True)).to_have_count(1)
                        page.get_by_role('link', name='Generate dashboards', exact=True).click()
                        page.get_by_role('button', name='Regenerate all student HTML files', exact=True).click()
                        expect(page.get_by_text('Saved dashboards match the current database revision.', exact=True)).to_be_visible()
                        with page.expect_download() as download:
                            page.get_by_role('link', name='Download all dashboards as ZIP (always uses current results)', exact=True).click()
                        with ZipFile(download.value.path()) as archive:
                            html = archive.read('student1001.html').decode('utf-8')
                            self.assertNotIn('Fictional Beta', html)
                        # No network is available to the rendered document: inline HTML/CSS suffices.
                        offline = browser.new_context(offline=True)
                        offline_page = offline.new_page()
                        offline_page.set_content(html)
                        expect(offline_page.get_by_role('heading', name='Fictional Alpha', exact=True)).to_be_visible()
                        expect(offline_page.get_by_role('heading', name='Assessment history', exact=True)).to_be_visible()
                        expect(offline_page.get_by_role('heading', name='CommandTerm', exact=True)).to_be_visible()
                        self.assertNotIn('Fictional Beta', offline_page.locator('body').inner_text())
                        offline_page.set_viewport_size(dict(width=375, height=812))
                        self.assertTrue(offline_page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                        offline.close()
                        self.assertEqual(errors, [])
                    finally:
                        browser.close()
            finally:
                server.shutdown()
                thread.join(5)
                server.server_close()
