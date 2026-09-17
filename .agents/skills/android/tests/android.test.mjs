import assert from 'node:assert/strict'
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { spawnSync } from 'node:child_process'

const ROOT = new URL('../../../../../', import.meta.url)
const CLI = new URL('../cli/android.mjs', import.meta.url)
const UI_XML = `<?xml version="1.0" encoding="UTF-8"?>
<hierarchy>
  <node index="0" text="" content-desc="" resource-id="" class="android.widget.FrameLayout" clickable="false" enabled="true" bounds="[0,0][1080,1920]" />
  <node index="1" text="Continue" content-desc="Continue button" resource-id="com.example:id/continue" class="android.widget.Button" clickable="true" enabled="true" bounds="[120,1500][960,1600]" />
</hierarchy>`

const EXACT_TAP_ARGS = [
  'tap',
  '--serial', 'device-1',
  '--index', '1',
  '--id', 'com.example:id/continue',
  '--class', 'android.widget.Button',
  '--bounds', '[120,1500][960,1600]',
  '--unique', 'true',
]

function createFakeAdb(devices, packages = []) {
  const root = mkdtempSync(join(tmpdir(), 'vader-android-test-'))
  const bin = join(root, 'bin')
  const log = join(root, 'adb.log')
  const adb = join(bin, 'adb')
  const deviceRows = devices.map((serial) => `${serial}\tdevice product:fixture model:Fixture transport_id:1`).join('\n')
  const packageRows = packages.map((name) => `package:${name}`).join('\\n')
  mkdirSync(bin)
  const source = `#!/bin/sh
set -eu
printf '%s\\n' "$*" >> "$VADER_ANDROID_TEST_LOG"
if [ "$1" = "devices" ]; then
  printf 'List of devices attached\\n${deviceRows}\\n'
  exit 0
fi
if [ "$1" = "-s" ]; then
  shift 2
fi
case "$*" in
  'shell uiautomator dump /sdcard/window.xml') exit 0 ;;
  'exec-out cat /sdcard/window.xml') printf '%s\\n' "$VADER_ANDROID_TEST_XML" ;;
  'shell pm list packages') printf '${packageRows}\\n' ;;
  'shell dumpsys window') printf 'mCurrentFocus=Window{42 u0 com.zhiliaoapp.musically/com.ss.android.ugc.aweme.main.MainActivity}\\n' ;;
  'shell input tap 540 1550') exit 0 ;;
  'shell input text '*)
    if [ "\${VADER_ANDROID_TEST_FAIL_SENSITIVE:-}" = "1" ]; then
      printf 'failed command: %s\\n' "$*" >&2
      exit 1
    fi
    exit 0
    ;;
  *) printf 'unexpected adb command: %s\\n' "$*" >&2; exit 1 ;;
esac
`
  writeFileSync(adb, source, { mode: 0o700 })
  chmodSync(adb, 0o700)
  return {
    root,
    log,
    env: {
      ...process.env,
      PATH: `${bin}:${process.env.PATH}`,
      VADER_ANDROID_TEST_LOG: log,
      VADER_ANDROID_TEST_XML: UI_XML,
    },
  }
}

function run(args, env, input) {
  return spawnSync(process.execPath, [CLI.pathname, ...args], {
    encoding: 'utf8',
    env,
    input,
  })
}

