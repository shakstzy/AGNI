import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { isAbsolute, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import {
  MIRCHI_PACKAGE,
  RUNTIME_DIRECTORY,
  execute,
  parseOptions,
} from '../cli/mirchi.mjs'

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [MIRCHI_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'Mirchi' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Initial surface' }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: MIRCHI_PACKAGE },
    screenshot: { ok: true, serial: 'pixel-3', out: '/returned.png' },
  }
  return {
    calls,
    invoke(command, args) {
      calls.push({ command, args })
      return overrides[command] || defaults[command]
    },
  }
}

const INITIAL_PHONE_LOGIN_SURFACE = [
  {
    text: 'SIGN IN WITH NUMBER',
    desc: '',
    resourceId: '',
    className: 'android.widget.TextView',
    bounds: { x1: 287, y1: 1516, x2: 794, y2: 1556, x: 541, y: 1536 },
  },
]

const PHONE_SURFACE = [
  {
    text: '1234567890',
    desc: '',
    resourceId: 'com.dating.mirchi:id/etNumber',
    className: 'android.widget.EditText',
    bounds: { x1: 492, y1: 537, x2: 1014, y2: 644, x: 753, y: 591 },
  },
  {
    text: ' US  +1',
    desc: 'United States phone code is +1',
    resourceId: 'com.dating.mirchi:id/textView_selectedCountry',
    className: 'android.widget.TextView',
    bounds: { x1: 214, y1: 557, x2: 368, y2: 624, x: 291, y: 591 },
  },
  {
    text: '',
    desc: '',
    resourceId: 'com.dating.mirchi:id/btnContinue',
    className: 'android.widget.ImageView',
    bounds: { x1: 659, y1: 848, x2: 1014, y2: 986, x: 837, y: 917 },
  },
]

function scriptedAndroid({ dumps = [PHONE_SURFACE], currents, overrides = {} } = {}) {
  const calls = []
  let dumpIndex = 0
  let currentIndex = 0
  const currentResults = currents || [
    {
      ok: true,
      serial: 'pixel-3',
      focus: 'mCurrentFocus=Window{1 u0 com.dating.mirchi/com.dating.mirchi.activity.LoginWithNumberActivity}',
    },
  ]
  return {
    calls,
    invoke(command, args, input) {
      calls.push({ command, args, ...(input === undefined ? {} : { input }) })
      if (overrides[command]) return overrides[command]({ command, args, input, calls })
      if (command === 'packages') {
        return { ok: true, serial: 'pixel-3', packages: [MIRCHI_PACKAGE] }
      }
      if (command === 'launch') {
        return { ok: true, serial: 'pixel-3', action: 'launch', package: MIRCHI_PACKAGE }
      }
      if (command === 'wait') {
        const elements = dumps[Math.min(dumpIndex, dumps.length - 1)]
        const valueFor = (flag) => args[args.indexOf(flag) + 1]
        const expectedBounds = valueFor('--bounds')
        const matches = elements.filter((element) => (
          (args.includes('--text') ? element.text === valueFor('--text') : true)
          && (args.includes('--desc') ? element.desc === valueFor('--desc') : true)
          && (args.includes('--id') ? element.resourceId === valueFor('--id') : true)
          && (args.includes('--class') ? element.className === valueFor('--class') : true)
          && (expectedBounds
            ? `[${element.bounds.x1},${element.bounds.y1}][${element.bounds.x2},${element.bounds.y2}]` === expectedBounds
            : true)
        ))
        return matches.length === 1
          ? { ok: true, serial: 'pixel-3', action: 'wait', waitedMs: 0, element: {} }
          : { ok: false, serial: 'pixel-3', error: 'wait_timeout' }
      }
      if (command === 'current') {
        const result = currentResults[Math.min(currentIndex, currentResults.length - 1)]
        currentIndex += 1
        return result
      }
      if (command === 'dump') {
        const elements = dumps[Math.min(dumpIndex, dumps.length - 1)]
        dumpIndex += 1
        return { ok: true, serial: 'pixel-3', elements }
      }
      if (command === 'tap') return { ok: true, serial: 'pixel-3', action: 'tap' }
      if (command === 'type-stdin') return { ok: true, serial: 'pixel-3', action: 'type-stdin' }
      throw new Error(`unexpected_android_command: ${command}`)
    },
  }
}

