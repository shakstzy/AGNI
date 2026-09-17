import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { isAbsolute, relative } from 'node:path'
import test from 'node:test'
import {
  HINGE_PACKAGE,
  RUNTIME_DIRECTORY,
  execute,
  parseOptions,
} from '../cli/hinge.mjs'

const adapterDirectory = new URL('..', import.meta.url)

function read(relativePath) {
  return readFileSync(new URL(relativePath, adapterDirectory), 'utf8')
}

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [HINGE_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'Hinge' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Welcome' }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: HINGE_PACKAGE },
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
    text: 'Sign in with Phone Number',
    desc: '',
    resourceId: '',
    className: 'android.widget.TextView',
    bounds: { x1: 265, y1: 1678, x2: 815, y2: 1732, x: 540, y: 1705 },
  },
]

const PHONE_SURFACE = [
  {
    text: "What's your phone number?",
    desc: '',
    resourceId: '',
    className: 'android.widget.TextView',
    bounds: { x1: 94, y1: 209, x2: 986, y2: 414, x: 540, y: 312 },
  },
  {
    text: 'United States 1',
    desc: '',
    resourceId: '',
    className: 'android.widget.Button',
    bounds: { x1: 55, y1: 691, x2: 438, y2: 856, x: 247, y: 774 },
  },
  {
    text: '',
    desc: '',
    resourceId: '',
    className: 'android.widget.EditText',
    bounds: { x1: 460, y1: 691, x2: 1025, y2: 856, x: 743, y: 774 },
  },
  {
    text: 'Phone number',
    desc: '',
    resourceId: '',
    className: 'android.widget.TextView',
    bounds: { x1: 515, y1: 744, x2: 841, y2: 803, x: 678, y: 774 },
  },
  {
    text: 'Continue',
    desc: '',
    resourceId: '',
    className: 'android.widget.TextView',
    bounds: { x1: 448, y1: 1761, x2: 633, y2: 1813, x: 541, y: 1787 },
  },
  {
    text: '',
    desc: '',
    resourceId: '',
    className: 'android.widget.Button',
    bounds: { x1: 375, y1: 1722, x2: 705, y2: 1852, x: 540, y: 1787 },
  },
  {
    text: 'Hinge will send you a text with a verification code. Message and data rates may apply.',
    desc: '',
    resourceId: '',
    className: 'android.widget.TextView',
    bounds: { x1: 44, y1: 1907, x2: 1036, y2: 1973, x: 540, y: 1940 },
  },
]

const FINAL_TAP_REJECT_PATTERNS = [
  /\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue as\b|\bcontinue with (?:google|facebook|apple)\b|\buse another account\b|\baccount owner\b|\bgoogle account\b|accounts\.google\.com/.source,
  /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/.source,
  /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/.source,
  /\btwo[- ]factor\b|\b2[- ]step\b|\b2fa\b/.source,
  /captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge/.source,
  /\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b/.source,
  /\bcreate (?:your )?profile\b|\bedit (?:your )?profile\b|\bcomplete (?:your )?profile\b|\bprofile setup\b/.source,
  /\b(?:connect|link|add) (?:your )?(?:instagram|facebook|spotify|social)\b/.source,
  /\benter (?:the )?(?:verification|authentication|security)?\s*code\b/.source,
]
const FINAL_TAP_REJECT_ARGS = FINAL_TAP_REJECT_PATTERNS.flatMap((pattern) => ['--reject-regex', pattern])

function scriptedAndroid({ dumps = [PHONE_SURFACE], currents, overrides = {} } = {}) {
  const calls = []
  let dumpIndex = 0
  let currentIndex = 0
  let waitIndex = 0
  const currentResults = currents || [
    { ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 co.hinge.app/co.hinge.app.LoginActivity}' },
  ]
  return {
    calls,
    invoke(command, args, input) {
      calls.push({ command, args, ...(input === undefined ? {} : { input }) })
      if (overrides[command]) return overrides[command]({ command, args, input, calls })
      if (command === 'packages') {
        return { ok: true, serial: 'pixel-3', packages: [HINGE_PACKAGE] }
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
      if (command === 'launch') return { ok: true, serial: 'pixel-3', action: 'launch', package: HINGE_PACKAGE }
      if (command === 'wait') {
        waitIndex += 1
        return waitIndex === 1
          ? { ok: false, error: 'wait_timeout: element_not_found' }
          : { ok: true, serial: 'pixel-3', action: 'wait' }
      }
      if (command === 'type-stdin') return { ok: true, serial: 'pixel-3', action: 'type-stdin' }
      throw new Error(`unexpected_android_command: ${command}`)
    },
  }
}

test('Hinge adapter documents its bounded, non-engagement contract', () => {
  assert.ok(existsSync(new URL('ADAPTER.md', adapterDirectory)))
  const adapter = read('ADAPTER.md')
  assert.match(adapter, /co\.hinge\.app/)
  assert.match(adapter, /hinge\.mjs check/)
  assert.match(adapter, /hinge\.mjs inspect/)
  assert.match(adapter, /hinge\.mjs open/)
  assert.match(adapter, /hinge\.mjs screenshot/)
  assert.match(adapter, /runtime-only/i)
  assert.match(adapter, /login|authentication|profile|engagement|messag|purchas/i)
})

test('Hinge check identifies only the Hinge package', () => {
  const android = fakeAndroid()
  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'hinge',
    name: 'Hinge',
    serial: 'pixel-3',
    package: HINGE_PACKAGE,
  })
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', HINGE_PACKAGE] }])
})

