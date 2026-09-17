import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { isAbsolute, relative } from 'node:path'
import test from 'node:test'
import {
  DILMIL_PACKAGE,
  RUNTIME_DIRECTORY,
  execute,
  parseOptions,
} from '../cli/dilmil.mjs'

const adapterDirectory = new URL('..', import.meta.url)
const adaptersDirectory = new URL('../..', import.meta.url)
const androidDirectory = new URL('../../..', import.meta.url)

function read(relativePath, base = adapterDirectory) {
  return readFileSync(new URL(relativePath, base), 'utf8')
}

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [DILMIL_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'Dil Mil' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Welcome', clickable: true }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: DILMIL_PACKAGE },
    tap: { ok: true, serial: 'pixel-3', action: 'tap' },
    'type-stdin': { ok: true, serial: 'pixel-3', action: 'type-stdin' },
    screenshot: { ok: true, serial: 'pixel-3', out: '/returned.png' },
  }
  return {
    calls,
    invoke(command, args, stdin) {
      calls.push({ command, args, stdin })
      const response = overrides[command] || defaults[command]
      return Array.isArray(response) ? response.shift() : response
    },
  }
}

test('DilMil adapter documents its bounded Android contract', () => {
  assert.ok(existsSync(new URL('ADAPTER.md', adapterDirectory)))
  assert.match(read('REGISTRY.md', androidDirectory), /\| adapters\/ \|/)
  assert.match(read('SKILL.md', androidDirectory), /adapters\/REGISTRY\.md/)
  assert.match(read('REGISTRY.md', adaptersDirectory), /\| dilmil\/ \|/)

  const adapter = read('ADAPTER.md')
  assert.match(adapter, /co\.dilmil\.android/)
  assert.match(adapter, /dilmil\.mjs check/)
  assert.match(adapter, /dilmil\.mjs inspect/)
  assert.match(adapter, /dilmil\.mjs open/)
  assert.match(adapter, /dilmil\.mjs screenshot/)
  assert.match(adapter, /dilmil\.mjs begin-login/)
  assert.match(adapter, /dilmil\.mjs fill-phone/)
  assert.match(adapter, /dilmil\.mjs verify-otp/)
  assert.match(adapter, /dilmil\.mjs connections/)
})

test('DilMil check identifies only the DilMil package', () => {
  const android = fakeAndroid()
  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'dilmil',
    name: 'Dil Mil',
    serial: 'pixel-3',
    package: DILMIL_PACKAGE,
  })
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', DILMIL_PACKAGE], stdin: undefined }])
  assert.throws(
    () => execute(
      parseOptions(['check']),
      fakeAndroid({ packages: { ok: true, serial: 'pixel-3', packages: ['com.example.dilmil'] } }).invoke,
    ),
    /dilmil_not_installed/,
  )
})

test('DilMil open launches then refreshes the initial visible state', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['open', '--serial', 'pixel-3']), android.invoke)
  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'Dil Mil')
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'launch', 'current', 'dump'])
  assert.deepEqual(android.calls[1].args, ['--serial', 'pixel-3', '--package', DILMIL_PACKAGE])
})

test('DilMil screenshot output is restricted to its runtime directory', () => {
  const android = fakeAndroid()
  execute(parseOptions(['screenshot', '--out', 'initial.png']), android.invoke)
  const output = android.calls.at(-1).args.at(-1)
  assert.equal(isAbsolute(output), true)
  assert.equal(relative(RUNTIME_DIRECTORY, output).startsWith('..'), false)
  assert.throws(
    () => execute(parseOptions(['screenshot', '--out', '/tmp/dilmil.png']), fakeAndroid().invoke),
    /unsafe_screenshot_path/,
  )
})

test('DilMil begin-login initiates phone auth route safely', () => {
  const android = fakeAndroid({
    dump: [
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Sign in with phone', bounds: '[100,500][900,600]' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Enter Phone Number', bounds: '[100,200][900,300]' }] },
    ],
  })

  const result = execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'begin-login')
  assert.equal(result.status, 'ready_for_phone')
})

test('DilMil begin-login stops on unsafe purchase surface', () => {
  const android = fakeAndroid({
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil VIP Elite Subscribe' }] },
  })

  assert.throws(
    () => execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
    /unsafe_surface_detected: purchase/,
  )
})

test('DilMil connections returns candidate match count', () => {
  const android = fakeAndroid({
    dump: {
      ok: true,
      serial: 'pixel-3',
      elements: [
        { text: 'Aanya', resourceId: 'co.dilmil.android:id/match_row', bounds: '[0,100][500,200]' },
        { text: 'Priya', resourceId: 'co.dilmil.android:id/match_row', bounds: '[0,200][500,300]' },
      ],
    },
  })

  const result = execute(parseOptions(['connections']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'connections')
  assert.equal(result.count, 2)
  assert.equal(result.matches[0].name, 'Aanya')
})
