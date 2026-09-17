#!/usr/bin/env node
/**
 * HADES Android Input & Capture Coordinator
 * Coordinates screen capture, UI dump, settled verification, and safe input
 * (tap, directional swipe, keyevent, input_text, clear).
 */

import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const ANDROID_CLI = resolve(__dirname, 'android.mjs')

export const SWIPE_DIRECTIONS = {
  up: { from: '540,1600', to: '540,600' },
  down: { from: '540,600', to: '540,1600' },
  left: { from: '900,1000', to: '150,1000' },
  right: { from: '150,1000', to: '900,1000' },
}

export function defaultInvokeAndroid(args, stdin = null) {
  const result = execFileSync(process.execPath, [ANDROID_CLI, ...args], {
    encoding: 'utf8',
    input: stdin !== null ? stdin : undefined,
    stdio: ['pipe', 'pipe', 'pipe'],
  })
  return JSON.parse(result)
}

export function coordinateCapture(options = {}, context = {}) {
  const invoke = context.invokeAndroid || defaultInvokeAndroid
  const serialArgs = options.serial ? ['--serial', options.serial] : []

  const current = invoke(['current', ...serialArgs])
  const dump = invoke(['dump', ...serialArgs])
  const screenshotArgs = ['screenshot', ...serialArgs]
  if (options.out) screenshotArgs.push('--out', options.out)
  const screenshot = invoke(screenshotArgs)

  return {
    ok: true,
    action: 'capture',
    serial: current.serial || options.serial,
    focus: current.focus,
    elements: dump.elements,
    screenshot: screenshot.out,
  }
}

export function coordinateTap(options = {}, context = {}) {
  const invoke = context.invokeAndroid || defaultInvokeAndroid
  const args = ['tap']
  if (options.serial) args.push('--serial', options.serial)
  if (options.x !== undefined && options.y !== undefined) {
    args.push('--point', `${options.x},${options.y}`)
  } else {
    if (options.text) args.push('--text', options.text)
    if (options.desc) args.push('--desc', options.desc)
    if (options.id || options.resourceId) args.push('--id', options.id || options.resourceId)
    if (options.class || options.className) args.push('--class', options.class || options.className)
    if (options.bounds) args.push('--bounds', options.bounds)
    if (options.index !== undefined) args.push('--index', String(options.index))
    if (options.unique) args.push('--unique', 'true')
    if (options.rejectRegex) {
      const patterns = Array.isArray(options.rejectRegex) ? options.rejectRegex : [options.rejectRegex]
      for (const p of patterns) args.push('--reject-regex', p)
    }
  }

  return invoke(args)
}

export function coordinateSwipe(options = {}, context = {}) {
  const invoke = context.invokeAndroid || defaultInvokeAndroid
  const args = ['swipe']
  if (options.serial) args.push('--serial', options.serial)

  let from = options.from
  let to = options.to

  if (options.direction) {
    const preset = SWIPE_DIRECTIONS[options.direction.toLowerCase()]
    if (!preset) throw new Error(`invalid_swipe_direction: ${options.direction}`)
    from = preset.from
    to = preset.to
  }

  if (!from || !to) throw new Error('swipe_requires_from_to_or_direction')

  args.push('--from', from, '--to', to)
  if (options.duration) args.push('--duration', String(options.duration))

  const res = invoke(args)
  return {
    ...res,
    direction: options.direction || 'custom',
  }
}

export function coordinateKey(options = {}, context = {}) {
  const invoke = context.invokeAndroid || defaultInvokeAndroid
  const args = ['key']
  if (options.serial) args.push('--serial', options.serial)
  const key = options.key || options.keycode
  if (!key) throw new Error('key_required')
  args.push('--key', key)
  return invoke(args)
}

export function coordinateInputText(options = {}, context = {}) {
  const invoke = context.invokeAndroid || defaultInvokeAndroid
  const serialArgs = options.serial ? ['--serial', options.serial] : []

  if (options.clear) {
    // send deletes
    for (let i = 0; i < 20; i += 1) {
      invoke(['key', ...serialArgs, '--key', 'delete'])
    }
  }

  if (options.stdin !== undefined) {
    return invoke(['type-stdin', ...serialArgs], options.stdin)
  }

  if (options.text !== undefined) {
    return invoke(['type', ...serialArgs, '--text', options.text])
  }

  throw new Error('text_or_stdin_required')
}

export function coordinateWait(options = {}, context = {}) {
  const invoke = context.invokeAndroid || defaultInvokeAndroid
  const args = ['wait']
  if (options.serial) args.push('--serial', options.serial)
  if (options.text) args.push('--text', options.text)
  if (options.desc) args.push('--desc', options.desc)
  if (options.id || options.resourceId) args.push('--id', options.id || options.resourceId)
  if (options.class || options.className) args.push('--class', options.class || options.className)
  if (options.bounds) args.push('--bounds', options.bounds)
  if (options.index !== undefined) args.push('--index', String(options.index))
  if (options.timeoutMs) args.push('--timeout', String(options.timeoutMs))
  return invoke(args)
}

function parseCliArgs(argv) {
  const command = argv[2]
  const options = {}
  for (let i = 3; i < argv.length; i += 1) {
    const arg = argv[i]
    if (arg.startsWith('--')) {
      const key = arg.slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase())
      const next = argv[i + 1]
      if (next && !next.startsWith('--')) {
        options[key] = next
        i += 1
      } else {
        options[key] = true
      }
    } else if (!options.positional) {
      options.positional = arg
    }
  }
  return { command, options }
}

async function main() {
  const { command, options } = parseCliArgs(process.argv)
  if (!command) {
    console.error('Usage: coordinator.mjs <capture|tap|swipe|key|input-text|wait> [options]')
    process.exit(1)
  }

  try {
    let result
    switch (command) {
      case 'capture':
        result = coordinateCapture(options)
        break
      case 'tap':
        result = coordinateTap(options)
        break
      case 'swipe':
        result = coordinateSwipe({ ...options, direction: options.positional || options.direction })
        break
      case 'key':
        result = coordinateKey({ ...options, key: options.positional || options.key })
        break
      case 'input-text':
        result = coordinateInputText(options)
        break
      case 'wait':
        result = coordinateWait(options)
        break
      default:
        throw new Error(`unknown_command: ${command}`)
    }
    console.log(JSON.stringify(result, null, 2))
  } catch (error) {
    console.error(JSON.stringify({ ok: false, error: error.message }))
    process.exit(1)
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(__filename)) {
  main()
}
