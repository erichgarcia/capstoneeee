<?php

namespace App\Services;

use App\Models\QueueTicket;
use Illuminate\Support\Facades\Log;

class ThermalPrinterService
{
    /**
     * Resolve the uppercase department label according to requirements:
     * CASHIER (for Cashier / Accounting), REGISTRAR, ITM, ADMISSION
     */
    public static function getDepartmentLabel(QueueTicket $ticket): string
    {
        $dept = Departments::name($ticket->service_type);

        return match ($dept) {
            'Cashier' => 'CASHIER',
            'Registrar' => 'REGISTRAR',
            'ITM' => 'ITM',
            'Admission' => 'ADMISSION',
            default => strtoupper((string) ($dept ?: 'CASHIER')),
        };
    }

    /**
     * Build ESC/POS binary command stream for Xprinter-58IIB thermal printer (58mm paper).
     */
    public static function buildEscPos(string $department, string $ticketNumber, ?string $date = null): string
    {
        $date ??= now()->format('m/d/Y');
        $deptUpper = strtoupper(trim($department));

        $esc = "\x1B";
        $gs = "\x1D";

        $data = '';

        // Initialize printer
        $data .= $esc . "@";

        // Center alignment
        $data .= $esc . "a\x01";

        // Line 1: LYCEUM OF ALABANG (Bold)
        $data .= $esc . "!\x08";
        $data .= "LYCEUM OF ALABANG\n\n";

        // Line 2: [DEPARTMENT] (Bold)
        $data .= $esc . "!\x08";
        $data .= $deptUpper . "\n\n";

        // Line 3: QUEUE NUMBER (Bold)
        $data .= $esc . "!\x08";
        $data .= "QUEUE NUMBER\n\n";

        // Line 4: [Ticket Number] (Double width + Double height + Bold)
        $data .= $gs . "!\x11";
        $data .= $ticketNumber . "\n\n";

        // Line 5: Date: [Date] (Normal text, smaller)
        $data .= $gs . "!\x00";
        $data .= $esc . "!\x00";
        $data .= "Date: " . $date . "\n\n\n\n";

        // Cut Paper: GS V 65 0 (Full cut with feed, for printers with auto-cutter)
        $data .= $gs . "V\x41\x00";

        return $data;
    }

    /** Build a signed receipt only after the database has saved the ticket. */
    public static function printTicket(QueueTicket $ticket): array
    {
        $configPath = base_path('../kiosk-print-service/config.json');
        $local = is_file($configPath) ? json_decode(file_get_contents($configPath), true) : [];
        $secret = config('kiosk_print.secret') ?: ($local['secret'] ?? '');
        if (!$secret) {
            Log::warning('Kiosk print service is not configured', ['ticket_id' => $ticket->ticket_id]);
            return ['success' => false, 'error' => 'Local print service is not configured'];
        }
        $payload = base64_encode(json_encode([
            'ticket_id' => (string) $ticket->ticket_id,
            'created_at' => $ticket->created_at->toIso8601String(),
            'escpos' => base64_encode(self::buildEscPos(
                self::getDepartmentLabel($ticket), (string) $ticket->ticket_number,
                $ticket->created_at->format('m/d/Y')
            )),
        ], JSON_UNESCAPED_SLASHES));
        return [
            'success' => false,
            'method' => 'local_service',
            'job' => ['payload' => $payload, 'signature' => hash_hmac('sha256', $payload, $secret)],
        ];
    }
}
