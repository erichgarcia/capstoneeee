# Silent kiosk printing (Windows / Xprinter XP-58IIB USB)

The existing Laravel ticket generator saves the queue ticket, then signs its existing ESC/POS receipt. The kiosk sends that receipt to http://127.0.0.1:9123/print, waits up to six seconds for the result, displays ticket information, and keeps its existing 30-second idle reset. There is no browser print call, Print/Reprint button, preview, or print modal.

## One-time setup on the kiosk PC

1. Install the Xprinter Windows USB driver and make sure a Windows test page prints. Find the exact printer name in Windows Settings > Printers & scanners.
2. Install Python 3, then from this directory run:

   python -m pip install -r requirements.txt
   python service.py --initialize

3. Edit **printer_name** in **config.json** to the exact Windows printer name (default XP-58IIB). This is the single printer setting. The generated secret must remain private; config.json is ignored by Git.
4. Add your exact kiosk website origin to **allowed_origins** if it differs from the included localhost development origins. Origins include scheme and port, with no trailing slash.
5. Run the normal frontend **npm run dev** launcher. On Windows it initializes and starts the service automatically alongside Laravel and Vite. Set KIOSK_PYTHON if Python has a nonstandard executable path. Printer service failure does not stop the queue system.

For a separately hosted Laravel backend, set **KIOSK_PRINT_SECRET** in the backend .env to the same secret in config.json, then run **php artisan config:clear** (or rebuild config cache). For a backend beside this service, Laravel reads the local config.json automatically. The secret is never sent to the browser.

For a production launcher, run **start-hidden.ps1** on the kiosk PC, or add a Windows Task Scheduler task at user logon that runs:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\path\to\kiosk-print-service\start-hidden.ps1"

Use the kiosk Windows user account that has access to the printer and write access to this directory. Run one service instance. Do not also install a logon task if the regular launcher starts the service. Check http://127.0.0.1:9123/health to confirm it is running. For a remotely hosted site, the browser may require a one-time local-network access permission configured by the kiosk administrator; test it before unattended use. No customer print interaction is involved.

## Duplicate and failure behavior

SQLite print-jobs.sqlite3 commits a unique ticket ID + creation timestamp claim BEFORE sending bytes. Repeated HTTP requests, re-renders, browser refreshes, concurrent calls, and service restarts cannot submit a second spool job for that receipt. There are no automatic print retries. Signed receipts prevent the frontend from inventing a print job for an unsaved ticket. The server no longer prints separately.

The response status **spooled** means Windows accepted the RAW ESC/POS job, not proof that paper exited. USB drivers may report offline or paper errors late. Immediate reported printer errors are returned to the kiosk and recorded in SQLite and print-service.log. The kiosk shows a small message asking the customer to note their queue number; technical details appear in its tooltip and browser console. Ticket creation remains successful and its database row is retained.

Failed and uncertain jobs remain claimed to prevent a partial or delayed print from being duplicated. After any timeout/crash, staff must inspect the physical printer and Windows spooler. Do not delete the SQLite ledger during ordinary startup, deployment, or recovery. If staff decide to reprint manually, first cancel any queued spool job and verify no paper was produced; there is intentionally no customer reprint button.

The service uses Windows OpenPrinter / StartDocPrinter with RAW data / WritePrinter, retaining the existing receipt fields and ESC/POS layout. See Microsoft's API example: https://learn.microsoft.com/en-us/windows/win32/printdocs/sending-data-directly-to-a-printer

## Validation

python -m unittest discover -s tests -v

Physical USB printing must be validated on the configured kiosk printer after setup.
