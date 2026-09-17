import assert from 'node:assert/strict'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const moduleUrl = new URL('../cli/play-store.mjs', import.meta.url)

async function loadAdapter() {
  return import(moduleUrl.href)
}

function fakeAndroid(packageName, overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [packageName] },
    current: { ok: true, serial: 'pixel-3', focus: 'Google Play Store' },
    dump: { ok: true, serial: 'pixel-3', elements: [{ text: 'Search' }] },
    launch: { ok: true, serial: 'pixel-3', action: 'launch', package: packageName },
    tap: { ok: true, serial: 'pixel-3', action: 'tap' },
    type: { ok: true, serial: 'pixel-3', action: 'type' },
    key: (args) => (
      args.slice(-2).join(' ') === '--name enter'
        || args.slice(-2).join(' ') === '--name delete'
        || args.slice(-2).join(' ') === '--code 123'
        ? { ok: true, serial: 'pixel-3', action: 'key' }
        : { ok: false, error: 'key_required' }
    ),
  }
  return {
    calls,
    invoke(command, args) {
      calls.push({ command, args })
      const response = overrides[command] ?? defaults[command]
      if (typeof response === 'function') return response(args, calls)
      return Array.isArray(response) ? response.shift() : response
    },
  }
}

function repeatedOptionValues(args, option) {
  const values = []
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === option) values.push(args[index + 1])
  }
  return values
}

function searchDumps(query, tail = []) {
  return [
    { ok: true, serial: 'pixel-3', elements: [{ text: 'Search' }] },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [{ desc: 'Search apps & games', className: 'android.widget.EditText' }],
    },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [{
        desc: 'Search apps & games',
        resourceId: 'com.android.vending:id/search_box',
        className: 'android.widget.EditText',
      }],
    },
    { ok: true, serial: 'pixel-3', elements: [{ text: query }] },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [...CAPTURED_RESULTS_HEADER, { text: query }, { text: 'Dating' }],
    },
    ...tail,
  ]
}

const LIVE_WELCOME_DUMP = {
  ok: true,
  serial: '976X23G9X',
  elements: [
    { text: 'Welcome to Google Play', desc: '', resourceId: '', className: 'android.widget.TextView' },
    { text: '', desc: 'Not now', resourceId: '', className: 'android.view.View' },
    { text: 'Not now', desc: '', resourceId: '', className: 'android.widget.TextView' },
    { text: '', desc: 'Get started', resourceId: '', className: 'android.view.View' },
    { text: 'Get started', desc: '', resourceId: '', className: 'android.widget.TextView' },
    { text: 'Search', desc: '', resourceId: '', className: 'android.widget.TextView' },
  ],
}

const LEVEL_UP_PROMOTION_HEADING = 'Level up your experience'
const LEVEL_UP_PROMOTION_COPY = 'Get special offers, early access to new features, and updates straight to your device and email'

const CAPTURED_LEVEL_UP_PROMOTION_DUMP = {
  ok: true,
  serial: '976X23G9X',
  elements: [
    {
      text: LEVEL_UP_PROMOTION_HEADING,
      desc: '',
      resourceId: '',
      className: 'android.widget.TextView',
      bounds: { x1: 88, y1: 420, x2: 992, y2: 500, x: 540, y: 460 },
    },
    {
      text: LEVEL_UP_PROMOTION_COPY,
      desc: '',
      resourceId: '',
      className: 'android.widget.TextView',
      bounds: { x1: 88, y1: 530, x2: 992, y2: 710, x: 540, y: 620 },
    },
    {
      text: '',
      desc: 'Not now',
      resourceId: '',
      className: 'android.view.View',
      bounds: { x1: 88, y1: 790, x2: 508, y2: 900, x: 298, y: 845 },
    },
    {
      text: 'Not now',
      desc: '',
      resourceId: '',
      className: 'android.widget.TextView',
      bounds: { x1: 88, y1: 790, x2: 508, y2: 900, x: 298, y: 845 },
    },
    {
      text: '',
      desc: "I'm in!",
      resourceId: '',
      className: 'android.view.View',
      bounds: { x1: 572, y1: 790, x2: 992, y2: 900, x: 782, y: 845 },
    },
    { text: 'Search', desc: '', resourceId: '', className: 'android.widget.TextView' },
  ],
}

const LIVE_ACTIVE_SEARCH_INPUT = {
  text: 'Dil MilMirchi',
  desc: '',
  resourceId: '',
  className: 'android.widget.EditText',
  bounds: { x1: 154, y1: 88, x2: 926, y2: 220, x: 540, y: 154 },
}

const LIVE_ACTIVE_SEARCH_CLEAR = {
  text: '',
  desc: 'Clear',
  resourceId: '',
  className: 'android.view.View',
  bounds: { x1: 970, y1: 121, x2: 1036, y2: 187, x: 1003, y: 154 },
}

const LIVE_ACTIVE_SEARCH_DUMP = {
  ok: true,
  serial: '976X23G9X',
  elements: [
    LIVE_ACTIVE_SEARCH_INPUT,
    LIVE_ACTIVE_SEARCH_CLEAR,
    { text: '', desc: 'Navigate up', resourceId: '', className: 'android.view.View' },
    { text: 'No results for dil milmirchi', desc: '', resourceId: '', className: 'android.widget.TextView' },
  ],
}

const CAPTURED_COMPOSE_SEARCH_INPUT = {
  text: '',
  desc: '',
  resourceId: '',
  className: 'android.widget.EditText',
  bounds: { x1: 154, y1: 88, x2: 926, y2: 220, x: 540, y: 154 },
}

const CAPTURED_COMPOSE_SEARCH_LABEL = {
  text: 'Search apps & games',
  desc: '',
  resourceId: '',
  className: 'android.widget.TextView',
  bounds: { x1: 154, y1: 121, x2: 587, y2: 187, x: 371, y: 154 },
}

const CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP = {
  text: '',
  desc: 'Navigate up',
  resourceId: '',
  className: 'android.view.View',
  bounds: { x1: 22, y1: 88, x2: 132, y2: 220, x: 77, y: 154 },
}

function composeSearchDump(input = CAPTURED_COMPOSE_SEARCH_INPUT, extras = []) {
  return {
    ok: true,
    serial: '976X23G9X',
    elements: [input, CAPTURED_COMPOSE_SEARCH_LABEL, CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP, ...extras],
  }
}

const FIRST_DIL_MIL_RESULT = {
  text: 'Dil Mil: South Asian Dating',
  desc: '',
  resourceId: 'listing',
  className: 'android.widget.TextView',
  bounds: { x1: 40, y1: 300, x2: 760, y2: 380, x: 400, y: 340 },
}

const SECOND_DIL_MIL_RESULT = {
  text: '',
  desc: 'Dil Mil Dating App',
  resourceId: 'listing',
  className: 'android.widget.TextView',
  bounds: { x1: 40, y1: 600, x2: 760, y2: 680, x: 400, y: 640 },
}

const CAPTURED_DIL_MIL_CARD_LABEL = 'Dil Mil: South Asian Dating&#10;Dil Mil Inc.&#10;Contains ads&#10;'

const CAPTURED_RESULTS_SEARCH_FIELD = {
  text: '',
  desc: '',
  resourceId: '',
  className: 'android.widget.EditText',
  bounds: { x1: 154, y1: 88, x2: 926, y2: 220, x: 540, y: 154 },
}