function withoutRejectRegex(args) {
  const normalized = []
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === '--reject-regex') {
      index += 1
      continue
    }
    normalized.push(args[index])
  }
  return normalized
}

function withoutTapRejectGuards(calls) {
  return calls.map((call) => (
    call.command === 'tap' ? { ...call, args: withoutRejectRegex(call.args) } : call
  ))
}

test('begin-login supports only the exact phone method', () => {
  assert.deepEqual(parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']), {
    command: 'begin-login',
    method: 'phone',
    serial: 'pixel-3',
  })
  assert.throws(() => parseOptions(['begin-login']), /phone_login_method_required/)
  assert.throws(() => parseOptions(['begin-login', '--method', 'google']), /unsupported_login_method/)
})

test('begin-login launches and resumes only the exact empty Mirchi phone form', () => {
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE] })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'begin-login',
    id: 'mirchi',
    name: 'Mirchi',
    serial: 'pixel-3',
    package: MIRCHI_PACKAGE,
    method: 'phone',
    status: 'phone-surface-ready',
    codeRequested: false,
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', MIRCHI_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', MIRCHI_PACKAGE] },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--text', '1234567890',
        '--desc', '',
        '--id', 'com.dating.mirchi:id/etNumber',
        '--class', 'android.widget.EditText',
        '--bounds', '[492,537][1014,644]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('begin-login accepts the live exact Mirchi country-label spacing', () => {
  const livePhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 1 ? { ...element, text: ' US  +1' } : element
  ))
  const android = scriptedAndroid({ dumps: [livePhoneSurface] })

  assert.deepEqual(
    execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
    {
      ok: true,
      action: 'begin-login',
      id: 'mirchi',
      name: 'Mirchi',
      serial: 'pixel-3',
      package: MIRCHI_PACKAGE,
      method: 'phone',
      status: 'phone-surface-ready',
      codeRequested: false,
    },
  )
})

test('begin-login accepts the live exact Mirchi country-label description', () => {
  const livePhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 1 ? { ...element, desc: 'United States phone code is +1' } : element
  ))
  const android = scriptedAndroid({ dumps: [livePhoneSurface] })

  assert.deepEqual(
    execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
    {
      ok: true,
      action: 'begin-login',
      id: 'mirchi',
      name: 'Mirchi',
      serial: 'pixel-3',
      package: MIRCHI_PACKAGE,
      method: 'phone',
      status: 'phone-surface-ready',
      codeRequested: false,
    },
  )
})

test('begin-login guarded-taps the exact observed route and freshly proves the phone form', () => {
  const android = scriptedAndroid({
    dumps: [INITIAL_PHONE_LOGIN_SURFACE, PHONE_SURFACE],
    currents: [
      {
        ok: true,
        serial: 'pixel-3',
        focus: 'mCurrentFocus=Window{1 u0 com.dating.mirchi/com.dating.mirchi.LoginActivity}',
      },
      {
        ok: true,
        serial: 'pixel-3',
        focus: 'mCurrentFocus=Window{1 u0 com.dating.mirchi/com.dating.mirchi.activity.LoginWithNumberActivity}',
      },
    ],
  })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'begin-login',
    id: 'mirchi',
    name: 'Mirchi',
    serial: 'pixel-3',
    package: MIRCHI_PACKAGE,
    method: 'phone',
    status: 'phone-surface-ready',
    codeRequested: false,
  })
  assert.deepEqual(
    android.calls.map(({ command }) => command),
    ['packages', 'launch', 'wait', 'wait', 'current', 'dump', 'tap', 'wait', 'current', 'dump'],
  )
  assert.deepEqual(android.calls[1].args, ['--serial', 'pixel-3', '--package', MIRCHI_PACKAGE])
  assert.deepEqual({ ...android.calls[6], args: withoutRejectRegex(android.calls[6].args) }, {
    command: 'tap',
    args: [
      '--serial', 'pixel-3',
      '--index', '0',
      '--text', 'SIGN IN WITH NUMBER',
      '--desc', '',
      '--id', '',
      '--class', 'android.widget.TextView',
      '--bounds', '[287,1516][794,1556]',
      '--unique', 'true',
    ],
  })
})

