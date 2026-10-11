import { spawn, spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const backendDir = path.resolve(frontendDir, '..', 'queuing-system-backend')
const viteBin = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js')

const children = []
let stopping = false

function start(command, args, cwd, label, required = true) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
    shell: false,
    windowsHide: true,
  })

  child.on('error', (error) => {
    console.error(`[${label}] Could not start: ${error.message}`)
    if (required) stop(1)
  })

  child.on('exit', (code) => {
    if (!stopping && code !== 0) {
      console.error(`[${label}] Exited with code ${code}.`)
      if (required) stop(code ?? 1)
    }
  })

  children.push(child)
}

function stop(exitCode = 0) {
  if (stopping) return
  stopping = true

  for (const child of children) {
    if (!child.killed) child.kill('SIGTERM')
  }

  setTimeout(() => process.exit(exitCode), 250)
}

console.log('Starting Laravel API at http://127.0.0.1:8000 ...')
console.log('Starting frontend at http://localhost:3000 ...')
console.log('XAMPP MySQL must be running for database access.\n')

// Initialize the shared signing configuration before Laravel reads it.
if (process.platform === 'win32') {
  const printDir = path.resolve(frontendDir, '..', 'kiosk-print-service')
  const python = process.env.KIOSK_PYTHON || 'python'
  const initialized = spawnSync(python, ['service.py', '--initialize'], {
    cwd: printDir, windowsHide: true, encoding: 'utf8',
  })
  if (initialized.status === 0) {
    start(python, ['service.py'], printDir, 'Silent printer', false)
  } else {
    console.warn('Silent printer unavailable. See kiosk-print-service/README.md.', initialized.error?.message || initialized.stderr)
  }
}

start('php', ['artisan', 'serve', '--host=127.0.0.1', '--port=8000'], backendDir, 'Laravel')
start(process.execPath, [viteBin], frontendDir, 'Vite')

process.on('SIGINT', () => stop(0))
process.on('SIGTERM', () => stop(0))
