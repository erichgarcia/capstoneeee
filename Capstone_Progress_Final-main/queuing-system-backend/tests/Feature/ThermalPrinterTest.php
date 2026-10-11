<?php

namespace Tests\Feature;

use App\Models\DisplaySetting;
use App\Models\QueueTicket;
use App\Services\ThermalPrinterService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ThermalPrinterTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        DisplaySetting::create([
            'settings' => [
                'enabledDepartments' => ['Cashier', 'Registrar', 'ITM', 'Admission'],
            ],
        ]);
    }

    public function test_department_labels_match_requirements(): void
    {
        $cashierTicket = new QueueTicket(['service_type' => 'C']);
        $this->assertSame('CASHIER', ThermalPrinterService::getDepartmentLabel($cashierTicket));

        $registrarTicket = new QueueTicket(['service_type' => 'R']);
        $this->assertSame('REGISTRAR', ThermalPrinterService::getDepartmentLabel($registrarTicket));

        $itmTicket = new QueueTicket(['service_type' => 'ITM']);
        $this->assertSame('ITM', ThermalPrinterService::getDepartmentLabel($itmTicket));

        $admTicket = new QueueTicket(['service_type' => 'ADM']);
        $this->assertSame('ADMISSION', ThermalPrinterService::getDepartmentLabel($admTicket));
    }

    public function test_escpos_stream_contains_required_fields_and_cut(): void
    {
        $escpos = ThermalPrinterService::buildEscPos('CASHIER', 'C-R001', '10/05/2026');

        $this->assertStringContainsString('LYCEUM OF ALABANG', $escpos);
        $this->assertStringContainsString('CASHIER', $escpos);
        $this->assertStringContainsString('QUEUE NUMBER', $escpos);
        $this->assertStringContainsString('C-R001', $escpos);
        $this->assertStringContainsString('Date: 10/05/2026', $escpos);

        // Auto-cut command: GS V 65 0 (\x1DV\x41\x00)
        $this->assertStringContainsString("\x1DV\x41\x00", $escpos);
    }

    public function test_printing_failure_does_not_break_ticket_generation(): void
    {
        $response = $this->postJson('/api/queue/generate', [
            'service_type' => 'C',
            'student_number' => 'Guest',
            'priority_type' => 'R',
            'transaction_type' => 'Payment',
        ]);

        $response->assertStatus(201);
        $response->assertJsonStructure([
            'message',
            'ticket' => ['ticket_id', 'ticket_number', 'service_type'],
            'print',
        ]);

        $this->assertNotEmpty($response->json('ticket.ticket_number'));
        $this->assertFalse($response->json('print.success'));
    }
    public function test_saved_ticket_receipt_is_signed_and_preserves_layout(): void
    {
        config(['kiosk_print.secret' => str_repeat('x', 64)]);
        $response = $this->postJson('/api/queue/generate', [
            'service_type' => 'C', 'student_number' => 'Guest',
            'priority_type' => 'R', 'transaction_type' => 'Payment',
        ]);
        $response->assertCreated();
        $job = $response->json('print.job');
        $this->assertSame(hash_hmac('sha256', $job['payload'], str_repeat('x', 64)), $job['signature']);
        $receipt = json_decode(base64_decode($job['payload']), true);
        $this->assertDatabaseHas('queue_tickets', ['ticket_id' => $receipt['ticket_id']]);
        $this->assertStringContainsString($response->json('ticket.ticket_number'), base64_decode($receipt['escpos']));
        $this->assertSame('local_service', $response->json('print.method'));
    }

    public function test_failed_ticket_creation_has_no_print_receipt(): void
    {
        config(['kiosk_print.secret' => str_repeat('x', 64)]);
        $response = $this->postJson('/api/queue/generate', ['service_type' => 'invalid']);
        $response->assertUnprocessable();
        $this->assertNull($response->json('print.job'));
        $this->assertDatabaseCount('queue_tickets', 0);
    }
}
