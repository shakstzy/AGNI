import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { isAbsolute, relative } from 'node:path'
import test from 'node:test'
import {
  BUMBLE_PACKAGE,
  RUNTIME_DIRECTORY,
  execute,
  parseOptions,
} from '../cli/bumble.mjs'

const adapterDirectory = new URL('..', import.meta.url)

function read(relativePath) {
  return readFileSync(new URL(relativePath, adapterDirectory), 'utf8')
}

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [BUMBLE_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'Bumble' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Welcome' }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: BUMBLE_PACKAGE },
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

function element({ desc = '', text = '', resourceId = '', className, bounds }) {
  const [x1, y1, x2, y2] = bounds
  return {
    text,
    desc,
    resourceId,
    className,
    bounds: {
      x1,
      y1,
      x2,
      y2,
      x: Math.round((x1 + x2) / 2),
      y: Math.round((y1 + y2) / 2),
    },
  }
}

const ACCOUNT_NAVIGATION_SURFACE = [
  element({
    desc: 'I have an account',
    className: 'android.view.View',
    bounds: [55, 1702, 1025, 1834],
  }),
]

const OTHER_METHODS_SURFACE = [
  element({
    desc: 'Continue with other methods',
    className: 'android.view.View',
    bounds: [55, 1702, 1025, 1834],
  }),
]

const LOGIN_METHOD_SURFACE = [
  element({
    desc: 'Quick sign in',
    className: 'android.view.View',
    bounds: [55, 1174, 1025, 1306],
  }),
  element({
    desc: 'Continue with Facebook',
    className: 'android.view.View',
    bounds: [55, 1339, 1025, 1471],
  }),
  element({
    desc: 'Continue with Google',
    className: 'android.view.View',
    bounds: [55, 1504, 1025, 1636],
  }),
  element({
    desc: 'Use cell phone number',
    className: 'android.view.View',
    bounds: [55, 1669, 1025, 1801],
  }),
]

const PHONE_SURFACE = [
  element({
    resourceId: 'com.bumble.app:id/reg_input_edittext',
    className: 'android.widget.EditText',
    bounds: [325, 742, 1014, 869],
  }),
  element({
    desc: 'Continue',
    resourceId: 'com.bumble.app:id/reg_footer_button',
    className: 'android.widget.Button',
    bounds: [904, 1843, 1036, 1975],
  }),
]

const COMPACT_PHONE_SURFACE = PHONE_SURFACE.map((control, index) => (
  index === 1
    ? element({
      desc: 'Continue',
      resourceId: 'com.bumble.app:id/reg_footer_button',
      className: 'android.widget.Button',
      bounds: [904, 1039, 1036, 1171],
    })
    : control
))

function scriptedAndroid({ dumps = [PHONE_SURFACE], currents, waits, overrides = {} } = {}) {
  const calls = []
  let dumpIndex = 0
  let currentIndex = 0
  let waitIndex = 0
  const currentResults = currents || [
    {
      ok: true,
      serial: 'pixel-3',
      focus: 'mCurrentFocus=Window{1 u0 com.bumble.app/com.bumble.app.LoginActivity}',
    },
  ]
  const waitResults = waits || [
    { ok: true, serial: 'pixel-3', action: 'wait', waitedMs: 0, element: {} },
  ]
  return {
    calls,
    invoke(command, args, input) {
      calls.push({ command, args, ...(input === undefined ? {} : { input }) })
      if (overrides[command]) return overrides[command]({ command, args, input, calls })
      if (command === 'packages') {
        return { ok: true, serial: 'pixel-3', packages: [BUMBLE_PACKAGE] }
      }
      if (command === 'launch') {
        return { ok: true, serial: 'pixel-3', action: 'launch', package: BUMBLE_PACKAGE }
      }
      if (command === 'wait') {
        const result = waitResults[Math.min(waitIndex, waitResults.length - 1)]
        waitIndex += 1
        return result
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

function withoutFinalTapGuards(calls) {
  return calls.map((call) => (
    call.command !== 'tap'
      ? call
      : {
        ...call,
        args: call.args.filter((argument, index, args) => (
          argument !== '--reject-regex' && args[index - 1] !== '--reject-regex'
        )),
      }
  ))
}

test('Bumble adapter documents its bounded, non-engagement contract', () => {
  assert.ok(existsSync(new URL('ADAPTER.md', adapterDirectory)))
  const adapter = read('ADAPTER.md')
  assert.match(adapter, /com\.bumble\.app/)
  assert.match(adapter, /bumble\.mjs check/)
  assert.match(adapter, /bumble\.mjs inspect/)
  assert.match(adapter, /bumble\.mjs open/)
  assert.match(adapter, /bumble\.mjs screenshot/)
  assert.match(adapter, /runtime-only/i)
  assert.match(adapter, /login|authentication|profile|engagement|messag|purchas/i)
})

test('Bumble check identifies only the Bumble package', () => {
  const android = fakeAndroid()
  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'bumble',
    name: 'Bumble',
    serial: 'pixel-3',
    package: BUMBLE_PACKAGE,
  })
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', BUMBLE_PACKAGE] }])
})

test('Bumble open launches then refreshes the initial visible state', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['open', '--serial', 'pixel-3']), android.invoke)
  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'Bumble')
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'launch', 'current', 'dump'])
  assert.deepEqual(android.calls[1].args, ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE])
})

