import assert from 'node:assert/strict'
import test from 'node:test'
import {
  HINGE_PACKAGE,
  execute,
  parseOptions,
} from '../cli/hinge.mjs'

function fakeAndroid(overrides = {}) {
  const calls = []
  const defaults = {
    packages: { ok: true, serial: 'pixel-3', packages: [HINGE_PACKAGE] },
    current: { ok: true, serial: 'pixel-3', focus: 'Hinge' },
    dump: {
      ok: true,
      serial: 'pixel-3',
      elements: [
        { text: 'Discover', className: 'android.widget.TextView', bounds: '[100,1800][300,1900]' },
        { text: 'Maya', className: 'android.widget.TextView', bounds: '[100,200][400,280]' },
        { text: 'My simple pleasures', className: 'android.widget.TextView', bounds: '[100,400][800,450]' },
        { text: 'Sunday morning matcha latte', className: 'android.widget.TextView', bounds: '[100,460][800,520]' },
        { className: 'android.widget.ImageView', bounds: '[0,0][1080,1080]' },
      ],
    },
    tap: { ok: true, serial: 'pixel-3', action: 'tap' },
    'type-stdin': { ok: true, serial: 'pixel-3', action: 'type-stdin' },
  }
  return {
    calls,
    invoke(command, args, input) {
      calls.push({ command, args, input })
      const response = overrides[command] || defaults[command]
      return Array.isArray(response) ? response.shift() : response
    },
  }
}

test('Hinge tab navigates to requested tab', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['tab', '--name', 'Discover']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'tab')
  assert.equal(result.tab, 'Discover')
})

test('Hinge profile-ingest extracts candidate prompts and photo count', () => {
  const android = fakeAndroid()
  const result = execute(parseOptions(['profile-ingest']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'profile-ingest')
  assert.equal(result.profile.name, 'Maya')
  assert.equal(result.profile.prompts.length, 1)
  assert.equal(result.profile.prompts[0].prompt, 'My simple pleasures')
  assert.equal(result.profile.prompts[0].answer, 'Sunday morning matcha latte')
  assert.equal(result.profile.photoCount, 1)
})

test('Hinge matches returns candidate conversations', () => {
  const android = fakeAndroid({
    dump: {
      ok: true,
      serial: 'pixel-3',
      elements: [
        { text: 'Sarah', clickable: true, bounds: '[100,300][900,400]' },
        { text: 'Elena', clickable: true, bounds: '[100,420][900,520]' },
      ],
    },
  })
  const result = execute(parseOptions(['matches']), android.invoke)
  assert.equal(result.ok, true)
  assert.equal(result.count, 2)
  assert.equal(result.matches[0].name, 'Sarah')
})

test('Hinge send-message verifies confirmation and sends text via stdin', () => {
  const android = fakeAndroid({
    dump: {
      ok: true,
      serial: 'pixel-3',
      elements: [
        { className: 'android.widget.EditText', bounds: '[50,1800][900,1900]' },
      ],
    },
  })

  assert.throws(
    () => execute(parseOptions(['send-message']), android.invoke, JSON.stringify({ message: 'Hey Maya!' })),
    /send_confirmation_required/,
  )

  const result = execute(
    parseOptions(['send-message', '--confirm', 'send']),
    android.invoke,
    JSON.stringify({ message: 'Hey Maya!' }),
  )
  assert.equal(result.ok, true)
  assert.equal(result.status, 'message_typed')
})
