import assert from 'node:assert/strict'
import test from 'node:test'
import {
  coordinateCapture,
  coordinateTap,
  coordinateSwipe,
  coordinateKey,
  coordinateInputText,
} from '../cli/coordinator.mjs'

test('coordinator capture collects focus, elements, and screenshot in single call', () => {
  const calls = []
  const fakeContext = {
    invokeAndroid: (args) => {
      calls.push(args)
      if (args[0] === 'current') return { ok: true, serial: 'device-1', focus: 'com.example/MainActivity' }
      if (args[0] === 'dump') return { ok: true, serial: 'device-1', elements: [{ text: 'Login', bounds: '[0,0][100,100]' }] }
      if (args[0] === 'screenshot') return { ok: true, serial: 'device-1', out: '/tmp/shot.png' }
      return { ok: true }
    },
  }

  const result = coordinateCapture({ serial: 'device-1', out: '/tmp/shot.png' }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'capture')
  assert.equal(result.focus, 'com.example/MainActivity')
  assert.equal(result.elements.length, 1)
  assert.equal(result.screenshot, '/tmp/shot.png')
  assert.equal(calls.length, 3)
})

test('coordinator swipe handles directional aliases', () => {
  const calls = []
  const fakeContext = {
    invokeAndroid: (args) => {
      calls.push(args)
      return { ok: true, action: 'swipe', from: [540, 1600], to: [540, 600] }
    },
  }

  const result = coordinateSwipe({ serial: 'device-1', direction: 'up', duration: 250 }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'swipe')
  assert.equal(result.direction, 'up')
  assert.deepEqual(calls[0], ['swipe', '--serial', 'device-1', '--from', '540,1600', '--to', '540,600', '--duration', '250'])
})

test('coordinator key translates symbolic keys', () => {
  const calls = []
  const fakeContext = {
    invokeAndroid: (args) => {
      calls.push(args)
      return { ok: true, action: 'key', code: 4 }
    },
  }

  const result = coordinateKey({ serial: 'device-1', key: 'back' }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'key')
  assert.deepEqual(calls[0], ['key', '--serial', 'device-1', '--key', 'back'])
})

test('coordinator input text with clear sends deletes before typing', () => {
  const calls = []
  const fakeContext = {
    invokeAndroid: (args) => {
      calls.push(args)
      return { ok: true, action: args[0] === 'key' ? 'key' : 'type' }
    },
  }

  const result = coordinateInputText({ serial: 'device-1', text: 'test-input', clear: true }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'type')
  assert.equal(calls.length, 21) // 20 deletes + 1 text input
  assert.deepEqual(calls[calls.length - 1], ['type', '--serial', 'device-1', '--text', 'test-input'])
})
