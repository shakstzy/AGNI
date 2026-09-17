import assert from 'node:assert/strict'
import { mkdirSync, mkdtempSync, rmSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { isAbsolute, join, relative, resolve } from 'node:path'
import test from 'node:test'
import { createStandardAppAdapter } from '../cli/standard-app.mjs'

const adapter = createStandardAppAdapter({
  id: 'fixture',
  name: 'Fixture App',
  packageName: 'com.example.fixture',
  runtimeDirectory: '/tmp/vader-standard-app-runtime',
})

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: ['com.example.fixture'] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: 'com.example.fixture' },
    current: { ok: true, serial: 'pixel-3', focus: 'com.example.fixture/.MainActivity' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Home' }] },
    screenshot: { ok: true, serial: 'pixel-3', out: '/tmp/vader-standard-app-runtime/returned.png' },
  }
  return {
    calls,
    invoke(command, args) {
      calls.push({ command, args })
      const response = overrides[command] || defaults[command]
      return Array.isArray(response) ? response.shift() : response
    },
  }
}

test('check requires the exact configured package', () => {
  const android = fakeAndroid()

  assert.deepEqual(adapter.execute(adapter.parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'fixture',
    name: 'Fixture App',
    serial: 'pixel-3',
    package: 'com.example.fixture',
  })
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', 'com.example.fixture'] }])
  assert.throws(
    () => adapter.execute(adapter.parseOptions(['check']), fakeAndroid({
      packages: { ok: true, serial: 'pixel-3', packages: ['com.example.fixture.helper'] },
    }).invoke),
    /fixture_not_installed/,
  )
})

test('open launches the package then refreshes its visible state', () => {
  const android = fakeAndroid()

  assert.deepEqual(adapter.execute(adapter.parseOptions(['open', '--serial', 'pixel-3']), android.invoke), {
    ok: true,
    action: 'open',
    id: 'fixture',
    name: 'Fixture App',
    serial: 'pixel-3',
    package: 'com.example.fixture',
    focus: 'com.example.fixture/.MainActivity',
    elements: [{ text: 'Home' }],
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', 'com.example.fixture'] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', 'com.example.fixture'] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('screenshot output is confined to the configured runtime directory', () => {
  const android = fakeAndroid()
  const result = adapter.execute(adapter.parseOptions(['screenshot', '--out', 'shot.png']), android.invoke)
  const output = android.calls.at(-1).args.at(-1)

  assert.equal(result.action, 'screenshot')
  assert.equal(isAbsolute(output), true)
  assert.equal(relative('/tmp/vader-standard-app-runtime', output).startsWith('..'), false)
  assert.equal(output, resolve('/tmp/vader-standard-app-runtime/shot.png'))
  assert.throws(
    () => adapter.execute(adapter.parseOptions(['screenshot', '--out', '/tmp/fixture.png']), fakeAndroid().invoke),
    /unsafe_screenshot_path/,
  )
})

test('screenshot rejects an in-runtime symlink that redirects outside runtime', () => {
  const root = mkdtempSync(join(tmpdir(), 'vader-standard-app-runtime-'))
  const runtimeDirectory = join(root, 'runtime')
  const outsideDirectory = join(root, 'outside')
  mkdirSync(runtimeDirectory)
  mkdirSync(outsideDirectory)
  symlinkSync(outsideDirectory, join(runtimeDirectory, 'redirect'))
  const symlinkAdapter = createStandardAppAdapter({
    id: 'fixture',
    name: 'Fixture App',
    packageName: 'com.example.fixture',
    runtimeDirectory,
  })
  const android = fakeAndroid()

  try {
    assert.throws(
      () => symlinkAdapter.execute(symlinkAdapter.parseOptions(['screenshot', '--out', 'redirect/escaped.png']), android.invoke),
      /unsafe_screenshot_path/,
    )
    assert.deepEqual(android.calls.map(({ command }) => command), ['packages'])
  } finally {
    rmSync(root, { recursive: true, force: true })
  }
})
