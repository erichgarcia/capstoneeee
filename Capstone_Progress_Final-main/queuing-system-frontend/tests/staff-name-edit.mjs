import assert from 'node:assert/strict'
import { build } from 'esbuild'
import { readFileSync } from 'node:fs'
import React from 'react'
import Renderer, { act } from 'react-test-renderer'
import { MemoryRouter } from 'react-router-dom'
const names = [...readFileSync('src/api.js', 'utf8').matchAll(/export async function (\w+)/g)].map(m => m[1])
await build({ entryPoints: ['src/pages/AdminPanel.jsx'], outfile: 'tests/.compiled/StaffNameEdit.js', bundle: true, format: 'esm', platform: 'node', jsx: 'automatic', packages: 'external', plugins: [{ name: 'admin-fixture', setup(b) {
  b.onResolve({ filter: /\/api$/ }, () => ({ path: 'api', namespace: 'api' }))
  b.onLoad({ filter: /.*/, namespace: 'api' }, () => ({ contents: names.map(n => 'export const '+n+'=(...args)=>globalThis.testApi?.'+n+' ? globalThis.testApi.'+n+'(...args) : Promise.resolve([]);').join('\n') }))
  b.onResolve({ filter: /\/(Analytics|Reports|TVPreviewViewport|CalendarDateRange|CompletedOfficeChart)$/ }, () => ({ path: 'component', namespace: 'stub' }))
  b.onLoad({ filter: /.*/, namespace: 'stub' }, () => ({ contents: 'export default function Stub(){return null}' }))
  b.onResolve({ filter: /\/useDisplayBoardData$/ }, () => ({ path: 'display', namespace: 'display' }))
  b.onLoad({ filter: /.*/, namespace: 'display' }, () => ({ contents: 'export const useDisplayBoardData=()=>({cashierTickets:[],registrarTickets:[],itmTickets:[],admissionTickets:[],servingTickets:[]});' }))
} }] })
const Admin = (await import('./.compiled/StaffNameEdit.js')).default
const storage = { getItem: () => null, setItem() {}, removeItem() {} }
Object.assign(globalThis, { window: Object.assign(new EventTarget(), { location: { origin: 'http://localhost:3000' }, localStorage: storage }), localStorage: storage,
  document: Object.assign(new EventTarget(), { hidden: false }), sessionStorage: storage })
const flush = fn => act(async () => { await fn?.(); await Promise.resolve() })
const label = n => typeof n === 'string' ? n : (n.children || []).map(label).join('')
for (const position of ['cashier','registrar','itm','admission']) {
  for (const role of ['head','dept_admin','legacy']) {
    let record = { user_id: 42, username: position+'1', full_name: 'Original Name', role: 'staff', position, status: 'active', assigned_window: { id: 7, department: position, window_number: 1 } }
    let payload, failure = false
    globalThis.testApi = {
      getStaffList: async () => [record], getServiceWindows: async () => [{ id: 7, staff_id: 42, department: position, window_number: 1 }],
      updateStaff: async (id, data) => { assert.equal(id,42); payload=data; if(failure) { const e=new Error('Invalid data'); e.response={errors:{full_name:['Name could not be saved.']}};throw e }
        record={...record,...data}; return {staff:record} },
    }
    const user = { role: role === 'dept_admin' ? 'dept_admin' : 'admin', position: role === 'head' ? null : position, full_name:'Admin' }
    let tree
    await flush(() => { tree=Renderer.create(React.createElement(MemoryRouter,{future:{v7_startTransition:true,v7_relativeSplatPath:true}},React.createElement(Admin,{user,initialPage:'staff'}))) })
    const button = text => tree.root.findAllByType('button').find(n => label(n) === text)
    await flush(() => button('Edit').props.onClick())
    const updated = position+' updated name'
    await flush(() => tree.root.findByProps({'aria-label':'Full Name'}).props.onChange({target:{value:'  '+updated+'  '}}))
    await flush(() => tree.root.findByProps({className:'staff-edit-row'}).props.onSubmit({preventDefault(){}}))
    assert.equal(payload.full_name,updated)
    assert(!('assigned_window_id' in payload),'name-only editing must preserve window assignment')
    assert(!('password' in payload))
    assert(label(tree.toJSON()).includes(updated),'saved name appears after list refresh')
    assert(label(tree.toJSON()).includes('Account updated successfully.'),'success feedback persists')
    await flush(() => button('Edit').props.onClick())
    assert.equal(tree.root.findByProps({'aria-label':'Full Name'}).props.value,updated)
    failure=true
    await flush(() => tree.root.findByProps({className:'staff-edit-row'}).props.onSubmit({preventDefault(){}}))
    assert(label(tree.toJSON()).includes('Name could not be saved.'))
    assert.equal(tree.root.findAllByProps({className:'staff-edit-row'}).length,1,'failed save keeps edit form open')
    await flush(() => tree.unmount())
    console.log('PASS '+role+' '+position+': saved name, preserved window/password, reload, and validation feedback')
  }
}