test('Hinge open launches then refreshes the initial visible state', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['open', '--serial', 'pixel-3']), android.invoke)
  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'Hinge')
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'launch', 'current', 'dump'])
  assert.deepEqual(android.calls[1].args, ['--serial', 'pixel-3', '--package', HINGE_PACKAGE])
})

test('Hinge screenshot output is restricted to its runtime directory', () => {
  const android = fakeAndroid()
  execute(parseOptions(['screenshot', '--out', 'initial.png']), android.invoke)
  const output = android.calls.at(-1).args.at(-1)
  assert.equal(isAbsolute(output), true)
  assert.equal(relative(RUNTIME_DIRECTORY, output).startsWith('..'), false)
  assert.throws(() => execute(parseOptions(['screenshot', '--out', '/tmp/hinge.png']), fakeAndroid().invoke), /unsafe_screenshot_path/)
})

test('begin-login supports only the exact phone method and rejects a Google route', () => {
  assert.deepEqual(parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']), {
    command: 'begin-login',
    method: 'phone',
    serial: 'pixel-3',
  })
  assert.throws(() => parseOptions(['begin-login']), /phone_login_method_required/)
  assert.throws(() => parseOptions(['begin-login', '--method', 'google']), /unsupported_login_method/)
})

test('begin-login navigates through the exact observed phone selector and freshly proves the phone surface', () => {
  const android = scriptedAndroid({ dumps: [INITIAL_PHONE_LOGIN_SURFACE, PHONE_SURFACE] })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'begin-login',
    id: 'hinge',
    name: 'Hinge',
    serial: 'pixel-3',
    package: HINGE_PACKAGE,
    method: 'phone',
    status: 'phone-surface-ready',
    codeRequested: false,
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', HINGE_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', HINGE_PACKAGE] },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--text', "What's your phone number?",
        '--id', '',
        '--class', 'android.widget.TextView',
        '--bounds', '[94,209][986,414]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--text', 'Sign in with Phone Number',
        '--id', '',
        '--class', 'android.widget.TextView',
        '--bounds', '[265,1678][815,1732]',
        '--unique', 'true',
        '--timeout-ms', '15000',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '0',
        '--text', 'Sign in with Phone Number',
        '--id', '',
        '--class', 'android.widget.TextView',
        '--bounds', '[265,1678][815,1732]',
        '--unique', 'true',
        ...FINAL_TAP_REJECT_ARGS,
      ],
    },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--text', "What's your phone number?",
        '--id', '',
        '--class', 'android.widget.TextView',
        '--bounds', '[94,209][986,414]',
        '--unique', 'true',
        '--timeout-ms', '15000',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('begin-login launches Hinge and returns ready when it resumes the exact empty phone form', () => {
  const android = scriptedAndroid({
    dumps: [PHONE_SURFACE],
    overrides: {
      launch: () => ({ ok: true, serial: 'pixel-3', action: 'launch', package: HINGE_PACKAGE }),
      wait: () => ({ ok: true, serial: 'pixel-3', action: 'wait' }),
    },
  })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.equal(result.status, 'phone-surface-ready')
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', HINGE_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', HINGE_PACKAGE] },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--text', "What's your phone number?",
        '--id', '',
        '--class', 'android.widget.TextView',
        '--bounds', '[94,209][986,414]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
  assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
})