const CAPTURED_RESULTS_SEARCH_CHILD = {
  text: 'Dil Mil',
  desc: '',
  resourceId: '',
  className: 'android.widget.TextView',
  bounds: { x1: 154, y1: 121, x2: 273, y2: 187, x: 214, y: 154 },
}

const CAPTURED_RESULTS_HEADER = [
  {
    text: '',
    desc: 'Navigate up',
    resourceId: '',
    className: 'android.view.View',
    bounds: { x1: 22, y1: 88, x2: 132, y2: 220, x: 77, y: 154 },
  },
  {
    text: '',
    desc: 'Search Google Play',
    resourceId: '',
    className: 'android.view.View',
    bounds: { x1: 132, y1: 88, x2: 948, y2: 220, x: 540, y: 154 },
  },
  {
    text: '',
    desc: 'Voice Search',
    resourceId: '',
    className: 'android.view.View',
    bounds: { x1: 948, y1: 88, x2: 1058, y2: 220, x: 1003, y: 154 },
  },
]

function withResultsHeader(elements) {
  return [...CAPTURED_RESULTS_HEADER, ...elements]
}

const CAPTURED_DIL_MIL_CARDS = [
  {
    text: '',
    desc: CAPTURED_DIL_MIL_CARD_LABEL,
    resourceId: '',
    className: 'android.view.View',
    bounds: { x1: 264, y1: 410, x2: 784, y2: 582, x: 524, y: 496 },
  },
  {
    text: '',
    desc: CAPTURED_DIL_MIL_CARD_LABEL,
    resourceId: '',
    className: 'android.view.View',
    bounds: { x1: 264, y1: 970, x2: 784, y2: 1142, x: 524, y: 1056 },
  },
]

test('search declines the captured live welcome surface before selecting fresh controls', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [LIVE_WELCOME_DUMP, ...searchDumps('Dil Mil')],
  })

  const result = execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke)

  assert.equal(result.action, 'search')
  assert.deepEqual(android.calls.filter(({ command }) => command === 'tap').map(({ args }) => args), [
    ['--desc', 'Not now'],
    ['--text', 'Search'],
    ['--desc', 'Search apps & games'],
  ])
})

test('search does not use Not now or an arbitrary EditText outside the exact welcome flow', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: {
      ok: true,
      serial: 'pixel-3',
      elements: [
        { text: 'Sign in to continue' },
        { desc: 'Not now' },
        { className: 'android.widget.EditText', desc: 'Email or phone' },
      ],
    },
  })

  assert.throws(
    () => execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke),
    /search_navigation_control_not_found/,
  )
  assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
})

test('search dismisses the captured level-up promotion with exactly one guarded Not now tap', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [CAPTURED_LEVEL_UP_PROMOTION_DUMP, ...searchDumps('Dil Mil')],
  })

  const result = execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke)

  assert.equal(result.action, 'search')
  const taps = android.calls.filter(({ command }) => command === 'tap')
  const declineTaps = taps.filter(({ args }) => args.includes('Not now'))
  assert.equal(declineTaps.length, 1)
  assert.deepEqual(declineTaps[0].args.slice(0, 8), [
    '--index', '2',
    '--desc', 'Not now',
    '--class', 'android.view.View',
    '--bounds', '[88,790][508,900]',
  ])
  assert.equal(declineTaps[0].args.includes('--x'), false)
  assert.deepEqual(repeatedOptionValues(declineTaps[0].args, '--unique'), ['true'])
  assert.equal(taps.some(({ args }) => args.includes("I'm in!")), false)
})

test('search refuses partial, lookalike, and ambiguous level-up promotions without tapping', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const [heading, copy, declineDesc, declineText, accept, search] = CAPTURED_LEVEL_UP_PROMOTION_DUMP.elements
  const decline = declineDesc
  const cases = [
    ['arbitrary decline', [decline, search]],
    ['missing copy anchor', [heading, decline, accept, search]],
    ['missing heading anchor', [copy, decline, accept, search]],
    ['heading without bounds', [{ ...heading, bounds: undefined }, copy, decline, accept, search]],
    ['heading with zero-area bounds', [
      { ...heading, bounds: { x1: 88, y1: 420, x2: 88, y2: 500, x: 88, y: 460 } },
      copy,
      decline,
      accept,
      search,
    ]],
    ['copy without bounds', [heading, { ...copy, bounds: undefined }, decline, accept, search]],
    ['copy with zero-area bounds', [
      heading,
      { ...copy, bounds: { x1: 88, y1: 530, x2: 992, y2: 530, x: 540, y: 530 } },
      decline,
      accept,
      search,
    ]],
    ['lookalike heading', [{ ...heading, text: 'Level up the experience' }, copy, decline, accept, search]],
    ['lookalike copy', [heading, { ...copy, text: `${LEVEL_UP_PROMOTION_COPY}.` }, decline, accept, search]],
    ['two lookalike anchors', [
      { ...heading, text: 'Level up the experience' },
      { ...copy, text: `${LEVEL_UP_PROMOTION_COPY}.` },
      decline,
      search,
    ]],
    ['ambiguous heading', [heading, { ...heading, bounds: { ...heading.bounds, y1: 300, y2: 380 } }, copy, decline, accept, search]],
    ['different decline bounds', [
      heading,
      copy,
      declineDesc,
      { ...declineText, bounds: { x1: 88, y1: 920, x2: 508, y2: 1030, x: 298, y: 975 } },
      accept,
      search,
    ]],
    ['decline candidate without bounds', [
      heading,
      copy,
      declineDesc,
      { ...declineText, bounds: undefined },
      accept,
      search,
    ]],
    ['decline candidate with zero-area bounds', [
      heading,
      copy,
      declineDesc,
      { ...declineText, bounds: { x1: 88, y1: 790, x2: 88, y2: 900, x: 88, y: 845 } },
      accept,
      search,
    ]],
    ['accept action only', [heading, copy, accept, search]],
  ]

  for (const [name, elements] of cases) {
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: { ...CAPTURED_LEVEL_UP_PROMOTION_DUMP, elements },
    })

    assert.throws(
      () => execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke),
      undefined,
      name,
    )
    assert.equal(
      android.calls.some(({ command }) => ['tap', 'type', 'key'].includes(command)),
      false,
      name,
    )
    assert.equal(
      android.calls.some(({ command, args }) => command === 'tap' && args.includes("I'm in!")),
      false,
      name,
    )
  }
})

test('option validation requires query only for search commands', async () => {
  const { parseOptions } = await loadAdapter()

  assert.deepEqual(parseOptions(['search', '--query', 'Dil Mil', '--serial', 'pixel-3']), {
    command: 'search',
    query: 'Dil Mil',
    serial: 'pixel-3',
  })
  assert.throws(() => parseOptions(['search']), /query_required/)
  assert.throws(() => parseOptions(['install-free', '--query', '   ']), /query_required/)
  assert.throws(() => parseOptions(['check', '--query', 'Dil Mil']), /query_only_supported_for_search/)
  assert.throws(() => parseOptions(['search', '--query', 'Dil Mil', '--out', 'x']), /unknown_option/)
})