test('tap refreshes UIAutomator state and taps the selector match center', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run(['tap', '--serial', 'device-1', '--text', 'Continue'], fixture.env)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: true,
      serial: 'device-1',
      action: 'tap',
      x: 540,
      y: 1550,
      element: {
        text: 'Continue',
        desc: 'Continue button',
        resourceId: 'com.example:id/continue',
        className: 'android.widget.Button',
        bounds: { x1: 120, y1: 1500, x2: 960, y2: 1600, x: 540, y: 1550 },
      },
    })
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), [
      'devices -l',
      '-s device-1 shell uiautomator dump /sdcard/window.xml',
      '-s device-1 exec-out cat /sdcard/window.xml',
      '-s device-1 shell input tap 540 1550',
    ])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('tap rejects visible text with any repeatable case-insensitive guard before input and redacts the observation', () => {
  const fixture = createFakeAdb(['device-1'])
  const observedText = 'GUARD refusal observed sentinel'
  const unsafeXml = UI_XML.replace(
    '</hierarchy>',
    `  <node index="2" text="${observedText}" content-desc="" resource-id="" class="android.widget.TextView" clickable="false" enabled="true" bounds="[40,400][1040,500]" />\n</hierarchy>`,
  )
  try {
    const result = run([
      'tap', '--serial', 'device-1', '--text', 'Continue',
      '--reject-regex', 'choose an account',
      '--reject-regex', 'guard refusal observed sentinel',
    ], { ...fixture.env, VADER_ANDROID_TEST_XML: unsafeXml })

    assert.equal(result.status, 1, result.stderr || result.stdout)
    assert.equal(JSON.parse(result.stdout).error, 'tap_rejected_by_guard')
    assert.equal(result.stdout.toLowerCase().includes(observedText.toLowerCase()), false)
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), [
      'devices -l',
      '-s device-1 shell uiautomator dump /sdcard/window.xml',
      '-s device-1 exec-out cat /sdcard/window.xml',
    ])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('--reject-regex is accepted only by tap and fails before ADB otherwise', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run(['dump', '--reject-regex', 'unsafe'], fixture.env)

    assert.equal(result.status, 1, result.stderr || result.stdout)
    assert.equal(JSON.parse(result.stdout).error, 'reject_regex_only_supported_for_tap')
    assert.equal(existsSync(fixture.log), false)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('guarded tap validates an exact unique final fingerprint before tapping', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run(EXACT_TAP_ARGS, fixture.env)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.equal(JSON.parse(result.stdout).x, 540)
    assert.equal(JSON.parse(result.stdout).y, 1550)
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), [
      'devices -l',
      '-s device-1 shell uiautomator dump /sdcard/window.xml',
      '-s device-1 exec-out cat /sdcard/window.xml',
      '-s device-1 shell input tap 540 1550',
    ])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('tap does not ignore supplied selector constraints when index is present', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run([
      'tap', '--serial', 'device-1', '--index', '1', '--id', 'com.example:id/changed',
    ], fixture.env)

    assert.equal(result.status, 1)
    assert.match(JSON.parse(result.stdout).error, /element_not_found/)
    assert.equal(readFileSync(fixture.log, 'utf8').includes('shell input tap'), false)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('guarded tap refuses a missing, changed, moved, or duplicate final target before tapping', () => {
  const cases = [
    ['missing', `<?xml version="1.0"?><hierarchy>
      <node index="0" text="" content-desc="" resource-id="" class="android.widget.FrameLayout" clickable="false" enabled="true" bounds="[0,0][1080,1920]" />
    </hierarchy>`],
    ['changed index', UI_XML.replace(
      '  <node index="1" text="Continue"',
      '  <node index="1" text="Spacer" content-desc="" resource-id="" class="android.view.View" clickable="false" enabled="true" bounds="[0,1000][1080,1100]" />\n  <node index="2" text="Continue"',
    )],
    ['changed id', UI_XML.replace('com.example:id/continue', 'com.example:id/changed')],
    ['changed class', UI_XML.replace('android.widget.Button', 'android.widget.TextView')],
    ['moved bounds', UI_XML.replace('[120,1500][960,1600]', '[120,1400][960,1500]')],
    ['duplicate', UI_XML.replace(
      '</hierarchy>',
      '  <node index="2" text="Continue" content-desc="Continue button" resource-id="com.example:id/continue" class="android.widget.Button" clickable="true" enabled="true" bounds="[120,1500][960,1600]" />\n</hierarchy>',
    )],
  ]

  for (const [name, xml] of cases) {
    const fixture = createFakeAdb(['device-1'])
    try {
      const result = run(EXACT_TAP_ARGS, { ...fixture.env, VADER_ANDROID_TEST_XML: xml })

      assert.equal(result.status, 1, `${name}: ${result.stderr || result.stdout}`)
      assert.equal(readFileSync(fixture.log, 'utf8').includes('shell input tap'), false, name)
    } finally {
      rmSync(fixture.root, { recursive: true, force: true })
    }
  }
})

test('guarded tap treats a same-identity control at different bounds as a duplicate', () => {
  const fixture = createFakeAdb(['device-1'])
  const duplicateAtDifferentBounds = UI_XML.replace(
    '</hierarchy>',
    '  <node index="2" text="Continue" content-desc="Continue button" resource-id="com.example:id/continue" class="android.widget.Button" clickable="true" enabled="true" bounds="[120,1300][960,1400]" />\n</hierarchy>',
  )
  try {
    const result = run(EXACT_TAP_ARGS, {
      ...fixture.env,
      VADER_ANDROID_TEST_XML: duplicateAtDifferentBounds,
    })

    assert.equal(result.status, 1, result.stderr || result.stdout)
    assert.match(JSON.parse(result.stdout).error, /element_not_unique/)
    assert.equal(readFileSync(fixture.log, 'utf8').includes('shell input tap'), false)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('guarded tap rejects malformed bounds and non-true uniqueness before ADB', () => {
  for (const args of [
    ['tap', '--bounds', '120,1500,960,1600'],
    ['tap', '--bounds', '[120,1500][120,1600]'],
    ['tap', '--unique', 'false'],
    ['tap', '--unique', 'yes'],
  ]) {
    const fixture = createFakeAdb(['device-1'])
    try {
      const result = run(args, fixture.env)

      assert.equal(result.status, 1, `${args.join(' ')}: ${result.stderr || result.stdout}`)
      assert.equal(existsSync(fixture.log), false, args.join(' '))
    } finally {
      rmSync(fixture.root, { recursive: true, force: true })
    }
  }
})

test('dump retains fresh bounds for every public UI element', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run(['dump', '--serial', 'device-1'], fixture.env)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: true,
      serial: 'device-1',
      elements: [
        {
          text: '',
          desc: '',
          resourceId: '',
          className: 'android.widget.FrameLayout',
          bounds: { x1: 0, y1: 0, x2: 1080, y2: 1920, x: 540, y: 960 },
        },
        {
          text: 'Continue',
          desc: 'Continue button',
          resourceId: 'com.example:id/continue',
          className: 'android.widget.Button',
          bounds: { x1: 120, y1: 1500, x2: 960, y2: 1600, x: 540, y: 1550 },
        },
      ],
    })
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('wait requires the supplied exact bounds before returning a selector match', () => {
  const args = [
    'wait', '--serial', 'device-1',
    '--id', 'com.example:id/continue',
    '--class', 'android.widget.Button',
    '--bounds', '[120,1500][960,1600]',
    '--unique', 'true',
    '--timeout-ms', '1', '--poll-ms', '1',
  ]
  const fixture = createFakeAdb(['device-1'])
  const movedFixture = createFakeAdb(['device-1'])
  try {
    const matched = run(args, fixture.env)
    assert.equal(matched.status, 0, matched.stderr || matched.stdout)

    const moved = run(args, {
      ...movedFixture.env,
      VADER_ANDROID_TEST_XML: UI_XML.replace('[120,1500][960,1600]', '[120,1400][960,1500]'),
    })
    assert.equal(moved.status, 1, moved.stderr || moved.stdout)
    assert.match(JSON.parse(moved.stdout).error, /wait_timeout: element_not_found/)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
    rmSync(movedFixture.root, { recursive: true, force: true })
  }
})

test('device commands reject ambiguous ADB selection before touching an app', () => {
  const fixture = createFakeAdb(['device-1', 'device-2'])
  try {
    const result = run(['dump'], fixture.env)

    assert.equal(result.status, 1)
    assert.match(result.stdout, /multiple_devices: pass --serial/)
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), ['devices -l'])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('packages filters an exact Android package without relying on its display name', () => {
  const fixture = createFakeAdb(['device-1'], [
    'com.zhiliaoapp.musically',
    'com.example.tiktok-helper',
  ])
  try {
    const result = run(['packages', '--serial', 'device-1', '--package', 'com.zhiliaoapp.musically'], fixture.env)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: true,
      serial: 'device-1',
      packages: ['com.zhiliaoapp.musically'],
    })
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('current reads the active focus from dumpsys window', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run(['current', '--serial', 'device-1'], fixture.env)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: true,
      serial: 'device-1',
      focus: 'mCurrentFocus=Window{42 u0 com.zhiliaoapp.musically/com.ss.android.ugc.aweme.main.MainActivity}',
    })
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), [
      'devices -l',
      '-s device-1 shell dumpsys window',
    ])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('type keeps its public --text behavior and typed-length result', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const result = run(['type', '--serial', 'device-1', '--text', 'hello world'], fixture.env)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: true,
      serial: 'device-1',
      action: 'type',
      typedLength: 11,
    })
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), [
      'devices -l',
      '-s device-1 shell input text hello%sworld',
    ])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('type-stdin accepts --serial, types one stdin value, and returns no payload metadata', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const sensitiveValue = 'one time value'
    const result = run(['type-stdin', '--serial', 'device-1'], fixture.env, `${sensitiveValue}\n`)

    assert.equal(result.status, 0, result.stderr || result.stdout)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: true,
      serial: 'device-1',
      action: 'type-stdin',
    })
    assert.equal(result.stdout.includes(sensitiveValue), false)
    assert.equal(result.stdout.includes(String(sensitiveValue.length)), false)
    assert.equal(result.stderr, '')
    assert.deepEqual(readFileSync(fixture.log, 'utf8').trim().split('\n'), [
      'devices -l',
      '-s device-1 shell input text one%stime%svalue',
    ])
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('type-stdin rejects --text before ADB and does not expose its option value', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const sensitiveValue = 'must-not-be-an-option'
    const result = run(['type-stdin', '--text', sensitiveValue], fixture.env)

    assert.equal(result.status, 1)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: false,
      error: 'type_stdin_options: only --serial is allowed',
      usage: 'Usage: android.mjs <doctor|devices|waydroid-status|start-waydroid|stop-waydroid|current|packages|launch|install-apk|dump|screenshot|tap|type|type-stdin|key|swipe|wait|open-url> [options]',
    })
    assert.equal(result.stdout.includes(sensitiveValue), false)
    assert.equal(result.stderr.includes(sensitiveValue), false)
    assert.equal(existsSync(fixture.log), false)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('type-stdin redacts malformed positional input before option parsing', () => {
  const sensitiveValue = `positional-redaction-sentinel-${'x'.repeat(31)}`
  const result = run(['type-stdin', sensitiveValue], process.env)
  const output = `${result.stdout}\n${result.stderr}`

  assert.equal(result.status, 1)
  assert.equal(JSON.parse(result.stdout).error, 'type_stdin_invalid_input')
  assert.equal(output.includes(sensitiveValue), false)
  assert.equal(output.includes(String(sensitiveValue.length)), false)
})