test('begin-login refuses duplicated or changed navigation before mutation', () => {
  const invalidInitialSurfaces = [
    [...INITIAL_PHONE_LOGIN_SURFACE, { ...INITIAL_PHONE_LOGIN_SURFACE[0] }],
    INITIAL_PHONE_LOGIN_SURFACE.map((element) => ({
      ...element,
      text: 'Sign in with number',
    })),
    INITIAL_PHONE_LOGIN_SURFACE.map((element) => ({
      ...element,
      bounds: { ...element.bounds, y1: 1515 },
    })),
  ]

  for (const surface of invalidInitialSurfaces) {
    const android = scriptedAndroid({ dumps: [surface] })
    assert.throws(
      () => execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
      /phone_login_navigation_not_exact_unique/,
    )
    assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
  }
})

test('begin-login refuses a changed or duplicated phone form after navigation', () => {
  const invalidPhoneSurfaces = [
    [...PHONE_SURFACE, { ...PHONE_SURFACE[0] }],
    PHONE_SURFACE.map((element, index) => index === 0
      ? { ...element, resourceId: 'com.dating.mirchi:id/etNumberChanged' }
      : element),
    PHONE_SURFACE.map((element, index) => index === 0
      ? { ...element, bounds: { ...element.bounds, x1: 491 } }
      : element),
    [...PHONE_SURFACE, { ...PHONE_SURFACE[2] }],
    PHONE_SURFACE.map((element, index) => index === 2
      ? { ...element, className: 'android.widget.Button' }
      : element),
    PHONE_SURFACE.map((element, index) => index === 1
      ? { ...element, text: 'CA +1' }
      : element),
  ]

  for (const surface of invalidPhoneSurfaces) {
    const android = scriptedAndroid({
      dumps: [INITIAL_PHONE_LOGIN_SURFACE, surface],
      currents: [
        {
          ok: true,
          serial: 'pixel-3',
          focus: 'mCurrentFocus=Window{1 u0 com.dating.mirchi/com.dating.mirchi.LoginActivity}',
        },
        {
          ok: true,
          serial: 'pixel-3',
          focus: 'mCurrentFocus=Window{1 u0 com.dating.mirchi/com.dating.mirchi.activity.LoginWithNumberActivity}',
        },
      ],
    })
    assert.throws(
      () => execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
      /phone_surface_not_exact_unique/,
    )
    assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  }
})

test('fill-phone accepts one stdin JSON phone and rejects CLI or malformed secret input without disclosure', () => {
  assert.deepEqual(parseOptions(['fill-phone', '--serial', 'pixel-3']), {
    command: 'fill-phone',
    serial: 'pixel-3',
  })

  const cliSecret = '5125550199-cli-secret'
  assert.throws(
    () => parseOptions(['fill-phone', '--phone', cliSecret]),
    (error) => {
      assert.match(error.message, /fill_phone_options/)
      assert.doesNotMatch(error.message, new RegExp(cliSecret))
      return true
    },
  )

  const privatePhone = '5125550199-private'
  for (const input of [
    '',
    `not-json-${privatePhone}`,
    `${JSON.stringify({ phone: privatePhone })}\n${JSON.stringify({ phone: privatePhone })}`,
    JSON.stringify({ phone: privatePhone, extra: true }),
    JSON.stringify({ phone: '' }),
    JSON.stringify({ phone: `${privatePhone}\nsecond-line` }),
    JSON.stringify([privatePhone]),
  ]) {
    const android = scriptedAndroid()
    assert.throws(
      () => execute(parseOptions(['fill-phone']), android.invoke, input),
      (error) => {
        assert.equal(error.message, 'phone_input_invalid')
        assert.doesNotMatch(error.message, new RegExp(privatePhone))
        return true
      },
    )
    assert.deepEqual(android.calls, [])
  }
})