test('option validation accepts candidates and a non-negative install result index only', async () => {
  const { parseOptions } = await loadAdapter()

  assert.deepEqual(parseOptions(['candidates', '--query', 'Dil Mil']), {
    command: 'candidates',
    query: 'Dil Mil',
  })
  assert.deepEqual(
    parseOptions(['install-free', '--query', 'Dil Mil', '--result-index', '1']),
    { command: 'install-free', query: 'Dil Mil', resultIndex: 1 },
  )
  for (const value of ['-1', '1.5', 'x', '', '9007199254740992']) {
    assert.throws(
      () => parseOptions(['install-free', '--query', 'Dil Mil', '--result-index', value]),
      /invalid_result_index/,
      value,
    )
  }
  assert.throws(
    () => parseOptions(['search', '--query', 'Dil Mil', '--result-index', '0']),
    /result_index_only_supported_for_install_free/,
  )
})

test('Android output parser accepts only identical duplicate JSON records', async () => {
  const { parseAndroidOutput } = await loadAdapter()
  const record = '{"ok":true,"serial":"pixel-3","elements":[]}'

  assert.deepEqual(parseAndroidOutput(`${record}\n${record}\n`), {
    ok: true,
    serial: 'pixel-3',
    elements: [],
  })
  assert.throws(
    () => parseAndroidOutput(`${record}\n{"ok":false,"error":"different"}\n`),
    /android_cli_conflicting_output/,
  )
})

test('check requires the exact Play Store package', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE)

  assert.deepEqual(execute(parseOptions(['check']), android.invoke), {
    ok: true,
    action: 'check',
    id: 'play-store',
    name: 'Google Play Store',
    serial: 'pixel-3',
    package: PLAY_STORE_PACKAGE,
  })
  assert.deepEqual(android.calls, [{ command: 'packages', args: ['--package', PLAY_STORE_PACKAGE] }])
  assert.throws(
    () => execute(
      parseOptions(['check']),
      fakeAndroid(PLAY_STORE_PACKAGE, {
        packages: { ok: true, serial: 'pixel-3', packages: ['com.example.vending'] },
      }).invoke,
    ),
    /play-store_not_installed/,
  )
})

test('open launches Play Store and inspect returns fresh UI state', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE)

  const result = execute(parseOptions(['open', '--serial', 'pixel-3']), android.invoke)

  assert.equal(result.action, 'open')
  assert.equal(result.focus, 'Google Play Store')
  assert.deepEqual(android.calls, [
    { command: 'packages', args: ['--serial', 'pixel-3', '--package', PLAY_STORE_PACKAGE] },
    { command: 'launch', args: ['--serial', 'pixel-3', '--package', PLAY_STORE_PACKAGE] },
    { command: 'current', args: ['--serial', 'pixel-3'] },
    { command: 'dump', args: ['--serial', 'pixel-3'] },
  ])
})

test('search refreshes UI before each observed selector tap and after each mutation', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: searchDumps('Dil Mil') })

  const result = execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke)

  assert.equal(result.action, 'search')
  assert.equal(result.query, 'Dil Mil')
  assert.deepEqual(result.elements, withResultsHeader([{ text: 'Dil Mil' }, { text: 'Dating' }]))
  assert.deepEqual(android.calls.map(({ command }) => command), [
    'packages', 'launch', 'current', 'dump',
    'tap', 'current', 'dump',
    'tap', 'current', 'dump',
    'type', 'current', 'dump',
    'key', 'current', 'dump',
  ])
  assert.deepEqual(android.calls[4].args, ['--text', 'Search'])
  assert.deepEqual(android.calls[7].args, ['--desc', 'Search apps & games'])
  assert.deepEqual(android.calls[13].args, ['--name', 'enter'])
})

test('search clears existing text from the observed searchable EditText before typing', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const searchField = {
    text: '',
    desc: 'Search apps & games',
    resourceId: 'com.android.vending:id/search_box',
    className: 'android.widget.EditText',
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      { ok: true, serial: 'pixel-3', elements: [searchField] },
      {
        ok: true,
        serial: 'pixel-3',
        elements: [{ ...searchField, text: 'Dil Mil' }],
      },
      { ok: true, serial: 'pixel-3', elements: [searchField] },
      { ok: true, serial: 'pixel-3', elements: [{ ...searchField, text: 'Mirchi' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Mirchi Dating' }] },
    ],
  })

  execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke)

  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'key').map(({ args }) => args),
    [
      ['--code', '123'],
      ...Array.from({ length: 7 }, () => ['--name', 'delete']),
      ['--name', 'enter'],
    ],
  )
  const typeCall = android.calls.findIndex(({ command }) => command === 'type')
  const finalDelete = android.calls.findLastIndex(
    ({ command, args }) => command === 'key' && args.includes('delete'),
  )
  assert.ok(finalDelete < typeCall)
})

test('search clears the exact captured unlabeled active Play Store search session', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      LIVE_ACTIVE_SEARCH_DUMP,
      LIVE_ACTIVE_SEARCH_DUMP,
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ ...LIVE_ACTIVE_SEARCH_INPUT, text: '' }],
      },
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ ...LIVE_ACTIVE_SEARCH_INPUT, text: 'Mirchi' }],
      },
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ text: 'Mirchi Dating', className: 'android.widget.TextView' }],
      },
    ],
  })

  const result = execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke)

  assert.equal(result.action, 'search')
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'tap').map(({ args }) => args),
    [
      ['--text', 'Dil MilMirchi'],
      ['--desc', 'Clear'],
    ],
  )
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'key').map(({ args }) => args),
    [['--name', 'enter']],
  )
  const clearTap = android.calls.findIndex(
    ({ command, args }) => command === 'tap' && args.includes('Clear'),
  )
  const typeCall = android.calls.findIndex(({ command }) => command === 'type')
  assert.ok(clearTap < typeCall)
})

test('search hands a labelled field tap off to the freshly observed unlabeled active session', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const labelledField = {
    text: '',
    desc: 'Search apps & games',
    resourceId: '',
    className: 'android.widget.EditText',
  }
  const active = {
    ...LIVE_ACTIVE_SEARCH_DUMP,
    elements: [
      { ...LIVE_ACTIVE_SEARCH_INPUT, text: 'Dil Mil' },
      LIVE_ACTIVE_SEARCH_CLEAR,
      { text: '', desc: 'Navigate up', resourceId: '', className: 'android.view.View' },
    ],
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      { ok: true, serial: '976X23G9X', elements: [labelledField] },
      active,
      active,
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ ...LIVE_ACTIVE_SEARCH_INPUT, text: '' }],
      },
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ ...LIVE_ACTIVE_SEARCH_INPUT, text: 'Mirchi' }],
      },
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ text: 'Mirchi Dating', className: 'android.widget.TextView' }],
      },
    ],
  })

  const result = execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke)

  assert.equal(result.action, 'search')
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'tap').map(({ args }) => args),
    [
      ['--desc', 'Search apps & games'],
      ['--text', 'Dil Mil'],
      ['--desc', 'Clear'],
    ],
  )
})

