# Start the kiosk on the main Windows PC

Double-click **Start Kiosk.vbs** in the outer project folder. It starts XAMPP MySQL when needed, starts the existing React/Laravel/printer launcher hidden, checks database and frontend readiness, and opens the kiosk in your default browser. No build or terminal command is needed for daily startup. Press F11 in the browser for full screen.

PHP, Node, Python, the frontend dependencies, Composer dependencies, backend .env/database, and printer configuration must already be installed on the PC. This launcher uses the existing development servers for the prototype. Closing the browser leaves the services running; opening the launcher again reuses the ready system. Restarting Windows stops these processes.

Startup logs are in `.kiosk-launcher`. Printer-specific logs remain in `kiosk-print-service`. Printer failure does not prevent the kiosk from opening; validate physical printing before your demonstration.

To start automatically at Windows login, press Win+R, enter `shell:startup`, and place a **shortcut** to Start Kiosk.vbs in that folder. Keep the original launcher with the project. Remove the shortcut to disable automatic startup. Do not configure a second printer startup task because the existing launcher starts it.

This is the local main-PC prototype. A multi-device pilot needs a configured web server, network addresses, and service management.