test('begin-login launches, waits through the exact initial anchor, then waits for the exact phone form', () => {
  let waitCount = 0
  const android = scriptedAndroid({
    dumps: [INITIAL_PHONE_LOGIN_SURFACE, PHONE_SURFACE],
    overrides: {
      launch: () => ({ ok: true, serial: 'pixel-3', action: 'launch', package: HINGE_PACKAGE }),
      wait: () => {
        waitCount += 1
        return waitCount === 1
          ? { ok: false, error: 'wait_timeout: element_not_found' }
          : { ok: true, serial: 'pixel-3', action: 'wait' }
      },
    },
  })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.equal(result.status, 'phone-surface-ready')
  assert.deepEqual(android.calls.map(({ command }) => command), [
    'packages', 'launch', 'wait', 'wait', 'current', 'dump', 'tap', 'wait', 'current', 'dump',
  ])
  assert.deepEqual(android.calls[3].args, [
    '--serial', 'pixel-3',
    '--text', 'Sign in with Phone Number',
    '--id', '',
    '--class', 'android.widget.TextView',
    '--bounds', '[265,1678][815,1732]',
    '--unique', 'true',
    '--timeout-ms', '15000',
  ])
  assert.deepEqual(android.calls[6].args, [
    '--serial', 'pixel-3',
    '--index', '0',
    '--text', 'Sign in with Phone Number',
    '--id', '',
    '--class', 'android.widget.TextView',
    '--bounds', '[265,1678][815,1732]',
    '--unique', 'true',
    ...FINAL_TAP_REJECT_ARGS,
  ])
  assert.deepEqual(android.calls[7].args, [
    '--serial', 'pixel-3',
    '--text', "What's your phone number?",
    '--id', '',
    '--class', 'android.widget.TextView',
    '--bounds', '[94,209][986,414]',
    '--unique', 'true',
    '--timeout-ms', '15000',
  ])
})