test('search binds the captured labelled Compose child to its one containing blank EditText', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      composeSearchDump(),
      composeSearchDump(),
      composeSearchDump({ ...CAPTURED_COMPOSE_SEARCH_INPUT, text: 'Mirchi' }),
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ text: 'Mirchi - South Asian Dating', className: 'android.widget.TextView' }],
      },
    ],
  })

  const result = execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke)

  assert.equal(result.action, 'search')
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'tap').map(({ args }) => args),
    [['--text', 'Search apps & games']],
  )
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'type').map(({ args }) => args),
    [['--text', 'Mirchi']],
  )
  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'key').map(({ args }) => args),
    [['--name', 'enter']],
  )
})

test('search clears a non-empty geometrically bound Compose input before typing', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const staleInput = { ...CAPTURED_COMPOSE_SEARCH_INPUT, text: 'Dil Mil' }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      composeSearchDump(staleInput),
      composeSearchDump(staleInput),
      composeSearchDump(),
      composeSearchDump({ ...CAPTURED_COMPOSE_SEARCH_INPUT, text: 'Mirchi' }),
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ text: 'Mirchi - South Asian Dating', className: 'android.widget.TextView' }],
      },
    ],
  })

  execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke)

  assert.deepEqual(
    android.calls.filter(({ command }) => command === 'key').map(({ args }) => args),
    [
      ['--code', '123'],
      ...Array.from({ length: 7 }, () => ['--name', 'delete']),
      ['--name', 'enter'],
    ],
  )
  const typeCall = android.calls.findIndex(({ command }) => command === 'type')
  const finalDelete = android.calls.findLastIndex(
    ({ command, args }) => command === 'key' && args.includes('delete'),
  )
  assert.ok(finalDelete < typeCall)
})

test('search refuses unbound, ambiguously bound, and lookalike Compose inputs', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const secondContainingInput = {
    ...CAPTURED_COMPOSE_SEARCH_INPUT,
    bounds: { x1: 132, y1: 88, x2: 948, y2: 220, x: 540, y: 154 },
  }
  const nonContainingInput = {
    ...CAPTURED_COMPOSE_SEARCH_INPUT,
    resourceId: 'com.android.vending:id/search_box',
    bounds: { x1: 600, y1: 88, x2: 926, y2: 220, x: 763, y: 154 },
  }
  const lookalikeInput = {
    ...CAPTURED_COMPOSE_SEARCH_INPUT,
    resourceId: 'com.android.vending:id/search_box',
    className: 'com.example.EditText',
  }
  const cases = [
    ['no input', [CAPTURED_COMPOSE_SEARCH_LABEL, CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP]],
    ['multiple containing inputs', [
      CAPTURED_COMPOSE_SEARCH_INPUT,
      secondContainingInput,
      CAPTURED_COMPOSE_SEARCH_LABEL,
      CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP,
    ]],
    ['non-containing input', [
      nonContainingInput,
      CAPTURED_COMPOSE_SEARCH_LABEL,
      CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP,
    ]],
    ['lookalike input class', [
      lookalikeInput,
      CAPTURED_COMPOSE_SEARCH_LABEL,
      CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP,
    ]],
  ]

  for (const [name, elements] of cases) {
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: { ok: true, serial: '976X23G9X', elements },
    })

    assert.throws(
      () => execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke),
      undefined,
      name,
    )
    assert.equal(android.calls.some(({ command }) => command === 'type'), false, name)
    assert.equal(android.calls.some(({ command }) => command === 'key'), false, name)
  }
})

async function assertMalformedComposeSearchLabelRefused(label) {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const unrelatedInput = {
    ...CAPTURED_COMPOSE_SEARCH_INPUT,
    resourceId: 'com.android.vending:id/search_box',
    bounds: { x1: 600, y1: 300, x2: 926, y2: 432, x: 763, y: 366 },
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: {
      ok: true,
      serial: '976X23G9X',
      elements: [unrelatedInput, label, CAPTURED_COMPOSE_SEARCH_NAVIGATE_UP],
    },
  })

  assert.throws(() => execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke))
  assert.equal(android.calls.some(({ command }) => command === 'type'), false)
  assert.equal(android.calls.some(({ command }) => command === 'key'), false)
}

test('search refuses a labelled Compose child with missing bounds before typing', async () => {
  await assertMalformedComposeSearchLabelRefused({
    ...CAPTURED_COMPOSE_SEARCH_LABEL,
    bounds: undefined,
  })
})

test('search refuses a labelled Compose child with zero-area bounds before typing', async () => {
  await assertMalformedComposeSearchLabelRefused({
    ...CAPTURED_COMPOSE_SEARCH_LABEL,
    bounds: { x1: 154, y1: 121, x2: 154, y2: 187, x: 154, y: 154 },
  })
})

test('search refuses unsafe surfaces around a geometrically bound Compose input', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const cases = [
    ['account', 'Choose an account'],
    ['identity', 'Verify it’s you'],
    ['permission', 'Grant permission to continue'],
  ]

  for (const [category, prompt] of cases) {
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: composeSearchDump(CAPTURED_COMPOSE_SEARCH_INPUT, [{ text: prompt }]),
    })

    assert.throws(
      () => execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke),
      new RegExp(`unsafe_search_surface: ${category}`),
      category,
    )
    assert.equal(android.calls.some(({ command }) => command === 'type'), false, category)
    assert.equal(android.calls.some(({ command }) => command === 'key'), false, category)
  }
})

test('candidates returns ordered bounded cards and collapses geometry-identical duplicates', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const duplicate = { ...FIRST_DIL_MIL_RESULT }
  const dumps = searchDumps('Dil Mil')
  dumps[4] = {
    ...dumps[4],
    elements: withResultsHeader([FIRST_DIL_MIL_RESULT, duplicate, SECOND_DIL_MIL_RESULT]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: dumps,
  })

  const result = execute(parseOptions(['candidates', '--query', 'Dil Mil']), android.invoke)

  assert.equal(result.action, 'candidates')
  assert.deepEqual(result.candidates, [
    {
      resultIndex: 0,
      title: 'Dil Mil: South Asian Dating',
      field: 'text',
      bounds: FIRST_DIL_MIL_RESULT.bounds,
    },
    {
      resultIndex: 1,
      title: 'Dil Mil Dating App',
      field: 'desc',
      bounds: SECOND_DIL_MIL_RESULT.bounds,
    },
  ])
})

