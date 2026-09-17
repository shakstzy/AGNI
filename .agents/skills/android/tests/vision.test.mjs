import assert from 'node:assert/strict'
import test from 'node:test'
import {
  locateElement,
  describeScreen,
  ocrScreen,
} from '../cli/vision.mjs'

test('locateElement parses JSON bounding box from VLM response', async () => {
  const fakeContext = {
    vlmResponse: '{"found": true, "label": "Continue button", "bounds": [100, 200, 300, 400], "center": [200, 300], "confidence": 0.98}',
  }

  const result = await locateElement('Continue button', { image: '/tmp/test.png' }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'locate')
  assert.equal(result.found, true)
  assert.deepEqual(result.center, [200, 300])
  assert.equal(result.confidence, 0.98)
})

test('locateElement handles not found response gracefully', async () => {
  const fakeContext = {
    vlmResponse: '{"found": false, "reason": "not_visible"}',
  }

  const result = await locateElement('Sign Up button', { image: '/tmp/test.png' }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.found, false)
  assert.equal(result.reason, 'not_visible')
})

test('describeScreen returns textual description', async () => {
  const fakeContext = {
    vlmResponse: 'Bumble feed showing candidate profile with photos and bio.',
  }

  const result = await describeScreen({ image: '/tmp/test.png' }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'describe')
  assert.equal(result.description, 'Bumble feed showing candidate profile with photos and bio.')
})

test('ocrScreen parses structured lines from VLM output', async () => {
  const fakeContext = {
    vlmResponse: '```json\n{"lines": [{"text": "Continue with phone", "bounds": [50, 100, 500, 150]}]}\n```',
  }

  const result = await ocrScreen({ image: '/tmp/test.png' }, fakeContext)
  assert.equal(result.ok, true)
  assert.equal(result.action, 'ocr')
  assert.equal(result.lines.length, 1)
  assert.equal(result.lines[0].text, 'Continue with phone')
})