test('Bumble screenshot output is restricted to its runtime directory', () => {
  const android = fakeAndroid()
  execute(parseOptions(['screenshot', '--out', 'initial.png']), android.invoke)
  const output = android.calls.at(-1).args.at(-1)
  assert.equal(isAbsolute(output), true)
  assert.equal(relative(RUNTIME_DIRECTORY, output).startsWith('..'), false)
  assert.throws(() => execute(parseOptions(['screenshot', '--out', '/tmp/bumble.png']), fakeAndroid().invoke), /unsafe_screenshot_path/)
})

test('begin-login supports only the exact phone route', () => {
  assert.deepEqual(parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']), {
    command: 'begin-login',
    method: 'phone',
    serial: 'pixel-3',
  })
  assert.throws(() => parseOptions(['begin-login']), /phone_login_method_required/)
  for (const method of ['facebook', 'google', 'quick-sign-in']) {
    assert.throws(
      () => parseOptions(['begin-login', '--method', method]),
      /unsupported_login_method/,
    )
  }
})

test('begin-login launches and returns ready idempotently only for the exact empty phone form', () => {
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE] })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.equal(result.status, 'phone-surface-ready')
  assert.deepEqual(withoutFinalTapGuards(android.calls), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE] },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--desc', '',
        '--text', '',
        '--id', 'com.bumble.app:id/reg_input_edittext',
        '--class', 'android.widget.EditText',
        '--bounds', '[325,742][1014,869]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('begin-login accepts the exact live Bumble Continue footprint', () => {
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE] })

  assert.deepEqual(
    execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
    {
      ok: true,
      action: 'begin-login',
      id: 'bumble',
      name: 'Bumble',
      serial: 'pixel-3',
      package: BUMBLE_PACKAGE,
      method: 'phone',
      status: 'phone-surface-ready',
      codeRequested: false,
    },
  )
})

test('begin-login derives the exact current Bumble Continue footprint across verified layouts', () => {
  const android = scriptedAndroid({ dumps: [COMPACT_PHONE_SURFACE] })

  assert.deepEqual(
    execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
    {
      ok: true,
      action: 'begin-login',
      id: 'bumble',
      name: 'Bumble',
      serial: 'pixel-3',
      package: BUMBLE_PACKAGE,
      method: 'phone',
      status: 'phone-surface-ready',
      codeRequested: false,
    },
  )
})