test('candidates extracts exact titles from captured cards and excludes search-field descendants', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const dumps = searchDumps('Dil Mil')
  dumps[4] = {
    ...dumps[4],
    elements: withResultsHeader([
      CAPTURED_RESULTS_SEARCH_FIELD,
      CAPTURED_RESULTS_SEARCH_CHILD,
      ...CAPTURED_DIL_MIL_CARDS,
    ]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  const result = execute(parseOptions(['candidates', '--query', 'Dil Mil']), android.invoke)

  assert.deepEqual(result.candidates, CAPTURED_DIL_MIL_CARDS.map((card, resultIndex) => ({
    resultIndex,
    title: 'Dil Mil: South Asian Dating',
    field: 'desc',
    bounds: card.bounds,
  })))
})

test('candidates excludes the captured query text using the fully observed search header', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const dumps = searchDumps('Dil Mil')
  dumps[4] = {
    ...dumps[4],
    elements: [
      ...CAPTURED_RESULTS_HEADER,
      CAPTURED_RESULTS_SEARCH_CHILD,
      ...CAPTURED_DIL_MIL_CARDS,
    ],
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  const result = execute(parseOptions(['candidates', '--query', 'Dil Mil']), android.invoke)

  assert.deepEqual(result.candidates, CAPTURED_DIL_MIL_CARDS.map((card, resultIndex) => ({
    resultIndex,
    title: 'Dil Mil: South Asian Dating',
    field: 'desc',
    bounds: card.bounds,
  })))
})

test('candidates refuses discovery without every observed header anchor', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const dumps = searchDumps('Dil Mil')
  dumps[4] = {
    ...dumps[4],
    elements: [
      ...CAPTURED_RESULTS_HEADER.slice(0, 2),
      CAPTURED_RESULTS_SEARCH_CHILD,
      ...CAPTURED_DIL_MIL_CARDS,
    ],
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  assert.throws(
    () => execute(parseOptions(['candidates', '--query', 'Dil Mil']), android.invoke),
    /search_header_not_proven/,
  )
})

test('search requires the exact Android EditText class for active-session recognition and post-clear verification', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const lookalikeInput = { ...LIVE_ACTIVE_SEARCH_INPUT, className: 'com.example.EditText' }
  const pairedLookalikeDump = {
    ...LIVE_ACTIVE_SEARCH_DUMP,
    elements: [
      lookalikeInput,
      LIVE_ACTIVE_SEARCH_CLEAR,
      { text: '', desc: 'Navigate up', resourceId: '', className: 'android.view.View' },
    ],
  }
  const recognitionAndroid = fakeAndroid(PLAY_STORE_PACKAGE, { dump: pairedLookalikeDump })

  assert.throws(
    () => execute(parseOptions(['search', '--query', 'Mirchi']), recognitionAndroid.invoke),
    /search_navigation_control_not_found/,
  )
  assert.equal(
    recognitionAndroid.calls.some(({ command }) => ['tap', 'type', 'key'].includes(command)),
    false,
  )

  const postClearAndroid = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      LIVE_ACTIVE_SEARCH_DUMP,
      LIVE_ACTIVE_SEARCH_DUMP,
      {
        ok: true,
        serial: '976X23G9X',
        elements: [{ ...lookalikeInput, text: '' }],
      },
    ],
  })

  assert.throws(
    () => execute(parseOptions(['search', '--query', 'Mirchi']), postClearAndroid.invoke),
    /active_search_input_not_visible_after_clear/,
  )
  assert.equal(
    postClearAndroid.calls.some(({ command }) => ['type', 'key'].includes(command)),
    false,
  )
})

test('search rejects incomplete or ambiguous unlabeled active-session evidence', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const navigateUp = { text: '', desc: 'Navigate up', resourceId: '', className: 'android.view.View' }
  const searchNavigation = { text: '', desc: 'Search', resourceId: '', className: 'android.view.View' }
  const secondInput = {
    ...LIVE_ACTIVE_SEARCH_INPUT,
    text: 'Other value',
    bounds: { x1: 154, y1: 300, x2: 926, y2: 432, x: 540, y: 366 },
  }
  const cases = [
    ['arbitrary unlabeled EditText', [{ ...LIVE_ACTIVE_SEARCH_INPUT, text: 'Draft' }, searchNavigation]],
    ['multiple visible inputs', [LIVE_ACTIVE_SEARCH_INPUT, secondInput, LIVE_ACTIVE_SEARCH_CLEAR, navigateUp, searchNavigation]],
    ['missing Clear', [LIVE_ACTIVE_SEARCH_INPUT, navigateUp, searchNavigation]],
    ['duplicate Clear', [LIVE_ACTIVE_SEARCH_INPUT, LIVE_ACTIVE_SEARCH_CLEAR, { ...LIVE_ACTIVE_SEARCH_CLEAR }, navigateUp, searchNavigation]],
    ['input without geometry', [{ ...LIVE_ACTIVE_SEARCH_INPUT, bounds: undefined }, LIVE_ACTIVE_SEARCH_CLEAR, navigateUp, searchNavigation]],
    ['input with zero geometry', [{ ...LIVE_ACTIVE_SEARCH_INPUT, bounds: { x1: 0, y1: 0, x2: 0, y2: 0 } }, LIVE_ACTIVE_SEARCH_CLEAR, navigateUp, searchNavigation]],
    ['Clear without geometry', [LIVE_ACTIVE_SEARCH_INPUT, { ...LIVE_ACTIVE_SEARCH_CLEAR, bounds: undefined }, navigateUp, searchNavigation]],
  ]

  for (const [name, elements] of cases) {
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: { ok: true, serial: '976X23G9X', elements },
    })

    assert.throws(
      () => execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke),
      undefined,
      name,
    )
    assert.equal(
      android.calls.some(({ command }) => ['tap', 'type', 'key'].includes(command)),
      false,
      name,
    )
  }
})

test('search rejects account, identity, and permission surfaces shaped like the active session', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const cases = [
    ['account', 'Choose an account'],
    ['identity', 'Verify it’s you'],
    ['permission', 'Grant permission to continue'],
  ]

  for (const [category, prompt] of cases) {
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: {
        ...LIVE_ACTIVE_SEARCH_DUMP,
        elements: [...LIVE_ACTIVE_SEARCH_DUMP.elements, { text: prompt }],
      },
    })

    assert.throws(
      () => execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke),
      new RegExp(`unsafe_search_surface: ${category}`),
      category,
    )
    assert.equal(
      android.calls.some(({ command }) => ['tap', 'type', 'key'].includes(command)),
      false,
      category,
    )
  }
})

test('search refuses to type when the fresh post-tap dump has no identified search input', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: [
      {
        ok: true,
        serial: 'pixel-3',
        elements: [{ desc: 'Search apps & games', className: 'android.widget.EditText' }],
      },
      {
        ok: true,
        serial: 'pixel-3',
        elements: [{
          text: 'adithya@example.com',
          desc: 'Email or phone',
          resourceId: 'com.android.vending:id/account_name',
          className: 'android.widget.EditText',
        }],
      },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Mirchi' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Mirchi Dating' }] },
    ],
  })

  assert.throws(
    () => execute(parseOptions(['search', '--query', 'Mirchi']), android.invoke),
    /search_input_not_visible_after_tap/,
  )
  assert.equal(android.calls.some(({ command }) => command === 'type'), false)
  assert.equal(android.calls.some(({ command }) => command === 'key'), false)
})

test('search preserves the failed selector stage and child Android error', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    tap: { ok: false, error: 'element_not_found: observed Search has zero bounds' },
  })

  assert.throws(
    () => execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke),
    /search_navigation_tap_failed: element_not_found: observed Search has zero bounds/,
  )
})

test('search treats the shared key contract as strict', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil'),
    key: { ok: false, error: 'key_required' },
  })

  assert.throws(
    () => execute(parseOptions(['search', '--query', 'Dil Mil']), android.invoke),
    /search_submit_failed: key_required/,
  )
})