test('fill-phone CLI reads its JSON phone only from stdin and redacts it before child invocation', () => {
  const phone = '5125550199-cli-private'
  const result = spawnSync(
    process.execPath,
    [fileURLToPath(new URL('../cli/mirchi.mjs', import.meta.url)), 'fill-phone'],
    {
      encoding: 'utf8',
      env: { ...process.env, PATH: '' },
      input: JSON.stringify({ phone }),
    },
  )

  assert.equal(result.status, 1)
  const output = JSON.parse(result.stdout)
  assert.equal(output.ok, false)
  assert.equal(output.error, 'android_packages_failed')
  assert.match(output.usage, /begin-login\|fill-phone\|request-code/)
  assert.doesNotMatch(`${result.stdout}\n${result.stderr}`, new RegExp(phone))
})

test('fill-phone guarded-taps the exact field, types through core stdin, and never requests a code', () => {
  const phone = '5125550199-private'
  const filledPhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 0 ? { ...element, text: phone } : element
  ))
  const android = scriptedAndroid({
    dumps: [PHONE_SURFACE, PHONE_SURFACE, filledPhoneSurface],
  })

  const result = execute(
    parseOptions(['fill-phone', '--serial', 'pixel-3']),
    android.invoke,
    JSON.stringify({ phone }),
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'fill-phone',
    id: 'mirchi',
    name: 'Mirchi',
    serial: 'pixel-3',
    package: MIRCHI_PACKAGE,
    status: 'phone-filled',
    codeRequested: false,
  })
  assert.doesNotMatch(JSON.stringify(result), new RegExp(phone))
  assert.deepEqual(withoutTapRejectGuards(android.calls), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', MIRCHI_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '0',
        '--text', '1234567890',
        '--desc', '',
        '--id', 'com.dating.mirchi:id/etNumber',
        '--class', 'android.widget.EditText',
        '--bounds', '[492,537][1014,644]',
        '--unique', 'true',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    { command: 'type-stdin', args: ['--serial', 'pixel-3'], input: phone },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
})

test('guarded Mirchi taps require generic fresh-dump rejection of every unsafe category', () => {
  const phone = '5125550199-private'
  const filledPhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 0 ? { ...element, text: phone } : element
  ))
  const android = scriptedAndroid({
    dumps: [PHONE_SURFACE, PHONE_SURFACE, filledPhoneSurface],
  })

  execute(
    parseOptions(['fill-phone', '--serial', 'pixel-3']),
    android.invoke,
    JSON.stringify({ phone }),
  )

  const tap = android.calls.find(({ command }) => command === 'tap')
  const guards = tap.args.filter((value, index) => tap.args[index - 1] === '--reject-regex')
  assert.equal(guards.length, 8)
  assert.ok(guards.some((pattern) => pattern.includes('continue (?:as|with)')))
  assert.ok(guards.some((pattern) => pattern.includes('permissioncontroller')))
  assert.ok(guards.some((pattern) => pattern.includes('captcha')))
})

test('fill-phone refuses an already populated phone field instead of appending', () => {
  const populatedPhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 0 ? { ...element, text: 'already-populated-private-phone' } : element
  ))
  const android = scriptedAndroid({ dumps: [populatedPhoneSurface] })

  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      android.invoke,
      JSON.stringify({ phone: 'new-private-phone' }),
    ),
    /phone_surface_not_exact_unique/,
  )
  assert.equal(android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
})