test('begin-login performs the exact three-step phone route with fresh state after every tap', () => {
  const android = scriptedAndroid({
    dumps: [
      ACCOUNT_NAVIGATION_SURFACE,
      OTHER_METHODS_SURFACE,
      LOGIN_METHOD_SURFACE,
      PHONE_SURFACE,
    ],
    waits: [
      { ok: false, error: 'wait_timeout: element_not_found' },
      { ok: true, serial: 'pixel-3', action: 'wait', waitedMs: 0, element: {} },
    ],
  })

  const result = execute(
    parseOptions(['begin-login', '--method', 'phone', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'begin-login',
    id: 'bumble',
    name: 'Bumble',
    serial: 'pixel-3',
    package: BUMBLE_PACKAGE,
    method: 'phone',
    status: 'phone-surface-ready',
    codeRequested: false,
  })
  assert.deepEqual(withoutFinalTapGuards(android.calls), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE] },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--desc', '',
        '--text', '',
        '--id', 'com.bumble.app:id/reg_input_edittext',
        '--class', 'android.widget.EditText',
        '--bounds', '[325,742][1014,869]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--desc', 'I have an account',
        '--class', 'android.view.View',
        '--bounds', '[55,1702][1025,1834]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '0',
        '--desc', 'I have an account',
        '--class', 'android.view.View',
        '--bounds', '[55,1702][1025,1834]',
        '--unique', 'true',
      ],
    },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--desc', 'Continue with other methods',
        '--class', 'android.view.View',
        '--bounds', '[55,1702][1025,1834]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '0',
        '--desc', 'Continue with other methods',
        '--class', 'android.view.View',
        '--bounds', '[55,1702][1025,1834]',
        '--unique', 'true',
      ],
    },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--desc', 'Use cell phone number',
        '--class', 'android.view.View',
        '--bounds', '[55,1669][1025,1801]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '3',
        '--desc', 'Use cell phone number',
        '--class', 'android.view.View',
        '--bounds', '[55,1669][1025,1801]',
        '--unique', 'true',
      ],
    },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--desc', '',
        '--text', '',
        '--id', 'com.bumble.app:id/reg_input_edittext',
        '--class', 'android.widget.EditText',
        '--bounds', '[325,742][1014,869]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
  const tappedDescriptions = android.calls
    .filter(({ command }) => command === 'tap')
    .map(({ args }) => args[args.indexOf('--desc') + 1])
  assert.deepEqual(tappedDescriptions, [
    'I have an account',
    'Continue with other methods',
    'Use cell phone number',
  ])
  assert.equal(
    tappedDescriptions.some((description) => /Facebook|Google|Quick sign in/.test(description)),
    false,
  )
})

test('begin-login fails closed on changed or duplicate controls at every route step', () => {
  const routeCases = [
    {
      dumps: [[...ACCOUNT_NAVIGATION_SURFACE, { ...ACCOUNT_NAVIGATION_SURFACE[0] }]],
      expectedTaps: 0,
    },
    {
      dumps: [
        ACCOUNT_NAVIGATION_SURFACE,
        OTHER_METHODS_SURFACE.map((control) => ({
          ...control,
          bounds: { ...control.bounds, y1: 1701 },
        })),
      ],
      expectedTaps: 1,
    },
    {
      dumps: [
        ACCOUNT_NAVIGATION_SURFACE,
        OTHER_METHODS_SURFACE,
        [...LOGIN_METHOD_SURFACE, { ...LOGIN_METHOD_SURFACE[3] }],
      ],
      expectedTaps: 2,
    },
  ]

  for (const { dumps, expectedTaps } of routeCases) {
    const android = scriptedAndroid({
      dumps,
      waits: [
        { ok: false, error: 'wait_timeout: element_not_found' },
        { ok: true, serial: 'pixel-3', action: 'wait', waitedMs: 0, element: {} },
      ],
    })
    assert.throws(
      () => execute(parseOptions(['begin-login', '--method', 'phone']), android.invoke),
      /phone_login_navigation_not_exact_unique/,
    )
    assert.equal(
      android.calls.filter(({ command }) => command === 'tap').length,
      expectedTaps,
    )
  }
})