test('install-free distinguishes an exact listing from the search input containing the query', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const dumps = searchDumps('Dil Mil', [
    { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Install' }] },
    { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Install' }] },
    { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Pending...' }] },
  ])
  dumps[4] = {
    ok: true,
    serial: 'pixel-3',
    elements: withResultsHeader([
      { text: 'Dil Mil', className: 'android.widget.EditText' },
      { text: 'Dil Mil', className: 'android.widget.TextView' },
    ]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  const result = execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke, () => {})

  assert.equal(result.listing, 'Dil Mil')
})

test('install-free collapses identical duplicate listing and Install accessibility nodes', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const listing = {
    text: 'Dil Mil: South Asian Dating',
    desc: '',
    resourceId: 'com.android.vending:id/0_resource_name_obfuscated',
    className: 'android.widget.TextView',
    bounds: { x1: 40, y1: 200, x2: 760, y2: 280, x: 400, y: 240 },
  }
  const install = {
    text: 'Install',
    desc: '',
    resourceId: 'com.android.vending:id/0_resource_name_obfuscated',
    className: 'android.widget.Button',
    bounds: { x1: 780, y1: 200, x2: 1040, y2: 280, x: 910, y: 240 },
  }
  const detail = [listing, { ...listing }, install, { ...install }, { text: 'In-app purchases' }]
  const dumps = searchDumps('Dil Mil: South Asian Dating', [
    { ok: true, serial: 'pixel-3', elements: detail },
    { ok: true, serial: 'pixel-3', elements: detail },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [listing, { ...listing }, { text: 'Pending...' }],
    },
  ])
  dumps[4] = {
    ok: true,
    serial: 'pixel-3',
    elements: withResultsHeader([listing, { ...listing }]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: dumps,
  })

  const result = execute(
    parseOptions(['install-free', '--query', 'Dil Mil: South Asian Dating']),
    android.invoke,
    () => {},
  )

  assert.equal(result.listing, 'Dil Mil: South Asian Dating')
  assert.deepEqual(
    android.calls.filter(({ command, args }) => command === 'tap' && (
      args.includes('Dil Mil: South Asian Dating') || args.includes('Install')
    )).map(({ args }) => args),
    [
      ['--text', 'Dil Mil: South Asian Dating'],
      ['--text', 'Install'],
    ],
  )
})

test('install-free guards same-bounds text and description Install nodes with one exact final selector', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const installBounds = { x1: 780, y1: 200, x2: 1040, y2: 280, x: 910, y: 240 }
  const detail = [
    { text: 'Mirchi - South Asian Dating' },
    {
      text: 'Install',
      desc: '',
      resourceId: '',
      className: 'android.widget.TextView',
      bounds: installBounds,
    },
    {
      text: '',
      desc: 'Install',
      resourceId: '',
      className: 'android.view.View',
      bounds: { ...installBounds },
    },
    { text: 'In-app purchases' },
  ]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Mirchi - South Asian Dating', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      {
        ok: true,
        serial: 'pixel-3',
        elements: [{ text: 'Mirchi - South Asian Dating' }, { text: 'Pending...' }],
      },
    ]),
  })

  const result = execute(
    parseOptions(['install-free', '--query', 'Mirchi - South Asian Dating']),
    android.invoke,
    () => {},
  )

  assert.equal(result.installState, 'progress')
  const installTaps = android.calls.filter(
    ({ command, args }) => command === 'tap' && args.includes('Install'),
  )
  assert.equal(installTaps.length, 1)
  assert.deepEqual(installTaps[0].args.slice(0, 8), [
    '--index', '1',
    '--text', 'Install',
    '--class', 'android.widget.TextView',
    '--bounds', '[780,200][1040,280]',
  ])
  assert.equal(installTaps[0].args.includes('--unique'), false)
  assert.equal(installTaps[0].args.includes('--x'), false)
  const rejectPatterns = repeatedOptionValues(installTaps[0].args, '--reject-regex')
  assert.equal(rejectPatterns.length, 10)
  for (const prompt of [
    '$1.99',
    'Pay now',
    'Payment required',
    'Add a payment method',
    'Free trial',
    'Select an account',
    'Verify your identity',
    'Permission required',
    'Not owned',
    'Guardian approval needed',
  ]) {
    assert.equal(rejectPatterns.some((pattern) => new RegExp(pattern, 'i').test(prompt)), true, prompt)
  }
  const installTap = android.calls.indexOf(installTaps[0])
  assert.deepEqual(android.calls.slice(installTap - 2, installTap).map(({ command }) => command), [
    'current', 'dump',
  ])
})

test('install-free requires a result index for same-metadata listings at different bounds', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const safeDetail = [{ text: 'Dil Mil' }, { text: 'Install' }]
  const dumps = searchDumps('Dil Mil', [
    { ok: true, serial: 'pixel-3', elements: safeDetail },
    { ok: true, serial: 'pixel-3', elements: safeDetail },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [{ text: 'Dil Mil' }, { text: 'Pending...' }],
    },
  ])
  dumps[4] = {
    ok: true,
    serial: 'pixel-3',
    elements: withResultsHeader([
      {
        text: 'Dil Mil',
        resourceId: 'listing',
        className: 'android.widget.TextView',
        bounds: { x1: 40, y1: 300, x2: 760, y2: 380, x: 400, y: 340 },
      },
      {
        text: 'Dil Mil',
        resourceId: 'listing',
        className: 'android.widget.TextView',
        bounds: { x1: 40, y1: 600, x2: 760, y2: 680, x: 400, y: 640 },
      },
      { text: 'Dating' },
    ]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  assert.throws(
    () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke),
    /result_index_required/,
  )
  assert.equal(android.calls.filter(({ command }) => command === 'tap').length, 2)
})

test('install-free requires a result index when search returns multiple distinct cards', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const dumps = searchDumps('Dil Mil')
  dumps[4] = {
    ...dumps[4],
    elements: withResultsHeader([FIRST_DIL_MIL_RESULT, SECOND_DIL_MIL_RESULT]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  assert.throws(
    () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke, () => {}),
    /result_index_required/,
  )
  assert.equal(
    android.calls.some(({ command, args }) => command === 'tap' && args.includes('--x')),
    false,
  )
})

test('install-free refuses an explicit index when the result header is incomplete', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [
    { text: 'Dil Mil' },
    { text: 'Install' },
  ]
  const dumps = searchDumps('Dil Mil', [
    { ok: true, serial: 'pixel-3', elements: detail },
    { ok: true, serial: 'pixel-3', elements: detail },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [{ text: 'Dil Mil' }, { text: 'Pending...' }],
    },
  ])
  dumps[4] = {
    ...dumps[4],
    elements: [
      ...CAPTURED_RESULTS_HEADER.slice(0, 2),
      CAPTURED_RESULTS_SEARCH_CHILD,
      CAPTURED_DIL_MIL_CARDS[0],
    ],
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  assert.throws(
    () => execute(
      parseOptions(['install-free', '--query', 'Dil Mil', '--result-index', '0']),
      android.invoke,
      () => {},
    ),
    /search_header_not_proven/,
  )
  const submit = android.calls.findIndex(
    ({ command, args }) => command === 'key' && args.includes('enter'),
  )
  assert.equal(
    android.calls.slice(submit + 1).some(({ command }) => command === 'tap'),
    false,
  )
})

