from contextlib import closing
"""Loopback-only silent Windows RAW printing, with durable at-most-once claims."""
import base64
import hashlib
import hmac
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import secrets
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / 'config.json'
DEFAULT_CONFIG = {
    'printer_name': 'XP-58IIB',
    'secret': '',
    'allowed_origins': ['http://localhost:3000', 'http://127.0.0.1:3000',
                        'http://localhost', 'http://127.0.0.1'],
}

def load_config():
    if not CONFIG_PATH.exists():
        config = dict(DEFAULT_CONFIG, secret=secrets.token_hex(32))
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')
    config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    if len(config.get('secret', '')) < 32:
        raise ValueError('Configure a secret of at least 32 characters')
    return config


def windows_print(printer_name, data, ticket_id):
    # pywin32 uses the Windows spooler; no browser, dialog, or preview.
    import win32print
    handle = win32print.OpenPrinter(printer_name)
    started = False
    try:
        info = win32print.GetPrinter(handle, 2)
        # Paused, error, paper jam/out/problem, offline, intervention, unavailable.
        bad_status = 0x1 | 0x2 | 0x8 | 0x10 | 0x40 | 0x80 | 0x1000 | 0x100000 | 0x400000
        if info['Status'] & bad_status or info['Attributes'] & 0x400:
            raise OSError('Printer is offline, paused, out of paper, or needs attention')
        job_id = win32print.StartDocPrinter(handle, 1, ('Queue ticket ' + ticket_id, None, 'RAW'))
        started = True
        win32print.StartPagePrinter(handle)
        written = win32print.WritePrinter(handle, data)
        if written != len(data):
            raise OSError('Incomplete print write; staff must inspect spooler')
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
        started = False
        return job_id
    except Exception:
        if started:
            try:
                win32print.AbortPrinter(handle)
            except Exception:
                logging.exception('Unable to abort incomplete print job')
        raise
    finally:
        win32print.ClosePrinter(handle)


class PrintService:
    def __init__(self, config, database, printer=windows_print):
        self.config, self.database, self.printer = config, str(database), printer
        self.lock = threading.Lock()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs (ticket_key TEXT PRIMARY KEY, status TEXT NOT NULL, result TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)')
            # A crash may occur after the printer accepted bytes. Never re-send.
            db.execute("UPDATE jobs SET status='uncertain', result=? WHERE status='printing'",
                       (json.dumps({'success': False, 'status': 'uncertain', 'error': 'Service stopped during printing; staff must inspect spooler'}),))

    def print_job(self, envelope):
        payload, signature = envelope.get('payload', ''), envelope.get('signature', '')
        if not isinstance(payload, str) or not isinstance(signature, str):
            raise ValueError('Invalid print receipt')
        expected = hmac.new(self.config['secret'].encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError('Invalid backend receipt signature')
        receipt = json.loads(base64.b64decode(payload, validate=True))
        ticket_id, created_at = str(receipt['ticket_id']), str(receipt['created_at'])
        if not ticket_id.isdigit() or not created_at:
            raise ValueError('Invalid ticket identity')
        data = base64.b64decode(receipt['escpos'], validate=True)
        if not data or len(data) > 16384:
            raise ValueError('Invalid receipt size')
        key = ticket_id + ':' + created_at
        # Serializes writes to the physical printer. SQLite UNIQUE also protects
        # claims across processes. Commit BEFORE touching the printer.
        with self.lock:
            with closing(sqlite3.connect(self.database, timeout=10)) as db, db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT result FROM jobs WHERE ticket_key=?', (key,)).fetchone()
                if row:
                    return dict(json.loads(row[0]), duplicate=True)
                pending = {'success': False, 'status': 'printing', 'error': 'Print already claimed; staff must inspect spooler'}
                db.execute('INSERT INTO jobs(ticket_key,status,result) VALUES (?,?,?)', (key, 'printing', json.dumps(pending)))
            try:
                job_id = self.printer(self.config['printer_name'], data, ticket_id)
                result = {'success': True, 'status': 'spooled', 'job_id': job_id}
            except Exception as error:
                logging.exception('Printing failed for ticket %s', ticket_id)
                result = {'success': False, 'status': 'failed', 'error': str(error)}
            with closing(sqlite3.connect(self.database)) as db, db:
                db.execute('UPDATE jobs SET status=?, result=?, updated_at=CURRENT_TIMESTAMP WHERE ticket_key=?',
                           (result['status'], json.dumps(result), key))
            return result


def handler_for(service):
    class Handler(BaseHTTPRequestHandler):
        def permitted(self):
            return self.headers.get('Origin') in service.config['allowed_origins']

        def reply(self, code, result):
            body = b'' if code == 204 else json.dumps(result).encode()
            self.send_response(code)
            if self.permitted():
                self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
                self.send_header('Vary', 'Origin')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Browser timeout does not cancel or repeat the spool job.

        def do_OPTIONS(self):
            self.reply(204 if self.permitted() else 403, {})

        def do_GET(self):
            self.reply(200 if self.path == '/health' else 404,
                       {'status': 'running', 'printer': service.config['printer_name']})

        def do_POST(self):
            if self.path != '/print' or not self.permitted():
                self.reply(403, {'success': False, 'error': 'Origin or endpoint denied'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 32768:
                    raise ValueError('Invalid request length')
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ValueError('JSON required')
                envelope = json.loads(self.rfile.read(length))
                if not isinstance(envelope, dict):
                    raise ValueError('Invalid receipt')
                result = service.print_job(envelope)
                self.reply(200, result)
            except (ValueError, KeyError, TypeError) as error:
                self.reply(400, {'success': False, 'error': str(error)})
            except Exception:
                logging.exception('Local print service request failed')
                self.reply(500, {'success': False, 'error': 'Local service error; see print-service.log'})

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, format, *args):
            logging.info(format, *args)
    return Handler


if __name__ == '__main__':
    import sys
    if '--initialize' in sys.argv:
        load_config()
        sys.exit(0)
    logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(
        HERE / 'print-service.log', maxBytes=1048576, backupCount=3), logging.StreamHandler()])
    config = load_config()
    # Bind first so a second instance cannot alter an active job's status.
    server = ThreadingHTTPServer(('127.0.0.1', 9123), BaseHTTPRequestHandler)
    service = PrintService(config, HERE / 'print-jobs.sqlite3')
    server.RequestHandlerClass = handler_for(service)
    logging.info('Silent print service on 127.0.0.1:9123, printer %s', config['printer_name'])
    server.serve_forever()
