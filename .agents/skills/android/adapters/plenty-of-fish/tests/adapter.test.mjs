import assert from 'node:assert/strict'
import { isAbsolute, relative } from 'node:path'
import test from 'node:test'
import {
  PLENTY_OF_FISH_PACKAGE,
  RUNTIME_DIRECTORY,
  execute,
  parseOptions,
} from '../cli/plenty-of-fish.mjs'

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [PLENTY_OF_FISH_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'Plenty of Fish' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Initial surface' }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: PLENTY_OF_FISH_PACKAGE },
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

const LOGIN_FORM = [
  {
    text: 'Username or email',
    desc: '',
    resourceId: 'com.pof.android:id/username',
    className: 'android.widget.EditText',
    bounds: { x1: 120, y1: 581, x2: 960, y2: 727, x: 540, y: 654 },
  },
  {
    text: 'Password',
    desc: '',
    resourceId: 'com.pof.android:id/password',
    className: 'android.widget.EditText',
    bounds: { x1: 120, y1: 730, x2: 960, y2: 873, x: 540, y: 802 },
  },
  {
    text: 'Log in',
    desc: '',
    resourceId: 'com.pof.android:id/login',
    className: 'android.widget.Button',
    bounds: { x1: 120, y1: 1015, x2: 960, y2: 1133, x: 540, y: 1074 },
  },
]

const FILLED_LOGIN_FORM = [
  { ...LOGIN_FORM[0], text: 'member@example.com' },
  { ...LOGIN_FORM[1], text: '••••••••' },
  LOGIN_FORM[2],
]

const UNSAFE_REJECT_REGEXPS = [
  String.raw`\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue as\b|\baccount owner\b|\bwho(?:'s| is) using\b`,
  String.raw`\bcontinue with (?:google|facebook|apple)\b`,
  String.raw`\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller`,
  String.raw`\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b`,
  String.raw`\btwo[- ]factor\b|\b2[- ]step\b|\bverification code\b|\bauthentication code\b|\bsecurity code\b|\benter (?:the )?code\b`,
  String.raw`captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge`,
  String.raw`\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b`,
  String.raw`\bcreate (?:your )?profile\b|\bedit (?:your )?profile\b|\bcomplete (?:your )?profile\b|\bprofile setup\b`,
  String.raw`\b(?:connect|link|add) (?:your )?(?:instagram|facebook|spotify|social)\b`,
]

function scriptedAndroid({ dumps = [LOGIN_FORM], currents, overrides = {} } = {}) {
  const calls = []
  let dumpIndex = 0
  let currentIndex = 0
  const currentResults = currents || [
    { ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.pof.android/com.pof.android.LoginActivity}' },
  ]
  return {
    calls,
    invoke(command, args, input) {
      calls.push({ command, args, ...(input === undefined ? {} : { input }) })
      if (overrides[command]) return overrides[command]({ command, args, input, calls })
      if (command === 'packages') {
        return { ok: true, serial: 'pixel-3', packages: [PLENTY_OF_FISH_PACKAGE] }
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
      if (command === 'launch') return { ok: true, serial: 'pixel-3', action: 'launch', package: PLENTY_OF_FISH_PACKAGE }
      if (command === 'wait') return { ok: true, serial: 'pixel-3', action: 'wait' }
      if (command === 'type-stdin') return { ok: true, serial: 'pixel-3', action: 'type-stdin' }
      throw new Error(`unexpected_android_command: ${command}`)
    },
  }
}

test('check requires the exact Plenty of Fish package', () => {
  const android = fakeAndroid()

  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'plenty-of-fish',
    name: 'Plenty of Fish',
    serial: 'pixel-3',
    package: PLENTY_OF_FISH_PACKAGE,
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--package', PLENTY_OF_FISH_PACKAGE] },
  ])

  const nearMatch = fakeAndroid({
    packages: { ok: true, serial: 'pixel-3', packages: [`${PLENTY_OF_FISH_PACKAGE}.helper`] },
  })
  assert.throws(
    () => execute(parseOptions(['check']), nearMatch.invoke),
    /plenty-of-fish_not_installed/,
  )
  assert.deepEqual(nearMatch.calls, [
    { command: 'packages', args: ['--package', PLENTY_OF_FISH_PACKAGE] },
  ])
})