test('fill-phone stops on unsafe auth, permission, purchase, profile, or social surfaces', () => {
  for (const [label, category] of [
    ['Choose an account', 'provider_or_account'],
    ['Continue as Adithya', 'provider_or_account'],
    ['Continue with Google', 'provider_or_account'],
    ['Create a passkey', 'passkey_or_identity'],
    ['Enter verification code', 'two_factor'],
    ["I'm not a robot CAPTCHA", 'captcha'],
    ['Allow Mirchi to access your contacts', 'permission'],
    ['Complete purchase', 'purchase'],
    ['Create your profile', 'profile'],
    ['Connect your Instagram', 'social'],
    ['Add your Instagram', 'social'],
  ]) {
    const unsafeSurface = [
      ...PHONE_SURFACE,
      { text: label, desc: '', resourceId: '', className: 'android.widget.TextView' },
    ]
    const android = scriptedAndroid({ dumps: [unsafeSurface] })
    assert.throws(
      () => execute(
        parseOptions(['fill-phone']),
        android.invoke,
        JSON.stringify({ phone: '5125550199-private' }),
      ),
      new RegExp(`unsafe_auth_surface: ${category}`),
    )
    assert.equal(android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
  }
})

test('fill-phone requires the exact Mirchi foreground package', () => {
  for (const focus of [
    'mCurrentFocus=Window{1 u0 com.google.android.gms/.auth.uiflows.minutemaid.MinuteMaidActivity}',
    'mCurrentFocus=Window{1 u0 com.dating.mirchi.helper/.LoginActivity}',
  ]) {
    const android = scriptedAndroid({
      currents: [{ ok: true, serial: 'pixel-3', focus }],
    })
    assert.throws(
      () => execute(
        parseOptions(['fill-phone']),
        android.invoke,
        JSON.stringify({ phone: '5125550199-private' }),
      ),
      /mirchi_not_in_foreground/,
    )
    assert.equal(android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
  }
})

test('fill-phone stops before typing if an unsafe surface appears after the field tap', () => {
  const unsafeAfterTap = [
    ...PHONE_SURFACE,
    {
      text: 'Allow Mirchi to access your contacts',
      desc: '',
      resourceId: '',
      className: 'android.widget.TextView',
    },
  ]
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE, unsafeAfterTap] })

  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      android.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /unsafe_auth_surface: permission/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.equal(android.calls.some(({ command }) => command === 'type-stdin'), false)
})

test('fill-phone stops before typing when the final guarded field fingerprint is refused', () => {
  const android = scriptedAndroid({
    overrides: {
      tap: () => ({ ok: false, error: 'element_not_unique' }),
    },
  })

  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      android.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /android_tap_failed/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.equal(android.calls.some(({ command }) => command === 'type-stdin'), false)
})

test('fill-phone redacts the phone and child failure details', () => {
  const phone = '5125550199-private'
  const android = scriptedAndroid({
    dumps: [PHONE_SURFACE, PHONE_SURFACE],
    overrides: {
      'type-stdin': ({ input }) => ({ ok: false, error: `adb rejected ${input}` }),
    },
  })

  assert.throws(
    () => execute(parseOptions(['fill-phone']), android.invoke, JSON.stringify({ phone })),
    (error) => {
      assert.equal(error.message, 'android_type_stdin_failed')
      assert.doesNotMatch(error.message, new RegExp(`${phone}|adb rejected`))
      return true
    },
  )
})

test('request-code requires exact explicit confirmation and never runs implicitly', () => {
  for (const argv of [
    ['request-code'],
    ['request-code', '--confirm', 'yes'],
  ]) {
    assert.throws(() => parseOptions(argv), /request_confirmation_required/)
  }

  const bypass = scriptedAndroid()
  assert.throws(
    () => execute({ command: 'request-code', serial: 'pixel-3' }, bypass.invoke),
    /request_confirmation_required/,
  )
  assert.deepEqual(bypass.calls, [])
})

