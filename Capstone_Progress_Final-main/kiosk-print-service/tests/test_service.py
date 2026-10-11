from contextlib import closing
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service import PrintService

class PrintingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = {'secret': 'x' * 64, 'printer_name': 'Test'}
        self.db = Path(self.tmp.name) / 'jobs.sqlite3'
        self.calls = []
        def printer(name, data, ticket_id):
            self.calls.append((name, data, ticket_id))
            return 101
        self.printer = printer
        self.service = PrintService(self.config, self.db, printer)
        payload = base64.b64encode(json.dumps({'ticket_id': '42', 'created_at': '2026-10-09T08:00:00+08:00',
            'escpos': base64.b64encode(b'LYCEUM OF ALABANG').decode()}).encode()).decode()
        self.envelope = {'payload': payload, 'signature': hmac.new(self.config['secret'].encode(), payload.encode(), hashlib.sha256).hexdigest()}

    def test_concurrent_duplicate_requests_print_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(self.service.print_job, [self.envelope] * 20))
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(all(r['success'] for r in results))
        self.assertEqual(sum(r.get('duplicate', False) for r in results), 19)

    def test_restart_and_browser_replay_do_not_reprint(self):
        self.service.print_job(self.envelope)
        restarted = PrintService(self.config, self.db, self.printer)
        self.assertTrue(restarted.print_job(self.envelope)['duplicate'])
        self.assertEqual(len(self.calls), 1)

    def test_failed_or_partially_sent_job_is_never_retried(self):
        def failed(*args):
            self.calls.append(args)
            raise OSError('Printer offline')
        service = PrintService(self.config, self.db, failed)
        self.assertFalse(service.print_job(self.envelope)['success'])
        restarted = PrintService(self.config, self.db, self.printer)
        result = restarted.print_job(self.envelope)
        self.assertFalse(result['success'])
        self.assertTrue(result['duplicate'])
        self.assertEqual(len(self.calls), 1)

    def test_unsigned_or_modified_ticket_cannot_print(self):
        with self.assertRaises(ValueError):
            self.service.print_job(dict(self.envelope, signature='bad'))
        self.assertEqual(self.calls, [])

    def test_crash_after_claim_does_not_print_again(self):
        import sqlite3
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('INSERT INTO jobs(ticket_key,status,result) VALUES (?,?,?)',
                ('42:2026-10-09T08:00:00+08:00', 'printing', '{}'))
        restarted = PrintService(self.config, self.db, self.printer)
        result = restarted.print_job(self.envelope)
        self.assertEqual(result['status'], 'uncertain')
        self.assertFalse(result['success'])
        self.assertEqual(self.calls, [])

if __name__ == '__main__':
    unittest.main()