test('install-free selects only the explicit candidate and keeps its exact title through proof', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const selectedTitle = 'Dil Mil Dating App'
  const detail = [
    { ...SECOND_DIL_MIL_RESULT },
    {
      text: 'Install',
      desc: '',
      resourceId: 'install',
      className: 'android.widget.Button',
      bounds: { x1: 780, y1: 600, x2: 1040, y2: 680, x: 910, y: 640 },
    },
  ]
  const dumps = searchDumps('Dil Mil', [
    { ok: true, serial: 'pixel-3', elements: detail },
    { ok: true, serial: 'pixel-3', elements: detail },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [{ ...SECOND_DIL_MIL_RESULT }, { text: 'Pending...' }],
    },
  ])
  dumps[4] = {
    ...dumps[4],
    elements: withResultsHeader([FIRST_DIL_MIL_RESULT, SECOND_DIL_MIL_RESULT]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  const result = execute(
    parseOptions(['install-free', '--query', 'Dil Mil', '--result-index', '1']),
    android.invoke,
    () => {},
  )

  assert.equal(result.query, 'Dil Mil')
  assert.equal(result.listing, selectedTitle)
  assert.equal(result.resultIndex, 1)
  const resultTap = android.calls.find(
    ({ command, args }) => command === 'tap' && args.includes(selectedTitle),
  )
  assert.deepEqual(resultTap?.args.slice(0, 8), [
    '--index', '4',
    '--desc', selectedTitle,
    '--class', 'android.widget.TextView',
    '--bounds', '[40,600][760,680]',
  ])
  assert.equal(resultTap?.args.includes('--unique'), false)
  assert.equal(resultTap?.args.includes('--x'), false)
  assert.equal(repeatedOptionValues(resultTap?.args || [], '--reject-regex').length, 10)
  assert.equal(
    android.calls.some(({ command, args }) => (
      command === 'tap' && args.includes('Dil Mil: South Asian Dating')
    )),
    false,
  )
})

test('install-free stops when the generic final guard refuses a stale or moved selected card', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const selectedTitle = 'Dil Mil Dating App'
  const detail = [
    { ...SECOND_DIL_MIL_RESULT },
    {
      text: 'Install',
      desc: '',
      resourceId: 'install',
      className: 'android.widget.Button',
      bounds: { x1: 780, y1: 600, x2: 1040, y2: 680, x: 910, y: 640 },
    },
  ]
  const dumps = searchDumps('Dil Mil', [
    { ok: true, serial: 'pixel-3', elements: detail },
    { ok: true, serial: 'pixel-3', elements: detail },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [{ ...SECOND_DIL_MIL_RESULT }, { text: 'Pending...' }],
    },
  ])
  dumps[4] = {
    ...dumps[4],
    elements: withResultsHeader([FIRST_DIL_MIL_RESULT, SECOND_DIL_MIL_RESULT]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: dumps,
    tap: (args) => args.includes(selectedTitle) && args.includes('--bounds')
      ? { ok: false, error: 'element_not_found' }
      : { ok: true, serial: 'pixel-3', action: 'tap' },
  })

  assert.throws(
    () => execute(
      parseOptions(['install-free', '--query', 'Dil Mil', '--result-index', '1']),
      android.invoke,
      () => {},
    ),
    /listing_tap_failed: element_not_found/,
  )
  const guardedTap = android.calls.find(
    ({ command, args }) => command === 'tap' && args.includes(selectedTitle),
  )
  assert.ok(guardedTap)
  assert.equal(android.calls.at(-1), guardedTap)
  assert.equal(android.calls.some(({ command, args }) => command === 'tap' && args.includes('Install')), false)
})

test('install-free propagates a generic unsafe final-state refusal without polling or fallback tap', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const installBounds = { x1: 780, y1: 200, x2: 1040, y2: 280, x: 910, y: 240 }
  const detail = [
    { text: 'Mirchi - South Asian Dating' },
    {
      text: 'Install',
      desc: '',
      resourceId: '',
      className: 'android.widget.TextView',
      bounds: installBounds,
    },
    {
      text: '',
      desc: 'Install',
      resourceId: '',
      className: 'android.view.View',
      bounds: { ...installBounds },
    },
  ]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Mirchi - South Asian Dating', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      {
        ok: true,
        serial: 'pixel-3',
        elements: [{ text: 'Mirchi - South Asian Dating' }, { text: 'Pending...' }],
      },
    ]),
    tap: (args) => {
      const guards = repeatedOptionValues(args, '--reject-regex')
      if (args.includes('Install') && guards.some((pattern) => new RegExp(pattern, 'i').test('Choose an account'))) {
        return { ok: false, error: 'tap_rejected_by_guard' }
      }
      return { ok: true, serial: 'pixel-3', action: 'tap' }
    },
  })

  assert.throws(
    () => execute(
      parseOptions(['install-free', '--query', 'Mirchi - South Asian Dating']),
      android.invoke,
      () => {},
    ),
    /install_tap_failed: tap_rejected_by_guard/,
  )
  const guardedTap = android.calls.find(
    ({ command, args }) => command === 'tap' && args.includes('Install'),
  )
  assert.ok(guardedTap)
  assert.equal(android.calls.at(-1), guardedTap)
  assert.equal(guardedTap.args.includes('--x'), false)
})

test('install-free taps the full composite selector while proving the separate exact title', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const selectedCard = CAPTURED_DIL_MIL_CARDS[0]
  const detail = [
    selectedCard,
    {
      text: 'Install',
      desc: '',
      resourceId: 'install',
      className: 'android.widget.Button',
      bounds: { x1: 780, y1: 410, x2: 1040, y2: 490, x: 910, y: 450 },
    },
  ]
  const dumps = searchDumps('Dil Mil', [
    { ok: true, serial: 'pixel-3', elements: detail },
    { ok: true, serial: 'pixel-3', elements: detail },
    {
      ok: true,
      serial: 'pixel-3',
      elements: [selectedCard, { text: 'Pending...' }],
    },
  ])
  dumps[4] = {
    ...dumps[4],
    elements: withResultsHeader([
      CAPTURED_RESULTS_SEARCH_FIELD,
      CAPTURED_RESULTS_SEARCH_CHILD,
      selectedCard,
    ]),
  }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, { dump: dumps })

  const result = execute(
    parseOptions(['install-free', '--query', 'Dil Mil']),
    android.invoke,
    () => {},
  )

  assert.equal(result.listing, 'Dil Mil: South Asian Dating')
  assert.deepEqual(
    android.calls.filter(({ command, args }) => (
      command === 'tap' && args.includes(CAPTURED_DIL_MIL_CARD_LABEL)
    )).map(({ args }) => args),
    [['--desc', CAPTURED_DIL_MIL_CARD_LABEL]],
  )
})

test('install-free refuses different, missing, or zero-area duplicate Install footprints', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const firstInstall = {
    text: 'Install',
    desc: '',
    resourceId: 'install',
    className: 'android.widget.Button',
    bounds: { x1: 780, y1: 200, x2: 1040, y2: 280, x: 910, y: 240 },
  }
  const cases = [
    ['different bounds', {
      text: '',
      desc: 'Install',
      resourceId: 'install',
      className: 'android.widget.Button',
      bounds: { x1: 780, y1: 600, x2: 1040, y2: 680, x: 910, y: 640 },
    }],
    ['missing bounds', {
      text: '',
      desc: 'Install',
      resourceId: 'install',
      className: 'android.widget.Button',
    }],
    ['zero-area bounds', {
      text: '',
      desc: 'Install',
      resourceId: 'install',
      className: 'android.widget.Button',
      bounds: { x1: 780, y1: 200, x2: 780, y2: 280, x: 780, y: 240 },
    }],
  ]

  for (const [name, secondInstall] of cases) {
    const detail = [
      { text: 'Dil Mil' },
      firstInstall,
      secondInstall,
    ]
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: searchDumps('Dil Mil', [
        { ok: true, serial: 'pixel-3', elements: detail },
        { ok: true, serial: 'pixel-3', elements: detail },
        {
          ok: true,
          serial: 'pixel-3',
          elements: [{ text: 'Dil Mil' }, { text: 'Pending...' }],
        },
      ]),
    })

    assert.throws(
      () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke, () => {}),
      /ambiguous_install_control/,
      name,
    )
    assert.equal(
      android.calls.some(({ command, args }) => command === 'tap' && (
        args.includes('Install') || args.includes('--x')
      )),
      false,
      name,
    )
  }
})