test('begin-login fails closed when the observed navigation control is duplicated or moved', () => {
  const invalidInitialSurfaces = [
    [...INITIAL_PHONE_LOGIN_SURFACE, { ...INITIAL_PHONE_LOGIN_SURFACE[0] }],
    INITIAL_PHONE_LOGIN_SURFACE.map((element) => ({
      ...element,
      bounds: { ...element.bounds, y1: 1600, y2: 1654 },
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

test('every guarded Hinge tap passes the full unsafe surface set to the generic final guard', () => {
  const begin = scriptedAndroid({ dumps: [INITIAL_PHONE_LOGIN_SURFACE, PHONE_SURFACE] })
  execute(parseOptions(['begin-login', '--method', 'phone']), begin.invoke)

  const phone = '5125550199-private'
  const filledPhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 2 ? { ...element, text: phone } : element
  ))
  const fill = scriptedAndroid({ dumps: [PHONE_SURFACE, PHONE_SURFACE, filledPhoneSurface] })
  execute(parseOptions(['fill-phone']), fill.invoke, JSON.stringify({ phone }))

  const request = scriptedAndroid({ dumps: [PHONE_SURFACE, [{ text: 'Enter verification code' }]] })
  execute(parseOptions(['request-code', '--confirm', 'request']), request.invoke)

  for (const android of [begin, fill, request]) {
    const taps = android.calls.filter(({ command }) => command === 'tap')
    assert.equal(taps.length, 1)
    const patterns = taps[0].args.reduce((values, argument, index, args) => (
      argument === '--reject-regex' ? [...values, args[index + 1]] : values
    ), [])
    assert.deepEqual(patterns, FINAL_TAP_REJECT_PATTERNS)
  }
})

test('fill-phone accepts one stdin JSON phone value and rejects CLI or malformed secret input without disclosure', () => {
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

test('fill-phone uses one guarded field tap and core type-stdin without requesting a code', () => {
  const phone = '5125550199-private'
  const filledPhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 2 ? { ...element, text: phone } : element
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
    id: 'hinge',
    name: 'Hinge',
    serial: 'pixel-3',
    package: HINGE_PACKAGE,
    status: 'phone-filled',
    codeRequested: false,
  })
  assert.doesNotMatch(JSON.stringify(result), new RegExp(phone))
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', HINGE_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '2',
        '--text', '',
        '--desc', '',
        '--id', '',
        '--class', 'android.widget.EditText',
        '--bounds', '[460,691][1025,856]',
        '--unique', 'true',
        ...FINAL_TAP_REJECT_ARGS,
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

test('fill-phone refuses an already populated phone field instead of appending', () => {
  const populatedPhoneSurface = PHONE_SURFACE.map((element, index) => (
    index === 2 ? { ...element, text: 'already-populated-private-phone' } : element
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

test('phone actions fail closed on duplicate or moved observed controls before mutation', () => {
  const invalidPhoneSurfaces = [
    [...PHONE_SURFACE, { ...PHONE_SURFACE[2] }],
    PHONE_SURFACE.map((element, index) => index === 2
      ? { ...element, bounds: { ...element.bounds, x1: 461 } }
      : element),
    [...PHONE_SURFACE, { ...PHONE_SURFACE[5] }],
    PHONE_SURFACE.map((element, index) => index === 5
      ? { ...element, bounds: { ...element.bounds, y1: 1723 } }
      : element),
  ]

  for (const surface of invalidPhoneSurfaces) {
    for (const [options, input] of [
      [parseOptions(['fill-phone']), JSON.stringify({ phone: '5125550199-private' })],
      [parseOptions(['request-code', '--confirm', 'request']), undefined],
    ]) {
      const android = scriptedAndroid({ dumps: [surface] })
      assert.throws(
        () => execute(options, android.invoke, input),
        /phone_surface_not_exact_unique/,
      )
      assert.equal(android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
    }
  }
})

test('phone actions stop on provider, account, identity, challenge, permission, purchase, profile, or social surfaces', () => {
  for (const [label, category] of [
    ['Choose an account', 'provider_or_account'],
    ['Continue as Adithya', 'provider_or_account'],
    ['Continue with Google', 'provider_or_account'],
    ['Create a passkey', 'passkey_or_identity'],
    ['Enter verification code', 'two_factor'],
    ["I'm not a robot CAPTCHA", 'captcha'],
    ['Allow Hinge to access your contacts', 'permission'],
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

  const wrongFocus = scriptedAndroid({
    currents: [{ ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.google.android.gms/.auth.uiflows.minutemaid.MinuteMaidActivity}' }],
  })
  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      wrongFocus.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /hinge_not_in_foreground/,
  )
  assert.equal(wrongFocus.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)

  const packagePrefixFocus = scriptedAndroid({
    currents: [{ ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 co.hinge.app.helper/.LoginActivity}' }],
  })
  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      packagePrefixFocus.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /hinge_not_in_foreground/,
  )
  assert.equal(packagePrefixFocus.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
})

test('fill-phone stops before typing if an unsafe handoff appears after the guarded field tap', () => {
  const unsafeAfterTap = [
    ...PHONE_SURFACE,
    { text: 'Allow Hinge to access your contacts', desc: '', resourceId: '', className: 'android.widget.TextView' },
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

test('request-code guards the exact Continue button, permits neutral Hinge code entry, and makes no authentication claim', () => {
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE, [{ text: 'Enter verification code' }]] })

  const result = execute(
    parseOptions(['request-code', '--confirm', 'request', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'request-code',
    id: 'hinge',
    name: 'Hinge',
    serial: 'pixel-3',
    package: HINGE_PACKAGE,
    status: 'submission-observed',
    authentication: 'unverified',
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', HINGE_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '5',
        '--text', '',
        '--desc', '',
        '--id', '',
        '--class', 'android.widget.Button',
        '--bounds', '[375,1722][705,1852]',
        '--unique', 'true',
        ...FINAL_TAP_REJECT_ARGS,
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('request-code fails redacted after the final tap on unsafe account, identity, challenge, permission, purchase, or profile handoffs', () => {
  for (const [label, category] of [
    ['Continue with Google private-provider-detail', 'provider_or_account'],
    ['Create a passkey private-identity-detail', 'passkey_or_identity'],
    ['Two-factor authentication private-two-factor-detail', 'two_factor'],
    ['CAPTCHA private-challenge-detail', 'captcha'],
    ['Allow Hinge to access your contacts private-permission-detail', 'permission'],
    ['Complete purchase private-purchase-detail', 'purchase'],
    ['Create your profile private-profile-detail', 'profile'],
  ]) {
    const android = scriptedAndroid({
      dumps: [PHONE_SURFACE, [{ text: label, desc: '', resourceId: '', className: 'android.widget.TextView' }]],
    })

    assert.throws(
      () => execute(
        parseOptions(['request-code', '--confirm', 'request']),
        android.invoke,
      ),
      (error) => {
        assert.equal(error.message, `unsafe_auth_surface: ${category}`)
        assert.doesNotMatch(error.message, /private-/)
        return true
      },
    )
    assert.deepEqual(android.calls.map(({ command }) => command), [
      'packages', 'current', 'dump', 'tap', 'current', 'dump',
    ])
  }
})

test('request-code stops after the final tap when Hinge is no longer the exact foreground package', () => {
  const android = scriptedAndroid({
    currents: [
      { ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 co.hinge.app/co.hinge.app.LoginActivity}' },
      { ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.google.android.gms/.auth.uiflows.minutemaid.MinuteMaidActivity}' },
    ],
  })

  assert.throws(
    () => execute(
      parseOptions(['request-code', '--confirm', 'request']),
      android.invoke,
    ),
    /hinge_not_in_foreground/,
  )
  assert.deepEqual(android.calls.map(({ command }) => command), [
    'packages', 'current', 'dump', 'tap', 'current',
  ])
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
