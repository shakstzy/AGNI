import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import {
  BUMBLE_PACKAGE,
  execute,
  parseOptions,
} from '../cli/bumble.mjs'

const adapterDirectory = new URL('..', import.meta.url)

function read(relativePath) {
  return readFileSync(new URL(relativePath, adapterDirectory), 'utf8')
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

const FOCUS = 'mCurrentFocus=Window{1 u0 com.bumble.app/com.bumble.app.ui.main.AppMainActivity}'
const CHAT_FOCUS = 'mCurrentFocus=Window{1 u0 com.bumble.app/com.bumble.app.ui.chat.ChatActivity}'

const TAB_BAR = [
  element({ desc: 'Profile', className: 'android.view.View', bounds: [0, 1868, 216, 2028] }),
  element({ text: 'Profile', className: 'android.widget.TextView', bounds: [65, 1967, 152, 2006] }),
  element({ desc: 'Discover', className: 'android.view.View', bounds: [216, 1868, 432, 2028] }),
  element({ text: 'Discover', className: 'android.widget.TextView', bounds: [265, 1967, 383, 2006] }),
  element({ desc: 'People', className: 'android.view.View', bounds: [432, 1868, 648, 2028] }),
  element({ text: 'People', className: 'android.widget.TextView', bounds: [493, 1967, 587, 2006] }),
  element({ desc: 'Liked You', className: 'android.view.View', bounds: [648, 1868, 864, 2028] }),
  element({ text: 'Liked You', className: 'android.widget.TextView', bounds: [693, 1967, 820, 2006] }),
  element({ desc: 'Chats', className: 'android.view.View', bounds: [864, 1868, 1080, 2028] }),
  element({ text: 'Chats', className: 'android.widget.TextView', bounds: [932, 1967, 1013, 2006] }),
]

const PEOPLE_SURFACE = [
  element({
    resourceId: 'com.bumble.app:id/mainApp_navigationTabBar',
    className: 'android.widget.FrameLayout',
    bounds: [0, 1868, 1080, 2028],
  }),
  ...TAB_BAR,
  element({ desc: 'Jaya’s main photo', className: 'android.view.View', bounds: [22, 253, 1058, 1571] }),
  element({ desc: 'Liked You', className: 'android.view.View', bounds: [77, 1173, 292, 1236] }),
  element({ text: 'Jaya, 27', className: 'android.widget.TextView', bounds: [77, 1258, 281, 1330] }),
  element({ text: 'Hospital at University of Texas', className: 'android.widget.TextView', bounds: [132, 1352, 696, 1406] }),
  element({ desc: 'Send SuperSwipe', resourceId: 'com.bumble.app:id/profile_details_badgeSuperSwipe', className: 'android.widget.FrameLayout', bounds: [849, 1362, 1014, 1527] }),
]

const DISCOVER_SURFACE = [
  ...TAB_BAR,
  element({ text: 'Recommended for you', className: 'android.widget.TextView', bounds: [44, 280, 800, 340] }),
  element({ desc: 'Pooja, 24, profile 1 of 2', className: 'android.widget.Button', bounds: [44, 413, 942, 1610] }),
  element({ desc: 'Meredith, 23, profile 2 of 2', className: 'android.widget.Button', bounds: [44, 1630, 942, 1800] }),
]

const PROFILE_OVERLAY = [
  element({ desc: 'Pooja’s main photo', className: 'android.view.View', bounds: [22, 253, 1058, 1200] }),
  element({ text: 'Pooja, 24', className: 'android.widget.TextView', bounds: [77, 1258, 281, 1330] }),
  element({ desc: 'Close', className: 'android.view.View', bounds: [44, 99, 154, 209] }),
  element({ desc: 'Not for me', className: 'android.view.View', bounds: [200, 1840, 420, 1970] }),
  element({ className: 'android.widget.Button', bounds: [200, 1840, 420, 1970] }),
  element({ desc: 'Like', className: 'android.view.View', bounds: [660, 1840, 880, 1970] }),
  element({ className: 'android.widget.Button', bounds: [660, 1840, 880, 1970] }),
  element({ desc: 'Send SuperSwipe', className: 'android.view.View', bounds: [849, 1362, 1014, 1527] }),
]

const LIKED_YOU_SURFACE = [
  ...TAB_BAR,
  element({ text: 'Liked You', className: 'android.widget.TextView', bounds: [44, 120, 400, 180] }),
  element({ text: 'Really into you • 17', className: 'android.widget.TextView', bounds: [44, 200, 400, 250] }),
  element({ text: 'All • 35', className: 'android.widget.TextView', bounds: [44, 260, 300, 310] }),
  element({ desc: 'Check out Dawn’s profile', className: 'android.view.View', bounds: [44, 400, 500, 700] }),
  element({ desc: 'Check out Priya’s profile', className: 'android.view.View', bounds: [540, 400, 1000, 700] }),
]

const CHATS_SURFACE = [
  ...TAB_BAR,
  element({
    text: 'Chats',
    resourceId: 'com.bumble.app:id/mainAppToolbarNavigation_title',
    className: 'android.widget.TextView',
    bounds: [44, 100, 200, 160],
  }),
  element({
    desc: 'Kobe, Date, match',
    resourceId: 'com.bumble.app:id/connectionItem_ringView',
    className: 'android.widget.Button',
    bounds: [33, 988, 248, 1203],
  }),
  element({
    text: 'Kobe',
    resourceId: 'com.bumble.app:id/connectionsItem_personName',
    className: 'android.widget.TextView',
    bounds: [270, 1000, 500, 1060],
  }),
  element({
    text: 'Your move',
    resourceId: 'com.bumble.app:id/connectionItem_badge',
    className: 'android.widget.TextView',
    bounds: [520, 1000, 800, 1060],
  }),
  element({
    text: 'Hey',
    resourceId: 'com.bumble.app:id/connectionsItem_message',
    className: 'android.widget.TextView',
    bounds: [270, 1070, 800, 1120],
  }),
  element({
    desc: '35 people like you! People are waiting to talk to you. ',
    resourceId: 'com.bumble.app:id/connections_beelinePromoContainer',
    className: 'android.widget.Button',
    bounds: [44, 240, 1036, 400],
  }),
]

const CHAT_THREAD = [
  element({
    text: 'Kobe',
    resourceId: 'com.bumble.app:id/chatToolbar_title',
    className: 'android.widget.TextView',
    bounds: [286, 123, 391, 185],
  }),
  element({ desc: 'Back', className: 'android.widget.ImageButton', bounds: [0, 77, 154, 231] }),
  element({ desc: 'Voice call', resourceId: 'com.bumble.app:id/chatToolbar_audioChatButton', className: 'android.widget.Button', bounds: [684, 88, 816, 220] }),
  element({ desc: 'Video call', resourceId: 'com.bumble.app:id/chatToolbar_videoChatButton', className: 'android.widget.Button', bounds: [816, 88, 948, 220] }),
  element({
    text: 'Aa',
    resourceId: 'com.bumble.app:id/chatInput_text',
    className: 'android.widget.EditText',
    bounds: [110, 1912, 882, 2011],
  }),
  element({ desc: 'Send', resourceId: 'com.bumble.app:id/chatInput_button_send', className: 'android.widget.Button', bounds: [904, 1929, 970, 1995] }),
]

function scriptedAndroid({ dumps, currents, focus = FOCUS } = {}) {
  const calls = []
  let dumpIndex = 0
  let currentIndex = 0
  const currentResults = currents || [{ ok: true, serial: 'pixel-3', focus }]
  return {
    calls,
    invoke(command, args, input) {
      calls.push({ command, args, ...(input === undefined ? {} : { input }) })
      if (command === 'packages') return { ok: true, serial: 'pixel-3', packages: [BUMBLE_PACKAGE] }
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
      if (command === 'wait') return { ok: true, serial: 'pixel-3', action: 'wait' }
      if (command === 'type-stdin') return { ok: true, serial: 'pixel-3', action: 'type-stdin' }
      if (command === 'key') return { ok: true, serial: 'pixel-3', action: 'key' }
      throw new Error(`unexpected_android_command: ${command}`)
    },
  }
}

test('Bumble adapter documents signed-in engagement without purchases or calls', () => {
  const adapter = read('ADAPTER.md')
  assert.match(adapter, /bumble\.mjs tab/)
  assert.match(adapter, /bumble\.mjs like/)
  assert.match(adapter, /bumble\.mjs pass/)
  assert.match(adapter, /bumble\.mjs chats/)
  assert.match(adapter, /bumble\.mjs send-message/)
  assert.match(adapter, /SuperSwipe/)
  assert.match(adapter, /Voice call|Video call/)
})

test('tab requires an observed main-app tab name', () => {
  assert.deepEqual(parseOptions(['tab', '--name', 'chats', '--serial', 'pixel-3']), {
    command: 'tab',
    name: 'chats',
    serial: 'pixel-3',
  })
  assert.throws(() => parseOptions(['tab']), /tab_name_required/)
  assert.throws(() => parseOptions(['tab', '--name', 'boost']), /unsupported_tab/)
})

test('tab Liked You taps the tab-bar control, not a card badge', () => {
  const android = scriptedAndroid({ dumps: [PEOPLE_SURFACE, LIKED_YOU_SURFACE] })
  const result = execute(parseOptions(['tab', '--name', 'liked-you']), android.invoke)
  assert.equal(result.action, 'tab')
  assert.equal(result.tab, 'liked-you')
  const tap = android.calls.find(({ command }) => command === 'tap')
  assert.ok(tap)
  assert.equal(tap.args[tap.args.indexOf('--desc') + 1], 'Liked You')
  assert.equal(tap.args[tap.args.indexOf('--bounds') + 1], '[648,1868][864,2028]')
})

test('cards lists visible People names without tapping SuperSwipe', () => {
  const android = scriptedAndroid({ dumps: [PEOPLE_SURFACE] })
  const result = execute(parseOptions(['cards']), android.invoke)
  assert.deepEqual(result.cards, [
    { name: 'Jaya', age: 27, subtitle: 'Hospital at University of Texas' },
  ])
  assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
})

test('discover lists recommended profile buttons', () => {
  const android = scriptedAndroid({ dumps: [DISCOVER_SURFACE] })
  const result = execute(parseOptions(['discover']), android.invoke)
  assert.deepEqual(result.cards, [
    { name: 'Pooja', age: 24, index: 1, total: 2 },
    { name: 'Meredith', age: 23, index: 2, total: 2 },
  ])
})

test('open-card taps the discover profile button for the requested name', () => {
  const android = scriptedAndroid({ dumps: [DISCOVER_SURFACE, PROFILE_OVERLAY] })
  const result = execute(parseOptions(['open-card', '--name', 'Pooja']), android.invoke)
  assert.equal(result.action, 'open-card')
  assert.equal(result.name, 'Pooja')
  const tap = android.calls.find(({ command }) => command === 'tap')
  assert.equal(tap.args[tap.args.indexOf('--desc') + 1], 'Pooja, 24, profile 1 of 2')
})

test('like requires confirmation and taps only Like, never SuperSwipe', () => {
  assert.throws(() => parseOptions(['like']), /like_confirmation_required/)
  const android = scriptedAndroid({ dumps: [PROFILE_OVERLAY, PROFILE_OVERLAY] })
  const result = execute(parseOptions(['like', '--confirm', 'like']), android.invoke)
  assert.equal(result.status, 'like-observed')
  const tap = android.calls.find(({ command }) => command === 'tap')
  assert.equal(tap.args[tap.args.indexOf('--desc') + 1], 'Like')
  assert.equal(tap.args.includes('Send SuperSwipe'), false)
})

test('pass requires confirmation and taps Not for me', () => {
  assert.throws(() => parseOptions(['pass']), /pass_confirmation_required/)
  const android = scriptedAndroid({ dumps: [PROFILE_OVERLAY, PROFILE_OVERLAY] })
  const result = execute(parseOptions(['pass', '--confirm', 'pass']), android.invoke)
  assert.equal(result.status, 'pass-observed')
  const tap = android.calls.find(({ command }) => command === 'tap')
  assert.equal(tap.args[tap.args.indexOf('--desc') + 1], 'Not for me')
})

test('liked-you lists visible inbound profiles without opening Beeline paywalls', () => {
  const android = scriptedAndroid({ dumps: [LIKED_YOU_SURFACE] })
  const result = execute(parseOptions(['liked-you']), android.invoke)
  assert.deepEqual(result.profiles, [{ name: 'Dawn' }, { name: 'Priya' }])
  assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
})

test('chats lists matches from observed row ids and does not tap the Beeline promo', () => {
  const android = scriptedAndroid({ dumps: [CHATS_SURFACE] })
  const result = execute(parseOptions(['chats']), android.invoke)
  assert.deepEqual(result.chats, [
    { name: 'Kobe', preview: 'Hey', badge: 'Your move' },
  ])
  assert.equal(android.calls.some(({ command }) => command === 'tap'), false)
})

test('open-chat taps the match row for the requested name', () => {
  const android = scriptedAndroid({
    dumps: [CHATS_SURFACE, CHAT_THREAD],
    currents: [
      { ok: true, serial: 'pixel-3', focus: FOCUS },
      { ok: true, serial: 'pixel-3', focus: FOCUS },
      { ok: true, serial: 'pixel-3', focus: CHAT_FOCUS },
    ],
  })
  const result = execute(parseOptions(['open-chat', '--name', 'Kobe']), android.invoke)
  assert.equal(result.action, 'open-chat')
  assert.equal(result.name, 'Kobe')
  const tap = android.calls.find(({ command }) => command === 'tap')
  assert.equal(tap.args[tap.args.indexOf('--desc') + 1], 'Kobe, Date, match')
})

test('send-message accepts one stdin JSON message and never a CLI secret', () => {
  assert.deepEqual(parseOptions(['send-message', '--confirm', 'send']), {
    command: 'send-message',
    confirm: 'send',
  })
  assert.throws(() => parseOptions(['send-message', '--confirm', 'send', '--message', 'hi-secret']), /send_message_options/)
  const android = scriptedAndroid({
    dumps: [CHAT_THREAD, CHAT_THREAD, CHAT_THREAD, CHAT_THREAD],
    focus: CHAT_FOCUS,
  })
  const result = execute(
    parseOptions(['send-message', '--confirm', 'send']),
    android.invoke,
    JSON.stringify({ message: 'hello-private' }),
  )
  assert.equal(result.status, 'message-submitted')
  assert.doesNotMatch(JSON.stringify(result), /hello-private/)
  const typed = android.calls.find(({ command }) => command === 'type-stdin')
  assert.equal(typed.input, 'hello-private')
  const send = android.calls.filter(({ command }) => command === 'tap').at(-1)
  assert.equal(send.args[send.args.indexOf('--desc') + 1], 'Send')
})

test('engagement actions fail closed on SuperSwipe, calls, and purchases', () => {
  const purchase = scriptedAndroid({
    dumps: [[
      ...PROFILE_OVERLAY,
      element({ text: 'Subscribe to Bumble Boost', className: 'android.widget.TextView', bounds: [100, 800, 900, 900] }),
    ]],
  })
  assert.throws(
    () => execute(parseOptions(['like', '--confirm', 'like']), purchase.invoke),
    /unsafe_engagement_surface: purchase/,
  )
})