test('install-free runs a fresh exact preflight and refuses unsafe prompts before Install', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [{ text: 'Dil Mil' }, { text: 'Install' }, { text: 'Buy for $1.99' }]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
    ]),
  })

  assert.throws(
    () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke),
    /unsafe_prompt: price_or_purchase/,
  )
  assert.deepEqual(android.calls.slice(-3).map(({ command }) => command), ['dump', 'current', 'dump'])
  assert.equal(
    android.calls.some(({ command, args }) => command === 'tap' && args.includes('Install')),
    false,
  )
})

test('install-free refuses every documented unsafe prompt category before Install', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const cases = [
    ['price_or_purchase', 'Price: 4.99 USD'],
    ['price_or_purchase', 'Add a payment method'],
    ['subscription', 'Subscription required'],
    ['account', 'Select an account'],
    ['identity', 'Verify it’s you'],
    ['permission', 'Grant permission to continue'],
    ['ownership', "You don't own this item"],
    ['approval', 'Guardian approval needed'],
  ]

  for (const [category, prompt] of cases) {
    const detail = [{ text: 'Dil Mil' }, { text: 'Install' }, { text: prompt }]
    const android = fakeAndroid(PLAY_STORE_PACKAGE, {
      dump: searchDumps('Dil Mil', [
        { ok: true, serial: 'pixel-3', elements: detail },
        { ok: true, serial: 'pixel-3', elements: detail },
      ]),
    })

    assert.throws(
      () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke, () => {}),
      new RegExp(`unsafe_prompt: ${category}`),
      category,
    )
    assert.equal(
      android.calls.some(({ command, args }) => command === 'tap' && args.includes('Install')),
      false,
      category,
    )
  }
})

test('install-free permits an informational In-app purchases label alone', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [
    { text: 'Dil Mil' },
    { text: 'Install' },
    { text: 'In-app purchases' },
  ]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Pending...' }] },
    ]),
  })

  const result = execute(
    parseOptions(['install-free', '--query', 'Dil Mil']),
    android.invoke,
    () => {},
  )

  assert.equal(result.installState, 'progress')
  assert.equal(result.evidence, 'Pending...')
})

test('install-free requires an observed exact Install control', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [{ text: 'Dil Mil' }, { text: 'Get' }]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
    ]),
  })

  assert.throws(
    () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke),
    /install_control_not_found/,
  )
  assert.equal(
    android.calls.some(({ command, args }) => command === 'tap' && args.includes('Get')),
    false,
  )
})

test('install-free taps exact Install only after preflight and stops on visible progress', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [{ text: 'Dil Mil' }, { text: 'Install' }]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Pending...' }, { text: 'Cancel' }] },
    ]),
  })

  const result = execute(
    parseOptions(['install-free', '--query', 'Dil Mil']),
    android.invoke,
    () => {},
  )

  assert.deepEqual(result, {
    ok: true,
    action: 'install-free',
    id: 'play-store',
    name: 'Google Play Store',
    serial: 'pixel-3',
    package: PLAY_STORE_PACKAGE,
    query: 'Dil Mil',
    listing: 'Dil Mil',
    installState: 'progress',
    evidence: 'Pending...',
  })
  const installTap = android.calls.findIndex(
    ({ command, args }) => command === 'tap' && args.includes('Install'),
  )
  assert.ok(installTap > 0)
  assert.deepEqual(android.calls.slice(installTap - 2, installTap + 4).map(({ command }) => command), [
    'current', 'dump', 'tap', 'current', 'dump',
  ])
  assert.deepEqual(android.calls[installTap].args, ['--text', 'Install'])
})

test('install-free refuses an unsafe prompt on every fresh post-tap poll', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [{ text: 'Dil Mil' }, { text: 'Install' }]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Choose an account' }] },
    ]),
  })

  assert.throws(
    () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke, () => {}),
    /unsafe_prompt_after_install_tap: account/,
  )
})

test('install-free ignores unrelated Open and requires listing-specific progress evidence', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [{ text: 'Dil Mil' }, { text: 'Install' }]
  let pauses = 0
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Other App' }, { text: 'Open' }] },
      { ok: true, serial: 'pixel-3', elements: [{ text: 'Dil Mil' }, { text: 'Downloading...' }] },
    ]),
  })

  const result = execute(
    parseOptions(['install-free', '--query', 'Dil Mil']),
    android.invoke,
    () => { pauses += 1 },
  )

  assert.equal(result.installState, 'progress')
  assert.equal(result.evidence, 'Downloading...')
  assert.equal(pauses, 1)
})

test('install-free polling is bounded and reports the last visible evidence', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [{ text: 'Dil Mil' }, { text: 'Install' }]
  const unrelated = { ok: true, serial: 'pixel-3', elements: [{ text: 'Other App' }, { text: 'Open' }] }
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: searchDumps('Dil Mil', [
      { ok: true, serial: 'pixel-3', elements: detail },
      { ok: true, serial: 'pixel-3', elements: detail },
      ...Array.from({ length: 20 }, () => unrelated),
    ]),
  })

  assert.throws(
    () => execute(parseOptions(['install-free', '--query', 'Dil Mil']), android.invoke, () => {}),
    /install_state_timeout: listing=Dil Mil; last_visible=Other App \| Open/,
  )
})

test('observe-release extracts release notes and version information', async () => {
  const { PLAY_STORE_PACKAGE, execute, parseOptions } = await loadAdapter()
  const detail = [
    { text: "What's new", desc: '' },
    { text: 'Added voice messages and performance fixes', desc: '' },
    { text: 'Updated on', desc: '' },
    { text: 'Sep 1, 2026', desc: '' },
    { text: 'Version', desc: '' },
    { text: 'v3.14.0', desc: '' },
  ]
  const android = fakeAndroid(PLAY_STORE_PACKAGE, {
    dump: { ok: true, serial: 'pixel-3', elements: detail },
  })

  const result = execute(parseOptions(['observe-release', '--query', 'Dil Mil']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'observe-release')
  assert.equal(result.release.whatsNew, 'Added voice messages and performance fixes')
  assert.equal(result.release.updatedOn, 'Sep 1, 2026')
  assert.equal(result.release.version, 'v3.14.0')
})

test('the CLI file is executable as a direct JSON command surface', async () => {
  const path = fileURLToPath(moduleUrl)
  const { stat } = await import('node:fs/promises')
  const mode = (await stat(path)).mode

  assert.notEqual(mode & 0o111, 0)
})