test('public commands preserve detailed positional argument errors', () => {
  const result = run(['type', 'public-positional-value'], process.env)

  assert.equal(result.status, 1)
  assert.equal(JSON.parse(result.stdout).error, 'invalid_argument: public-positional-value')
})

test('type-stdin rejects empty or multiline standard input before ADB', () => {
  for (const [input, error] of [
    ['', 'stdin_value_required'],
    ['\n', 'stdin_value_required'],
    ['first\nsecond\n', 'stdin_single_value_required'],
  ]) {
    const fixture = createFakeAdb(['device-1'])
    try {
      const result = run(['type-stdin', '--serial', 'device-1'], fixture.env, input)

      assert.equal(result.status, 1)
      assert.equal(JSON.parse(result.stdout).error, error)
      assert.equal(existsSync(fixture.log), false)
    } finally {
      rmSync(fixture.root, { recursive: true, force: true })
    }
  }
})

test('type-stdin redacts payload and ADB details when sensitive typing fails', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const sensitiveValue = 'failure payload'
    const env = { ...fixture.env, VADER_ANDROID_TEST_FAIL_SENSITIVE: '1' }
    const result = run(['type-stdin', '--serial', 'device-1'], env, sensitiveValue)

    assert.equal(result.status, 1)
    assert.deepEqual(JSON.parse(result.stdout), {
      ok: false,
      error: 'adb_sensitive_input_failed',
      usage: 'Usage: android.mjs <doctor|devices|waydroid-status|start-waydroid|stop-waydroid|current|packages|launch|install-apk|dump|screenshot|tap|type|type-stdin|key|swipe|wait|open-url> [options]',
    })
    assert.equal(result.stdout.includes(sensitiveValue), false)
    assert.equal(result.stdout.includes('failure%spayload'), false)
    assert.equal(result.stdout.includes(String(sensitiveValue.length)), false)
    assert.equal(result.stderr.includes(sensitiveValue), false)
    assert.equal(result.stderr.includes('failure%spayload'), false)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})

test('type-stdin redacts payload when sensitive ADB spawning throws', () => {
  const fixture = createFakeAdb(['device-1'])
  try {
    const sensitiveValue = 'nul\0payload'
    const result = run(['type-stdin', '--serial', 'device-1'], fixture.env, sensitiveValue)

    assert.equal(result.status, 1)
    assert.equal(JSON.parse(result.stdout).error, 'adb_sensitive_input_failed')
    assert.equal(result.stdout.includes('nul'), false)
    assert.equal(result.stdout.includes('payload'), false)
    assert.equal(result.stdout.includes(String(sensitiveValue.length)), false)
    assert.equal(result.stderr.includes('nul'), false)
    assert.equal(result.stderr.includes('payload'), false)
  } finally {
    rmSync(fixture.root, { recursive: true, force: true })
  }
})
