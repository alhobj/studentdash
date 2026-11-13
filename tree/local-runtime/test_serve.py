import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('local_serve',Path(__file__).with_name('serve.py'))
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'app/assets').mkdir(parents=True);(self.root/'app/index.html').write_text('viewer')
        (self.root/'assets-manifest.json').write_text(json.dumps(['assets/app.js']))
        (self.root/'results.json').write_text('{"evidence":[]}');(self.root/'master.xlsx').write_text('PRIVATE')
    def request(self,path,**headers):
        cls=server.handler(self.root);h=object.__new__(cls);h.path=path;h.headers={'Host':'127.0.0.1:8765',**headers};h.wfile=io.BytesIO();h.response_headers={}
        h.send_response=lambda n:setattr(h,'status',n);h.send_error=lambda n,*args:setattr(h,'status',n)
        h.send_header=lambda k,v:h.response_headers.update({k:v});h.end_headers=lambda:None
        h.reply(False);return h
    def test_exact_allowlist_and_headers(self):
        h=self.request('/results.json');self.assertEqual(h.status,200);self.assertEqual(h.response_headers['Cache-Control'],'no-store')
        self.assertIn("connect-src 'self'",h.response_headers['Content-Security-Policy'])
        for path in ['/master.xlsx','/','/../master.xlsx','/%2e%2e/master.xlsx','/serve.py']:self.assertEqual(self.request(path).status,200 if path=='/' else 404)
        for headers in [{'Host':'evil.example'},{'Origin':'https://evil.example'},{'Sec-Fetch-Site':'cross-site'}]:self.assertEqual(self.request('/results.json',**headers).status,403)
    def test_missing_or_large_file(self):
        (self.root/'results.json').unlink();self.assertEqual(self.request('/results.json').status,503)
        (self.root/'results.json').write_bytes(b' '*(2*1024*1024+1));self.assertEqual(self.request('/results.json').status,503)
        self.assertEqual(self.request('/').status,200)
    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            target=Path(outside)/'results.json';target.write_text('private');(self.root/'results.json').unlink();(self.root/'results.json').symlink_to(target)
            self.assertEqual(self.request('/results.json').status,503)
if __name__=='__main__':unittest.main()