test('fill-phone accepts only one stdin JSON phone field and never accepts a CLI secret', () => {
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

test('fill-phone guards the exact observed field, uses core type-stdin, refreshes, and never requests', () => {
  const phone = '5125550199-private'
  const filledPhoneSurface = PHONE_SURFACE.map((control, index) => (
    index === 0 ? { ...control, text: phone } : control
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
    id: 'bumble',
    name: 'Bumble',
    serial: 'pixel-3',
    package: BUMBLE_PACKAGE,
    status: 'phone-filled',
    codeRequested: false,
  })
  assert.doesNotMatch(JSON.stringify(result), new RegExp(phone))
  assert.deepEqual(withoutFinalTapGuards(android.calls), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '0',
        '--desc', '',
        '--text', '',
        '--id', 'com.bumble.app:id/reg_input_edittext',
        '--class', 'android.widget.EditText',
        '--bounds', '[325,742][1014,869]',
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

test('fill-phone refuses an already populated phone field instead of appending', () => {
  const populatedSurface = PHONE_SURFACE.map((control, index) => (
    index === 0 ? { ...control, text: 'existing-private-phone' } : control
  ))
  const android = scriptedAndroid({ dumps: [populatedSurface] })

  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      android.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /phone_surface_not_exact_unique/,
  )
  assert.equal(
    android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)),
    false,
  )
})

test('phone actions fail closed on changed IDs, moved phone fields, or duplicate controls', () => {
  const invalidPhoneSurfaces = [
    PHONE_SURFACE.map((control, index) => index === 0
      ? { ...control, resourceId: 'com.bumble.app:id/changed_phone' }
      : control),
    [...PHONE_SURFACE, { ...PHONE_SURFACE[0] }],
    [...PHONE_SURFACE, { ...PHONE_SURFACE[1] }],
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
      assert.equal(
        android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)),
        false,
      )
    }
  }
})

test('phone-field and Continue final guards reject every stop class, including provider choices', () => {
  for (const label of [
    'Choose an account',
    'Continue with Google',
    'Continue with Facebook',
    'Continue with Apple',
    'Allow Bumble to access your contacts',
    'Create a passkey',
    'Enter verification code',
    "I'm not a robot CAPTCHA",
    'Complete purchase',
    'Create your profile',
    'Connect your Instagram',
  ]) {
    let matchedFinalGuard = false
    for (const [options, input, preventedAction] of [
      [parseOptions(['fill-phone']), JSON.stringify({ phone: '5125550199-private' }), 'type-stdin'],
      [parseOptions(['request-code', '--confirm', 'request']), undefined, 'post-submit'],
    ]) {
      const android = scriptedAndroid({
        overrides: {
          tap: ({ args }) => {
            const rejectPatterns = args
              .flatMap((argument, index) => argument === '--reject-regex' ? [args[index + 1]] : [])
            matchedFinalGuard = rejectPatterns.some((source) => new RegExp(source, 'i').test(label))
            return matchedFinalGuard
              ? { ok: false, error: 'tap_rejected_by_guard' }
              : { ok: true, serial: 'pixel-3', action: 'tap' }
          },
        },
      })

      assert.throws(
        () => execute(options, android.invoke, input),
        /android_tap_failed/,
      )
      assert.equal(matchedFinalGuard, true)
      assert.equal(
        preventedAction === 'type-stdin'
          ? android.calls.some(({ command }) => command === 'type-stdin')
          : android.calls.filter(({ command }) => command === 'current').length > 1,
        false,
      )
    }
  }
})

test('provider choices are excluded only from the exact cell-phone route tap', () => {
  for (const label of [
    'Continue with Google',
    'Continue with Facebook',
    'Continue with Apple',
  ]) {
    const android = scriptedAndroid({
      dumps: [
        ACCOUNT_NAVIGATION_SURFACE,
        OTHER_METHODS_SURFACE,
        LOGIN_METHOD_SURFACE,
        PHONE_SURFACE,
      ],
      waits: [
        { ok: false, error: 'wait_timeout: element_not_found' },
        { ok: true, serial: 'pixel-3', action: 'wait', waitedMs: 0, element: {} },
      ],
      overrides: {
        tap: ({ args }) => {
          return { ok: true, serial: 'pixel-3', action: 'tap' }
        },
      },
    })

    assert.equal(
      execute(
        parseOptions(['begin-login', '--method', 'phone']),
        android.invoke,
      ).status,
      'phone-surface-ready',
    )
    const providerGuardMatches = android.calls
      .filter(({ command }) => command === 'tap')
      .map(({ args }) => args
        .flatMap((argument, index) => argument === '--reject-regex' ? [args[index + 1]] : [])
        .some((source) => new RegExp(source, 'i').test(label)))
    assert.deepEqual(
      providerGuardMatches,
      [true, true, false],
    )
  }
})