test('request-code guards the exact observed Continue control, then freshly inspects without claiming authentication', () => {
  const android = scriptedAndroid({
    dumps: [
      PHONE_SURFACE,
      [{
        text: 'Enter verification code',
        desc: '',
        resourceId: '',
        className: 'android.widget.TextView',
      }],
    ],
  })

  const result = execute(
    parseOptions(['request-code', '--confirm', 'request', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'request-code',
    id: 'mirchi',
    name: 'Mirchi',
    serial: 'pixel-3',
    package: MIRCHI_PACKAGE,
    status: 'submission-observed',
    authentication: 'unverified',
  })
  assert.deepEqual(withoutTapRejectGuards(android.calls), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', MIRCHI_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '2',
        '--text', '',
        '--desc', '',
        '--id', 'com.dating.mirchi:id/btnContinue',
        '--class', 'android.widget.ImageView',
        '--bounds', '[659,848][1014,986]',
        '--unique', 'true',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
  assert.equal(Object.hasOwn(result, 'authenticated'), false)
})

test('request-code rejects a neutral code label combined with an explicit two-factor warning', () => {
  const android = scriptedAndroid({
    dumps: [
      PHONE_SURFACE,
      [
        {
          text: 'Enter verification code',
          desc: '',
          resourceId: '',
          className: 'android.widget.TextView',
        },
        {
          text: 'Two-factor authentication required',
          desc: '',
          resourceId: '',
          className: 'android.widget.TextView',
        },
      ],
    ],
  })

  assert.throws(
    () => execute(
      parseOptions(['request-code', '--confirm', 'request']),
      android.invoke,
    ),
    /unsafe_auth_surface: two_factor/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
})

test('request-code refuses a post-tap provider focus handoff', () => {
  const android = scriptedAndroid({
    dumps: [PHONE_SURFACE],
    currents: [
      {
        ok: true,
        serial: 'pixel-3',
        focus: 'mCurrentFocus=Window{1 u0 com.dating.mirchi/com.dating.mirchi.activity.LoginWithNumberActivity}',
      },
      {
        ok: true,
        serial: 'pixel-3',
        focus: 'mCurrentFocus=Window{2 u0 com.google.android.gms/.auth.uiflows.minutemaid.MinuteMaidActivity}',
      },
    ],
  })

  assert.throws(
    () => execute(
      parseOptions(['request-code', '--confirm', 'request']),
      android.invoke,
    ),
    /mirchi_not_in_foreground/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.equal(android.calls.filter(({ command }) => command === 'dump').length, 1)
})

test('request-code refuses every unsafe category appearing after the guarded tap', () => {
  for (const [label, category] of [
    ['Choose an account', 'provider_or_account'],
    ['Allow Mirchi to access your contacts', 'permission'],
    ['Create a passkey', 'passkey_or_identity'],
    ['Two-factor authentication required', 'two_factor'],
    ["I'm not a robot CAPTCHA", 'captcha'],
    ['Complete purchase', 'purchase'],
    ['Create your profile', 'profile'],
    ['Connect your Instagram', 'social'],
  ]) {
    const postRequestSurface = [
      {
        text: label,
        desc: '',
        resourceId: '',
        className: 'android.widget.TextView',
      },
    ]
    const android = scriptedAndroid({ dumps: [PHONE_SURFACE, postRequestSurface] })

    assert.throws(
      () => execute(
        parseOptions(['request-code', '--confirm', 'request']),
        android.invoke,
      ),
      new RegExp(`unsafe_auth_surface: ${category}`),
    )
    assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
    assert.equal(android.calls.some(({ command }) => command === 'type-stdin'), false)
  }
})

test('request-code refuses a malformed post-tap observation', () => {
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE, undefined] })

  assert.throws(
    () => execute(
      parseOptions(['request-code', '--confirm', 'request']),
      android.invoke,
    ),
    /post_request_surface_invalid/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
})

test('request-code refuses a changed or duplicated form before mutation', () => {
  const invalidPhoneSurfaces = [
    [...PHONE_SURFACE, { ...PHONE_SURFACE[0] }],
    PHONE_SURFACE.map((element, index) => index === 0
      ? { ...element, className: 'android.widget.TextView' }
      : element),
    [...PHONE_SURFACE, { ...PHONE_SURFACE[2] }],
    PHONE_SURFACE.map((element, index) => index === 2
      ? { ...element, bounds: { ...element.bounds, y1: 849 } }
      : element),
  ]

  for (const surface of invalidPhoneSurfaces) {
    const android = scriptedAndroid({ dumps: [surface] })
    assert.throws(
      () => execute(
        parseOptions(['request-code', '--confirm', 'request']),
        android.invoke,
      ),
      /phone_surface_not_exact_unique/,
    )
    assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
  }
})

test('request-code stops when the final guarded Continue fingerprint is refused', () => {
  const android = scriptedAndroid({
    overrides: {
      tap: () => ({ ok: false, error: 'element_not_unique' }),
    },
  })

  assert.throws(
    () => execute(
      parseOptions(['request-code', '--confirm', 'request']),
      android.invoke,
    ),
    /android_tap_failed/,
  )
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'current', 'dump', 'tap'])
})

