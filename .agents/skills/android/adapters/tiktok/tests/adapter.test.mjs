import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { isAbsolute, relative } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import {
  RUNTIME_DIRECTORY,
  TIKTOK_PACKAGE,
  execute,
  parseOptions,
} from '../cli/tiktok.mjs'

const testsDirectory = fileURLToPath(new URL('.', import.meta.url))
const adapterDirectory = new URL('..', import.meta.url)
const adaptersDirectory = new URL('../..', import.meta.url)
const androidDirectory = new URL('../../..', import.meta.url)

function read(relativePath, base = adapterDirectory) {
  return readFileSync(new URL(relativePath, base), 'utf8')
}

test('TikTok adapter registers its bounded Android contract', () => {
  assert.ok(existsSync(new URL('ADAPTER.md', adapterDirectory)), testsDirectory)
  assert.match(read('REGISTRY.md', androidDirectory), /\| adapters\/ \|/)
  assert.match(read('SKILL.md', androidDirectory), /adapters\/REGISTRY\.md/)
  assert.match(read('REGISTRY.md', adaptersDirectory), /\| tiktok\/ \|/)

  const adapter = read('ADAPTER.md')
  assert.doesNotMatch(adapter, /^Read sibling `REGISTRY\.md` first\.$/m)
  assert.match(adapter, /com\.zhiliaoapp\.musically/)
  assert.match(adapter, /tiktok\.mjs check/)
  assert.match(adapter, /tiktok\.mjs inspect/)
  assert.match(adapter, /tiktok\.mjs open/)
  assert.match(adapter, /tiktok\.mjs screenshot/)
  assert.match(adapter, /tiktok\.mjs account-status/)
  assert.match(adapter, /tiktok\.mjs begin-login/)
  assert.match(adapter, /tiktok\.mjs sign-up/)
})

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [TIKTOK_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'TikTok' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Home' }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: TIKTOK_PACKAGE },
    tap: { ok: true, serial: 'pixel-3', action: 'tap' },
    push: { ok: true, serial: 'pixel-3', action: 'push' },
    shell: { ok: true, serial: 'pixel-3', action: 'shell' },
    screenshot: { ok: true, serial: 'pixel-3', out: '/unused.png' },
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

test('check requires the exact TikTok package', () => {
  const android = fakeAndroid()
  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    serial: 'pixel-3',
    package: TIKTOK_PACKAGE,
  })
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', TIKTOK_PACKAGE] }])

  assert.throws(
    () => execute(parseOptions(['check']), fakeAndroid({ packages: { ok: true, serial: 'pixel-3', packages: ['com.example.tiktok'] } }).invoke),
    /tiktok_not_installed/,
  )
})

test('inspect uses fresh current and UI dump results', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['inspect', '--serial', 'pixel-3']), android.invoke)

  assert.deepEqual(result, {
    ok: true,
    action: 'inspect',
    serial: 'pixel-3',
    package: TIKTOK_PACKAGE,
    focus: 'TikTok',
    elements: [{ text: 'Home' }],
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', TIKTOK_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('open launches TikTok then refreshes its visible state', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['open']), android.invoke)

  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'TikTok')
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'launch', 'current', 'dump'])
  assert.deepEqual(android.calls[1].args, ['--package', TIKTOK_PACKAGE])
})

test('screenshot stays in the ignored Android runtime directory', () => {
  const android = fakeAndroid({ screenshot: { ok: true, serial: 'pixel-3', out: '/returned.png' } })
  const result = execute(parseOptions(['screenshot', '--out', '.agents/skills/android/runtime/tiktok/shot.png']), android.invoke)
  const output = android.calls.at(-1).args.at(-1)

  assert.equal(result.action, 'screenshot')
  assert.equal(result.out, '/returned.png')
  assert.equal(isAbsolute(output), true)
  assert.equal(relative(RUNTIME_DIRECTORY, output).startsWith('..'), false)
  assert.throws(
    () => execute(parseOptions(['screenshot', '--out', '/tmp/tiktok.png']), fakeAndroid().invoke),
    /unsafe_screenshot_path/,
  )
})

test('begin-login reaches the observed email credential field without typing credentials', () => {
  const android = fakeAndroid({
    dump: [
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Use phone / email / username' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Phone' }, { text: 'Email / Username' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Email or username' }, { text: 'Continue' }] },
    ],
  })

  const result = execute(parseOptions(['begin-login', '--method', 'email']), android.invoke)

  assert.deepEqual(result, {
    ok: true,
    action: 'begin-login',
    serial: 'pixel-3',
    package: TIKTOK_PACKAGE,
    method: 'email',
    authState: 'awaiting-user-credential',
    field: 'Email or username',
  })
  assert.deepEqual(android.calls.map(({ command }) => command), [
    'packages', 'launch', 'current', 'dump', 'tap', 'current', 'dump', 'tap', 'current', 'dump',
  ])
  assert.deepEqual(android.calls[4].args, ['--text', 'Use phone / email / username'])
  assert.deepEqual(android.calls[7].args, ['--text', 'Email / Username'])
})

test('account-status reports the observed signed-out login surface', () => {
  const android = fakeAndroid({
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Log in to TikTok' }] },
  })

  assert.deepEqual(execute(parseOptions(['account-status']), android.invoke), {
    ok: true,
    action: 'account-status',
    serial: 'pixel-3',
    package: TIKTOK_PACKAGE,
    authState: 'signed-out',
  })
})

test('switch-account requires account option and taps target or switcher', () => {
  const android = fakeAndroid({
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: '@creator_alt', desc: 'Account' }] },
  })

  const result = execute(parseOptions(['switch-account', '--account', '@creator_alt']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'switch-account')
  assert.equal(result.switchedTo, '@creator_alt')
})

test('create-hook transitions to creator draft view safely', () => {
  const android = fakeAndroid({
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: '+', desc: 'Create' }] },
  })

  const result = execute(parseOptions(['create-hook']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'create-hook')
  assert.equal(result.stage, 'creator_view_opened')
})

test('stage-content pushes media file to Android media store', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['stage-content', '--path', '.agents/skills/android/runtime/tiktok/video.mp4']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'stage-content')
  assert.equal(result.stagedPath, '/sdcard/DCIM/Camera/video.mp4')
})

test('sign-up parses options and reaches sign-up surface on Android', () => {
  const options = parseOptions(['sign-up', '--email', 'creator@outerscope.xyz', '--birthday', '1998-01-15'])
  assert.equal(options.command, 'sign-up')
  assert.equal(options.email, 'creator@outerscope.xyz')
  assert.equal(options.birthday, '1998-01-15')

  const android = fakeAndroid({
    dump: [
      { ok: true, serial: 'pixel-3', elements: [{ desc: 'Cancel', resourceId: 'com.google.android.gms:id/cancel' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Don’t have an account? Sign up' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Use phone or email' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Email' }, { text: 'Month' }] },
    ],
  })

  const result = execute(options, android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'sign-up')
  assert.equal(result.email, 'creator@outerscope.xyz')
  assert.equal(result.stage, 'credential_surface_reached')
})

