import assert from 'node:assert/strict'
import test from 'node:test'
import {
  BUMBLE_PACKAGE,
  execute,
  parseOptions,
} from '../cli/bumble.mjs'

function element({ desc = '', text = '', resourceId = '', className = 'android.view.View', bounds }) {
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
  element({ desc: 'Profile', bounds: [0, 1868, 216, 2028] }),
  element({ desc: 'Discover', bounds: [216, 1868, 432, 2028] }),
  element({ desc: 'People', bounds: [432, 1868, 648, 2028] }),
  element({ desc: 'Liked You', bounds: [648, 1868, 864, 2028] }),
  element({ desc: 'Chats', bounds: [864, 1868, 1080, 2028] }),
]

const CHATS_PAGE_1 = [
  ...TAB_BAR,
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
]

const CHATS_PAGE_2 = [
  ...TAB_BAR,
  element({
    desc: 'Aaditi, Date, match',
    resourceId: 'com.bumble.app:id/connectionItem_ringView',
    className: 'android.widget.Button',
    bounds: [33, 988, 248, 1203],
  }),
  element({
    text: 'Aaditi',
    resourceId: 'com.bumble.app:id/connectionsItem_personName',
    className: 'android.widget.TextView',
    bounds: [270, 1000, 500, 1060],
  }),
  element({
    text: 'mozarts tonight?',
    resourceId: 'com.bumble.app:id/connectionsItem_message',
    className: 'android.widget.TextView',
    bounds: [270, 1070, 800, 1120],
  }),
]

const CHAT_THREAD_MESSAGES = [
  element({
    text: 'Kobe',
    resourceId: 'com.bumble.app:id/chatToolbar_title',
    className: 'android.widget.TextView',
    bounds: [286, 123, 391, 185],
  }),
  element({
    desc: 'Navigate up',
    className: 'android.widget.ImageButton',
    bounds: [0, 77, 154, 231],
  }),
  element({
    desc: 'View profile',
    resourceId: 'com.bumble.app:id/chatToolbar_avatar',
    className: 'android.widget.ImageView',
    bounds: [176, 100, 264, 188],
  }),
  element({
    text: 'Hey! Are you in Austin? 512-555-0199',
    resourceId: 'com.bumble.app:id/chatMessage_text',
    className: 'android.widget.TextView',
    bounds: [100, 400, 700, 480],
  }),
  element({
    text: 'Aa',
    resourceId: 'com.bumble.app:id/chatInput_text',
    className: 'android.widget.EditText',
    bounds: [110, 1912, 882, 2011],
  }),
  element({
    desc: 'Send',
    resourceId: 'com.bumble.app:id/chatInput_button_send',
    className: 'android.widget.Button',
    bounds: [904, 1929, 970, 1995],
  }),
]

const PROFILE_PAGE_1 = [
  element({ desc: 'Close', bounds: [44, 99, 154, 209] }),
  element({ text: 'Kobe, 25', className: 'android.widget.TextView', bounds: [77, 1258, 281, 1330] }),
  element({ text: 'Software Engineer', className: 'android.widget.TextView', bounds: [77, 1350, 500, 1400] }),
  element({ text: 'UT Austin', className: 'android.widget.TextView', bounds: [77, 1410, 400, 1460] }),
]

function scriptedAndroid({ dumps = [], currents = [], focus = FOCUS } = {}) {
  const calls = []
  let dumpIndex = 0
  let currentIndex = 0
  const currentResults = currents.length ? currents : [{ ok: true, serial: 'pixel-3', focus }]
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
        const elements = dumps[Math.min(dumpIndex, dumps.length - 1)] || []
        dumpIndex += 1
        return { ok: true, serial: 'pixel-3', elements }
      }
      if (command === 'tap') return { ok: true, serial: 'pixel-3', action: 'tap' }
      if (command === 'swipe') return { ok: true, serial: 'pixel-3', action: 'swipe' }
      if (command === 'type-stdin') return { ok: true, serial: 'pixel-3', action: 'type-stdin' }
      if (command === 'screenshot') return { ok: true, serial: 'pixel-3', out: '/tmp/test.png' }
      throw new Error(`unexpected_android_command: ${command}`)
    },
  }
}

test('parseOptions accepts new batch commands', () => {
  assert.deepEqual(parseOptions(['crawl-chats', '--limit', '20', '--scrolls', '5']), {
    command: 'crawl-chats',
    limit: '20',
    scrolls: '5',
  })
  assert.deepEqual(parseOptions(['inspect-thread', '--name', 'Kobe']), {
    command: 'inspect-thread',
    name: 'Kobe',
  })
  assert.deepEqual(parseOptions(['inspect-profile', '--name', 'Kobe']), {
    command: 'inspect-profile',
    name: 'Kobe',
  })
  assert.deepEqual(parseOptions(['send-batch', '--confirm', 'send']), {
    command: 'send-batch',
    confirm: 'send',
  })
})

test('crawl-chats scrolls and catalogs deduplicated chats', () => {
  const android = scriptedAndroid({
    dumps: [CHATS_PAGE_1, CHATS_PAGE_2, CHATS_PAGE_2],
    focus: FOCUS,
  })
  const result = execute(parseOptions(['crawl-chats', '--scrolls', '2']), android.invoke)
  assert.equal(result.action, 'crawl-chats')
  assert.ok(Array.isArray(result.chats))
  assert.equal(result.chats.length, 2)
  assert.equal(result.chats[0].name, 'Kobe')
  assert.equal(result.chats[0].badge, 'Your move')
  assert.equal(result.chats[1].name, 'Aaditi')
  assert.ok(android.calls.some(({ command }) => command === 'swipe'))
})

test('inspect-thread extracts messages, sender attribution, and phone number', () => {
  const android = scriptedAndroid({
    dumps: [CHATS_PAGE_1, CHAT_THREAD_MESSAGES, CHAT_THREAD_MESSAGES, CHATS_PAGE_1],
    currents: [
      { ok: true, serial: 'pixel-3', focus: FOCUS },
      { ok: true, serial: 'pixel-3', focus: CHAT_FOCUS },
      { ok: true, serial: 'pixel-3', focus: CHAT_FOCUS },
      { ok: true, serial: 'pixel-3', focus: FOCUS },
    ],
  })
  const result = execute(parseOptions(['inspect-thread', '--name', 'Kobe']), android.invoke)
  assert.equal(result.action, 'inspect-thread')
  assert.equal(result.name, 'Kobe')
  assert.ok(result.messages.length > 0)
  assert.equal(result.messages[0].sender, 'Kobe')
  assert.equal(result.has_phone, true)
  assert.equal(result.phone, '5125550199')
})

test('send-batch dispatches queued messages sequentially', () => {
  const android = scriptedAndroid({
    dumps: [
      CHATS_PAGE_1,
      CHAT_THREAD_MESSAGES,
      CHAT_THREAD_MESSAGES,
      CHAT_THREAD_MESSAGES,
      CHAT_THREAD_MESSAGES,
      CHATS_PAGE_1,
    ],
    focus: CHAT_FOCUS,
  })
  const input = JSON.stringify([{ name: 'Kobe', message: 'Sounds good!' }])
  const result = execute(parseOptions(['send-batch', '--confirm', 'send']), android.invoke, input)
  assert.equal(result.action, 'send-batch')
  assert.equal(result.sent_count, 1)
  assert.equal(result.results[0].name, 'Kobe')
  assert.equal(result.results[0].status, 'sent')
})