test('Mirchi check identifies only the exact Mirchi package', () => {
  const android = fakeAndroid()
  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'mirchi',
    name: 'Mirchi',
    serial: 'pixel-3',
    package: 'com.dating.mirchi',
  })
  assert.equal(MIRCHI_PACKAGE, 'com.dating.mirchi')
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', 'com.dating.mirchi'] }])

  const similarPackage = fakeAndroid({
    packages: { ok: true, serial: 'pixel-3', packages: ['com.dating.mirchi.beta'] },
  })
  assert.throws(() => execute(parseOptions(['check']), similarPackage.invoke), /mirchi_not_installed/)
  assert.deepEqual(similarPackage.calls, [{ command: 'packages', args: ['--package', 'com.dating.mirchi'] }])
})

test('Mirchi open launches then refreshes the initial visible state', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['open', '--serial', 'pixel-3']), android.invoke)
  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'Mirchi')
  assert.deepEqual(result.elements, [{ text: 'Initial surface' }])
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'launch', 'current', 'dump'])
  assert.deepEqual(android.calls[1].args, ['--serial', 'pixel-3', '--package', 'com.dating.mirchi'])
})

test('Mirchi inspect refreshes state without launching the app', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['inspect', '--serial', 'pixel-3']), android.invoke)
  assert.equal(result.action, 'inspect')
  assert.equal(result.package, 'com.dating.mirchi')
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'current', 'dump'])
})

test('Mirchi screenshot output is restricted to its runtime directory', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['screenshot', '--out', 'initial.png']), android.invoke)
  const output = android.calls.at(-1).args.at(-1)
  assert.equal(result.action, 'screenshot')
  assert.equal(isAbsolute(output), true)
  assert.equal(relative(RUNTIME_DIRECTORY, output).startsWith('..'), false)
  assert.throws(
    () => execute(parseOptions(['screenshot', '--out', '/tmp/mirchi.png']), fakeAndroid().invoke),
    /unsafe_screenshot_path/,
  )
})

test('the narrow command surface rejects account and engagement workflows', () => {
  for (const command of [
    'login',
    'authenticate',
    'select-account',
    'edit-profile',
    'message',
    'engage',
    'purchase',
  ]) {
    assert.throws(() => parseOptions([command]), new RegExp(`unknown_command: ${command}`))
  }
})