test('inspect returns only fresh current and UI state', () => {
  const android = fakeAndroid()

  assert.deepEqual(execute(parseOptions(['inspect', '--serial', 'pixel-3']), android.invoke), {
    ok: true,
    action: 'inspect',
    id: 'plenty-of-fish',
    name: 'Plenty of Fish',
    serial: 'pixel-3',
    package: PLENTY_OF_FISH_PACKAGE,
    focus: 'Plenty of Fish',
    elements: [{ text: 'Initial surface' }],
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', PLENTY_OF_FISH_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('open launches the exact package then refreshes visible state', () => {
  const android = fakeAndroid()

  const result = execute(parseOptions(['open', '--serial', 'pixel-3']), android.invoke)

  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'Plenty of Fish')
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'launch', 'current', 'dump'])
  assert.deepEqual(android.calls[1].args, ['--serial', 'pixel-3', '--package', PLENTY_OF_FISH_PACKAGE])
})

test('screenshot output is restricted to the Plenty of Fish runtime directory', () => {
  const android = fakeAndroid()

  execute(parseOptions(['screenshot', '--out', 'initial.png']), android.invoke)

  const output = android.calls.at(-1).args.at(-1)
  assert.equal(isAbsolute(output), true)
  assert.equal(relative(RUNTIME_DIRECTORY, output).startsWith('..'), false)
  assert.throws(
    () => execute(parseOptions(['screenshot', '--out', '/tmp/plenty-of-fish.png']), fakeAndroid().invoke),
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

test('fill-login accepts only --serial and never accepts credentials as options', () => {
  assert.deepEqual(parseOptions(['fill-login', '--serial', 'pixel-3']), {
    command: 'fill-login',
    serial: 'pixel-3',
  })

  const secret = 'cli-secret-should-not-escape'
  assert.throws(
    () => parseOptions(['fill-login', '--password', secret]),
    (error) => {
      assert.doesNotMatch(error.message, new RegExp(secret))
      return /fill_login_options/.test(error.message)
    },
  )
})

test('fill-login rejects malformed credential stdin without exposing its payload', () => {
  const android = scriptedAndroid()
  const cases = [
    ['', 'credential_input_invalid'],
    ['not-json-with-private-token', 'credential_input_invalid'],
    [JSON.stringify({ username: 'member@example.com', password: 'private-token', extra: true }), 'credential_input_invalid'],
    [JSON.stringify({ username: '', password: 'private-token' }), 'credential_input_invalid'],
    [JSON.stringify({ username: 'member@example.com\nother', password: 'private-token' }), 'credential_input_invalid'],
    [JSON.stringify({ username: 'member@example.com', password: 'private\r\ntoken' }), 'credential_input_invalid'],
  ]

  for (const [input, expected] of cases) {
    assert.throws(
      () => execute(parseOptions(['fill-login']), android.invoke, input),
      (error) => {
        assert.equal(error.message, expected)
        assert.doesNotMatch(error.message, /private|member@example|not-json/)
        return true
      },
    )
  }
  assert.deepEqual(android.calls, [])
})

test('fill-login fails closed on non-exact or non-unique login controls before mutation', () => {
  const malformedForms = [
    [...LOGIN_FORM, { ...LOGIN_FORM[0] }],
    LOGIN_FORM.map((element, index) => index === 0 ? { ...element, text: 'Email' } : element),
    LOGIN_FORM.map((element, index) => index === 1 ? { ...element, resourceId: 'com.pof.android:id/passcode' } : element),
    LOGIN_FORM.map((element, index) => index === 2 ? { ...element, className: 'android.widget.TextView' } : element),
    LOGIN_FORM.map((element, index) => index === 0 ? { ...element, bounds: null } : element),
    LOGIN_FORM.map((element, index) => index === 1 ? { ...element, bounds: { x1: 120, y1: 730, x2: 120, y2: 873 } } : element),
  ]
  const credentials = JSON.stringify({ username: 'member@example.com', password: 'private-token' })

  for (const form of malformedForms) {
    const android = scriptedAndroid({ dumps: [form] })
    assert.throws(
      () => execute(parseOptions(['fill-login']), android.invoke, credentials),
      /login_form_not_exact_unique/,
    )
    assert.equal(android.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
  }
})

test('fill-login launches POF and waits for the exact username control before inspecting the form', () => {
  const android = scriptedAndroid({
    overrides: {
      launch: () => ({ ok: true, serial: 'pixel-3', action: 'launch', package: PLENTY_OF_FISH_PACKAGE }),
      wait: () => ({ ok: true, serial: 'pixel-3', action: 'wait' }),
    },
  })

  execute(
    parseOptions(['fill-login', '--serial', 'pixel-3']),
    android.invoke,
    JSON.stringify({ username: 'member@example.com', password: 'private-token' }),
  )

  assert.deepEqual(android.calls.slice(0, 5), [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', PLENTY_OF_FISH_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', PLENTY_OF_FISH_PACKAGE] },
    {
      command: 'wait',
      args: [
        '--serial', 'pixel-3',
        '--id', 'com.pof.android:id/username',
        '--text', 'Username or email',
        '--class', 'android.widget.EditText',
        '--bounds', '[120,581][960,727]',
        '--unique', 'true',
        '--timeout-ms', '3000',
        '--poll-ms', '250',
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('fill-login types username then password through separate child stdin calls and never submits', () => {
  const username = 'member@example.com'
  const password = 'private-token'
  const usernameFilled = [
    { ...LOGIN_FORM[0], text: username },
    LOGIN_FORM[1],
    LOGIN_FORM[2],
  ]
  const fullyFilled = [
    { ...LOGIN_FORM[0], text: username },
    { ...LOGIN_FORM[1], text: '••••••••' },
    LOGIN_FORM[2],
  ]
  const android = scriptedAndroid({
    dumps: [LOGIN_FORM, LOGIN_FORM, usernameFilled, usernameFilled, fullyFilled],
  })

  const result = execute(
    parseOptions(['fill-login', '--serial', 'pixel-3']),
    android.invoke,
    JSON.stringify({ username, password }),
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'fill-login',
    id: 'plenty-of-fish',
    name: 'Plenty of Fish',
    serial: 'pixel-3',
    package: PLENTY_OF_FISH_PACKAGE,
    status: 'credentials-filled',
    submitted: false,
  })
  assert.doesNotMatch(JSON.stringify(result), new RegExp(`${username}|${password}`))
  assert.deepEqual(android.calls.map(({ command }) => command), [
    'packages', 'launch', 'wait', 'current', 'dump',
    'tap', 'current', 'dump',
    'type-stdin',
    'packages', 'current', 'dump',
    'tap', 'current', 'dump',
    'type-stdin',
    'current', 'dump',
  ])
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'tap').map(({ args }) => args),
    [
      [
        '--serial', 'pixel-3',
        '--index', '0',
        '--id', 'com.pof.android:id/username',
        '--class', 'android.widget.EditText',
        '--bounds', '[120,581][960,727]',
        '--unique', 'true',
        ...UNSAFE_REJECT_REGEXPS.flatMap((pattern) => ['--reject-regex', pattern]),
      ],
      [
        '--serial', 'pixel-3',
        '--index', '1',
        '--id', 'com.pof.android:id/password',
        '--class', 'android.widget.EditText',
        '--bounds', '[120,730][960,873]',
        '--unique', 'true',
        ...UNSAFE_REJECT_REGEXPS.flatMap((pattern) => ['--reject-regex', pattern]),
      ],
    ],
  )
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'type-stdin'),
    [
      { command: 'type-stdin', args: ['--serial', 'pixel-3'], input: username },
      { command: 'type-stdin', args: ['--serial', 'pixel-3'], input: password },
    ],
  )
  assert.equal(
    android.calls.some(({ command, args }) => command === 'tap' && args.includes('com.pof.android:id/login')),
    false,
  )
})

test('fill-login refuses unsafe prompts and non-POF focus before any typing', () => {
  const credentials = JSON.stringify({ username: 'member@example.com', password: 'private-token' })
  for (const [label, category] of [
    ['Choose an account', 'account_selection'],
    ['Continue with Google', 'provider_or_account'],
    ['Allow POF to access your photos', 'permission'],
    ['Create a passkey', 'passkey_or_identity'],
    ['Enter verification code', 'two_factor'],
    ["I'm not a robot CAPTCHA", 'captcha'],
    ['Complete purchase', 'purchase'],
    ['Create your profile', 'profile'],
  ]) {
    const unsafe = scriptedAndroid({
      dumps: [[...LOGIN_FORM, { text: label, desc: '', resourceId: '', className: 'android.widget.TextView' }]],
    })
    assert.throws(
      () => execute(parseOptions(['fill-login']), unsafe.invoke, credentials),
      new RegExp(`unsafe_auth_surface: ${category}`),
    )
    assert.equal(unsafe.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
  }

  const promptAfterFieldTap = scriptedAndroid({
    dumps: [
      LOGIN_FORM,
      [...LOGIN_FORM, { text: 'Allow POF to access your photos', desc: '', resourceId: '', className: 'android.widget.TextView' }],
    ],
  })
  assert.throws(
    () => execute(parseOptions(['fill-login']), promptAfterFieldTap.invoke, credentials),
    /unsafe_auth_surface: permission/,
  )
  assert.equal(promptAfterFieldTap.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.equal(promptAfterFieldTap.calls.some(({ command }) => command === 'type-stdin'), false)

  const wrongFocus = scriptedAndroid({
    currents: [{ ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.android.permissioncontroller/.GrantPermissionsActivity}' }],
  })
  assert.throws(
    () => execute(parseOptions(['fill-login']), wrongFocus.invoke, credentials),
    /pof_not_in_foreground/,
  )
  assert.equal(wrongFocus.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)

  const packagePrefixFocus = scriptedAndroid({
    currents: [{ ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.pof.android.helper/.LoginActivity}' }],
  })
  assert.throws(
    () => execute(parseOptions(['fill-login']), packagePrefixFocus.invoke, credentials),
    /pof_not_in_foreground/,
  )
  assert.equal(packagePrefixFocus.calls.some(({ command }) => ['tap', 'type-stdin'].includes(command)), false)
})

test('fill-login stops before either credential type on a social-linking handoff', () => {
  const android = scriptedAndroid({
    dumps: [[
      ...LOGIN_FORM,
      { text: 'Connect your Instagram', desc: '', resourceId: '', className: 'android.widget.TextView' },
    ]],
  })

  assert.throws(
    () => execute(
      parseOptions(['fill-login', '--serial', 'pixel-3']),
      android.invoke,
      JSON.stringify({ username: 'member@example.com', password: 'private-token' }),
    ),
    /unsafe_auth_surface: social/,
  )
  assert.equal(android.calls.some(({ command }) => command === 'type-stdin'), false)
})

test('every guarded POF field and submit tap passes all unsafe rejections to the generic tap', () => {
  const fill = scriptedAndroid({
    dumps: [LOGIN_FORM, LOGIN_FORM, [{ ...LOGIN_FORM[0], text: 'member@example.com' }, LOGIN_FORM[1], LOGIN_FORM[2]], [{ ...LOGIN_FORM[0], text: 'member@example.com' }, LOGIN_FORM[1], LOGIN_FORM[2]], FILLED_LOGIN_FORM],
  })
  execute(
    parseOptions(['fill-login', '--serial', 'pixel-3']),
    fill.invoke,
    JSON.stringify({ username: 'member@example.com', password: 'private-token' }),
  )

  const submit = scriptedAndroid({ dumps: [FILLED_LOGIN_FORM, [{ text: 'Loading' }]] })
  execute(
    parseOptions(['submit-login', '--confirm', 'submit', '--serial', 'pixel-3']),
    submit.invoke,
  )

  const guardedTaps = [...fill.calls, ...submit.calls]
    .filter(({ command }) => command === 'tap')
  assert.equal(guardedTaps.length, 3)
  for (const { args } of guardedTaps) {
    assert.deepEqual(
      args.filter((value, index) => args[index - 1] === '--reject-regex'),
      UNSAFE_REJECT_REGEXPS,
    )
  }
})

test('fill-login stops before typing when the generic guarded tap refuses the fresh fingerprint', () => {
  const android = scriptedAndroid({
    overrides: {
      tap: ({ args }) => args.includes('--unique')
        ? { ok: false, error: 'element_not_found' }
        : { ok: true, serial: 'pixel-3', action: 'tap' },
    },
  })

  assert.throws(
    () => execute(
      parseOptions(['fill-login', '--serial', 'pixel-3']),
      android.invoke,
      JSON.stringify({ username: 'member@example.com', password: 'private-token' }),
    ),
    /android_tap_failed/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.equal(android.calls.some(({ command }) => command === 'type-stdin'), false)
})

test('submit-login requires exact confirmation, proves fresh state, and returns no success claim', () => {
  for (const argv of [
    ['submit-login'],
    ['submit-login', '--confirm', 'yes'],
  ]) {
    assert.throws(() => parseOptions(argv), /submit_confirmation_required/)
  }

  const bypass = scriptedAndroid({ dumps: [FILLED_LOGIN_FORM] })
  assert.throws(
    () => execute({ command: 'submit-login', serial: 'pixel-3' }, bypass.invoke),
    /submit_confirmation_required/,
  )
  assert.deepEqual(bypass.calls, [])

  const android = scriptedAndroid({ dumps: [FILLED_LOGIN_FORM, [{ text: 'Loading' }]] })
  const result = execute(
    parseOptions(['submit-login', '--confirm', 'submit', '--serial', 'pixel-3']),
    android.invoke,
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'submit-login',
    id: 'plenty-of-fish',
    name: 'Plenty of Fish',
    serial: 'pixel-3',
    package: PLENTY_OF_FISH_PACKAGE,
    status: 'submission-observed',
    authentication: 'unverified',
  })
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', PLENTY_OF_FISH_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
    {
      command: 'tap',
      args: [
        '--serial', 'pixel-3',
        '--index', '2',
        '--id', 'com.pof.android:id/login',
        '--class', 'android.widget.Button',
        '--bounds', '[120,1015][960,1133]',
        '--unique', 'true',
        ...UNSAFE_REJECT_REGEXPS.flatMap((pattern) => ['--reject-regex', pattern]),
      ],
    },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('submit-login stops when the generic guarded tap refuses the fresh fingerprint', () => {
  const android = scriptedAndroid({
    dumps: [FILLED_LOGIN_FORM],
    overrides: {
      tap: ({ args }) => args.includes('--unique')
        ? { ok: false, error: 'element_not_unique' }
        : { ok: true, serial: 'pixel-3', action: 'tap' },
    },
  })

  assert.throws(
    () => execute(
      parseOptions(['submit-login', '--confirm', 'submit', '--serial', 'pixel-3']),
      android.invoke,
    ),
    /android_tap_failed/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 1)
  assert.deepEqual(android.calls.map(({ command }) => command), ['packages', 'current', 'dump', 'tap'])
})

test('submit-login stops on a post-submit focus loss or verification prompt', () => {
  const focusLoss = scriptedAndroid({
    dumps: [FILLED_LOGIN_FORM],
    currents: [
      { ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.pof.android/com.pof.android.LoginActivity}' },
      { ok: true, serial: 'pixel-3', focus: 'mCurrentFocus=Window{1 u0 com.android.permissioncontroller/.GrantPermissionsActivity}' },
    ],
  })
  assert.throws(
    () => execute(
      parseOptions(['submit-login', '--confirm', 'submit', '--serial', 'pixel-3']),
      focusLoss.invoke,
    ),
    /pof_not_in_foreground/,
  )
  assert.deepEqual(focusLoss.calls.map(({ command }) => command), ['packages', 'current', 'dump', 'tap', 'current'])

  const verificationPrompt = scriptedAndroid({
    dumps: [
      FILLED_LOGIN_FORM,
      [{ text: 'Enter verification code', desc: '', resourceId: '', className: 'android.widget.TextView' }],
    ],
  })
  assert.throws(
    () => execute(
      parseOptions(['submit-login', '--confirm', 'submit', '--serial', 'pixel-3']),
      verificationPrompt.invoke,
    ),
    /unsafe_auth_surface: two_factor/,
  )
  assert.deepEqual(verificationPrompt.calls.map(({ command }) => command), ['packages', 'current', 'dump', 'tap', 'current', 'dump'])
})

test('submit-login stops on a social-linking handoff after its guarded tap', () => {
  const socialPrompt = scriptedAndroid({
    dumps: [
      FILLED_LOGIN_FORM,
      [{ text: 'Connect your Instagram', desc: '', resourceId: '', className: 'android.widget.TextView' }],
    ],
  })

  assert.throws(
    () => execute(
      parseOptions(['submit-login', '--confirm', 'submit', '--serial', 'pixel-3']),
      socialPrompt.invoke,
    ),
    /unsafe_auth_surface: social/,
  )
  assert.deepEqual(socialPrompt.calls.map(({ command }) => command), ['packages', 'current', 'dump', 'tap', 'current', 'dump'])
})

test('authentication errors redact credential values and child failure details', () => {
  const username = 'member@example.com'
  const password = 'private-token'
  const android = scriptedAndroid({
    overrides: {
      'type-stdin': ({ input }) => ({ ok: false, error: `adb rejected ${input}` }),
    },
  })

  assert.throws(
    () => execute(
      parseOptions(['fill-login']),
      android.invoke,
      JSON.stringify({ username, password }),
    ),
    (error) => {
      assert.equal(error.message, 'android_type_stdin_failed')
      assert.doesNotMatch(error.message, new RegExp(`${username}|${password}|adb rejected`))
      return true
    },
  )
})
