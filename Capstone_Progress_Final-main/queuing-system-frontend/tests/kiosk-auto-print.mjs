import assert from 'node:assert/strict'
import { build } from 'esbuild'
import React from 'react'
import Renderer, { act } from 'react-test-renderer'
import { MemoryRouter } from 'react-router-dom'
await build({ entryPoints: ['src/pages/Kiosk.jsx'], outfile: 'tests/.compiled/KioskAutoPrint.js', bundle: true,
  format: 'esm', platform: 'node', jsx: 'automatic', packages: 'external', plugins: [{ name: 'api-fixture', setup(b) {
    b.onResolve({ filter: /\/api$/ }, () => ({ path: 'api', namespace: 'mock' }))
    b.onLoad({ filter: /.*/, namespace: 'mock' }, () => ({ contents: ['generateTicket', 'verifySecurityCode', 'getWindowAvailability', 'getDisplayConfiguration', 'getStudent']
      .map(n => 'export const ' + n + '=(...args)=>globalThis.testApi.' + n + '(...args);').join('\n') }))
  } }] })
const Kiosk = (await import('./.compiled/KioskAutoPrint.js')).default
let creates = 0, prints = 0, resolveCreation, resolvePrint, resetTimeout
const originalTimeout = globalThis.setTimeout
Object.assign(globalThis, {
  window: Object.assign(new EventTarget(), { print() { assert.fail('Browser printing forbidden') }, open() { assert.fail('Popup forbidden') } }),
  setTimeout(fn, ms, ...args) { if (ms === 30000) resetTimeout = fn; return originalTimeout(fn, ms, ...args) },
  testApi: {
    getDisplayConfiguration: async () => ({ settings: { enabledDepartments: ['Cashier', 'Registrar', 'ITM', 'Admission'] } }),
    getWindowAvailability: async () => [],
    generateTicket: () => { creates++; return new Promise(r => resolveCreation = r) },
  },
  fetch: async (url, options) => { assert.equal(url, 'http://127.0.0.1:9123/print'); assert.equal(options.method, 'POST'); prints++;
    return new Promise(r => resolvePrint = r) },
})
const flush = fn => act(async () => { await fn?.(); await Promise.resolve() })
let tree
const ui = () => React.createElement(MemoryRouter, { future: { v7_startTransition: true, v7_relativeSplatPath: true } }, React.createElement(Kiosk))
const mount = () => flush(() => { tree = Renderer.create(ui()) })
const find = cls => tree.root.findAllByType('button').find(b => b.props.className?.includes(cls))
const enterPayment = async () => {
  await flush(() => tree.root.findByProps({ className: 'kiosk-splash' }).props.onClick())
  await flush(() => find('student-guest-btn').props.onClick())
  await flush(() => find('service-cashier').props.onClick())
  await flush(() => find('priority-regular').props.onClick())
}
await mount(); await enterPayment()
const click = find('kiosk-transaction-card').props.onClick
let pending
await flush(() => { pending = click(); click() })
assert.equal(creates, 1, 'double click creates only one request')
assert.equal(prints, 0, 'printing waits for database success')
await flush(() => resolveCreation({ ticket_id: 42, ticket_number: 'C-R001', service_type: 'C', created_at: '2026-10-09T08:00:00Z', print: { job: { payload: 'signed-test-receipt', signature: 'test' } } }))
assert.equal(prints, 1, 'successful generation automatically dispatches print')
await flush(async () => { resolvePrint({ ok: true, json: async () => ({ success: true, status: 'spooled' }) }); await pending })
assert.equal(tree.root.findAllByProps({ className: 'kiosk-ticket-num-big' }).length, 1)
assert.equal(find('print-ticket-btn'), undefined, 'no print/reprint button')
assert.equal(tree.root.findAllByProps({ role: 'dialog' }).length, 0)
await flush(() => tree.update(ui()))
assert.equal(prints, 1, 'rendering does not print again')
await flush(() => resetTimeout())
assert.equal(tree.root.findAllByProps({ className: 'kiosk-splash' }).length, 1, 'normal idle reset preserved')
await flush(() => tree.unmount())
await mount(); await enterPayment()
testApi.generateTicket = async () => { throw new Error('Database unavailable') }
await flush(() => find('kiosk-transaction-card').props.onClick())
assert.equal(prints, 1, 'failed generation never prints')
assert.equal(tree.root.findAllByProps({ className: 'kiosk-ticket-num-big' }).length, 0)
await flush(() => tree.unmount())
globalThis.setTimeout = originalTimeout
console.log('PASS automatic saved-ticket printing, no popup/button, double clicks, re-render, creation failure, and idle reset')

// Guest Registrar: selecting a window submits directly, with no Continue step.
testApi.generateTicket = request => { creates++; globalThis.lastRegistrarRequest = request; return new Promise(r => resolveCreation = r) }
await mount()
await flush(() => tree.root.findByProps({ className: 'kiosk-splash' }).props.onClick())
await flush(() => find('student-guest-btn').props.onClick())
await flush(() => find('service-registrar').props.onClick())
await flush(() => find('priority-regular').props.onClick())
await flush(() => find('kiosk-transaction-card').props.onClick())
assert.equal(tree.root.findAllByType('button').some(b => b.children.includes('Continue')), false)
const windowClick = find('kiosk-window-card').props.onClick
const before = creates
await flush(() => { pending = windowClick(); windowClick() })
assert.equal(creates, before + 1, 'window double click submits only once')
assert.equal(lastRegistrarRequest.window, 9)
assert.equal(lastRegistrarRequest.transaction_type, 'Document Request')
await flush(() => resolveCreation({ ticket_id: 43, ticket_number: 'R-R001', service_type: 'R', window: 9, created_at: '2026-10-09T08:00:01Z', print: { job: { payload: 'registrar-receipt', signature: 'test' } } }))
await flush(async () => { resolvePrint({ ok: true, json: async () => ({ success: true }) }); await pending })
assert.equal(tree.root.findAllByProps({ className: 'kiosk-ticket-num-big' }).length, 1)
await flush(() => tree.unmount())
console.log('PASS Registrar window selection automatically creates and prints one ticket without Continue')