test('phone actions stop on provider, account, identity, challenge, permission, purchase, profile, or social states', () => {
  for (const [label, category] of [
    ['Choose an account', 'provider_or_account'],
    ['Continue as Adithya', 'provider_or_account'],
    ['Create a passkey', 'passkey_or_identity'],
    ['Enter verification code', 'two_factor'],
    ["I'm not a robot CAPTCHA", 'captcha'],
    ['Allow Bumble to access your contacts', 'permission'],
    ['Complete purchase', 'purchase'],
    ['Create your profile', 'profile'],
    ['Connect your Instagram', 'social'],
  ]) {
    const unsafeSurface = [
      ...PHONE_SURFACE,
      element({
        text: label,
        className: 'android.widget.TextView',
        bounds: [100, 1200, 980, 1300],
      }),
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
    assert.equal(
      android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)),
      false,
    )
  }

  const wrongFocus = scriptedAndroid({
    currents: [{
      ok: true,
      serial: 'pixel-3',
      focus: 'mCurrentFocus=Window{1 u0 com.google.android.gms/.auth.uiflows.minutemaid.MinuteMaidActivity}',
    }],
  })
  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      wrongFocus.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /bumble_not_in_foreground/,
  )
  assert.equal(
    wrongFocus.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)),
    false,
  )
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

test('fill-phone stops before typing if an unsafe state appears after the field tap', () => {
  const unsafeSurface = [
    ...PHONE_SURFACE,
    element({
      text: 'Create a passkey',
      className: 'android.widget.TextView',
      bounds: [100, 1200, 980, 1300],
    }),
  ]
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE, unsafeSurface] })

  assert.throws(
    () => execute(
      parseOptions(['fill-phone']),
      android.invoke,
      JSON.stringify({ phone: '5125550199-private' }),
    ),
    /unsafe_auth_surface: passkey_or_identity/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.equal(android.calls.some(({ command }) => command === 'type-stdin'), false)
})

test('fill-phone redacts the phone and child failure details', () => {
  const phone = '5125550199-private'
  const android = scriptedAndroid({
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

test('request-code guards only the exact Continue button, re-inspects, and claims only submission', () => {
  const android = scriptedAndroid({ dumps: [PHONE_SURFACE, [{ text: 'Loading' }]] })

  const result = execute(
    parseOptions(['request-code', '--confirm', 'request', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'request-code',
    id: 'bumble',
    name: 'Bumble',
    serial: 'pixel-3',
    package: BUMBLE_PACKAGE,
    status: 'submission-observed',
    authentication: 'unverified',
  })
  assert.deepEqual(withoutFinalTapGuards(android.calls), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', BUMBLE_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '1',
        '--desc', 'Continue',
        '--text', '',
        '--id', 'com.bumble.app:id/reg_footer_button',
        '--class', 'android.widget.Button',
        '--bounds', '[904,1843][1036,1975]',
        '--unique', 'true',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('request-code stops after submit on focus loss or an unverified verification-code surface', () => {
  const postSubmitCases = [
    {
      currents: [
        {
          ok: true,
          serial: 'pixel-3',
          focus: 'mCurrentFocus=Window{1 u0 com.bumble.app/com.bumble.app.LoginActivity}',
        },
        {
          ok: true,
          serial: 'pixel-3',
          focus: 'mCurrentFocus=Window{1 u0 com.google.android.gms/.auth.uiflows.minutemaid.MinuteMaidActivity}',
        },
      ],
      dumps: [PHONE_SURFACE],
      error: /bumble_not_in_foreground/,
    },
    {
      dumps: [
        PHONE_SURFACE,
        [element({
          text: 'Enter verification code',
          className: 'android.widget.TextView',
          bounds: [100, 1200, 980, 1300],
        })],
      ],
      error: /unsafe_auth_surface: two_factor/,
    },
    ...['Continue with Google', 'Continue with Facebook', 'Continue with Apple'].map((label) => ({
      dumps: [
        PHONE_SURFACE,
        [element({
          text: label,
          className: 'android.widget.TextView',
          bounds: [100, 1200, 980, 1300],
        })],
      ],
      error: /unsafe_auth_surface: provider_or_account/,
    })),
  ]

  for (const { currents, dumps, error } of postSubmitCases) {
    const android = scriptedAndroid({ currents, dumps })
    assert.throws(
      () => execute(
        parseOptions(['request-code', '--confirm', 'request']),
        android.invoke,
      ),
      error,
    )
    assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  }
})
