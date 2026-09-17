#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const KEYCODES = {
  back: 4,
  home: 3,
  enter: 66,
  tab: 61,
  delete: 67,
  escape: 111,
}

function usage() {
  return 'Usage: android.mjs <doctor|devices|waydroid-status|start-waydroid|stop-waydroid|current|packages|launch|install-apk|dump|screenshot|tap|type|type-stdin|key|swipe|wait|open-url> [options]'
}

function parseArgs(argv) {
  const options = { command: argv[0] || 'doctor' }
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index]
    if (!argument.startsWith('--')) throw new Error(`invalid_argument: ${argument}`)
    const key = argument.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())
    const value = argv[index + 1]
    if (value === undefined || value.startsWith('--')) throw new Error(`value_required: ${argument}`)
    if (key === 'rejectRegex') {
      options.rejectRegex = [...(options.rejectRegex || []), value]
    } else {
      options[key] = value
    }
    index += 1
  }
  return options
}

function run(binary, args, { binaryOutput = false, allowFailure = false } = {}) {
  const result = spawnSync(binary, args, {
    encoding: binaryOutput ? null : 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  })
  if (result.error) throw new Error(`${binary}_unavailable: ${result.error.message}`)
  if (!allowFailure && result.status !== 0) {
    const detail = String(result.stderr || result.stdout || '').trim()
    throw new Error(`${binary}_failed: ${args.join(' ')}${detail ? `: ${detail}` : ''}`)
  }
  return result
}

function adb(options, args, settings) {
  return run('adb', options.serial ? ['-s', options.serial, ...args] : args, settings)
}

function parseDevices(output) {
  return String(output || '')
    .split(/\r?\n/)
    .slice(1)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [serial, state, ...metadata] = line.split(/\s+/)
      return { serial, state, metadata }
    })
}

function devices() {
  return parseDevices(run('adb', ['devices', '-l']).stdout)
}

function selectDevice(options) {
  const available = devices().filter((device) => device.state === 'device')
  if (options.serial) {
    if (!available.some((device) => device.serial === options.serial)) {
      throw new Error(`device_not_found: ${options.serial}`)
    }
    return options.serial
  }
  if (available.length === 0) throw new Error('no_android_device: start Waydroid or connect a device through ADB')
  if (available.length > 1) throw new Error(`multiple_devices: pass --serial (${available.map((device) => device.serial).join(', ')})`)
  return available[0].serial
}

function attribute(tag, name) {
  const match = tag.match(new RegExp(`${name}="([^"]*)"`))
  return match ? match[1]
    .replaceAll('&quot;', '"')
    .replaceAll('&apos;', "'")
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&amp;', '&') : ''
}

function bounds(value) {
  const match = value.match(/\[(\d+),(\d+)\]\[(\d+),(\d+)\]/)
  if (!match) return null
  const [x1, y1, x2, y2] = match.slice(1).map(Number)
  return { x1, y1, x2, y2, x: Math.round((x1 + x2) / 2), y: Math.round((y1 + y2) / 2) }
}

function parseUi(xml) {
  return [...String(xml).matchAll(/<node\b[^>]*>/g)].map((match, index) => {
    const tag = match[0]
    return {
      index,
      text: attribute(tag, 'text'),
      desc: attribute(tag, 'content-desc'),
      resourceId: attribute(tag, 'resource-id'),
      className: attribute(tag, 'class'),
      clickable: attribute(tag, 'clickable') === 'true',
      enabled: attribute(tag, 'enabled') !== 'false',
      bounds: bounds(attribute(tag, 'bounds')),
    }
  })
}

function dumpUi(options) {
  adb(options, ['shell', 'uiautomator', 'dump', '/sdcard/window.xml'])
  return String(adb(options, ['exec-out', 'cat', '/sdcard/window.xml']).stdout)
}

function parseExpectedBounds(value) {
  const match = String(value).match(/^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$/)
  if (!match) throw new Error('invalid_tap_bounds')
  const [x1, y1, x2, y2] = match.slice(1).map(Number)
  if (x2 <= x1 || y2 <= y1) throw new Error('invalid_tap_bounds')
  return { x1, y1, x2, y2 }
}

function validateTapOptions(options) {
  if (options.bounds !== undefined) options.expectedBounds = parseExpectedBounds(options.bounds)
  if (options.unique !== undefined && options.unique !== 'true') {
    throw new Error('invalid_tap_unique: expected true')
  }
  options.rejectPatterns = (options.rejectRegex || []).map((pattern) => {
    try {
      return new RegExp(pattern, 'i')
    } catch {
      throw new Error('invalid_tap_reject_regex')
    }
  })
}

function visibleElement(element) {
  return element.bounds
    && element.bounds.x2 > element.bounds.x1
    && element.bounds.y2 > element.bounds.y1
}

function rejectedByTapGuard(elements, patterns) {
  return patterns.length > 0 && elements.some((element) => (
    visibleElement(element)
    && [element.text, element.desc].some((value) => patterns.some((pattern) => pattern.test(value)))
  ))
}

function sameBounds(actual, expected) {
  return actual
    && actual.x2 > actual.x1
    && actual.y2 > actual.y1
    && actual.x1 === expected.x1
    && actual.y1 === expected.y1
    && actual.x2 === expected.x2
    && actual.y2 === expected.y2
}

function matchesSelector(element, options, { includeIndex = true, includeBounds = true } = {}) {
  if (includeBounds && (!element.bounds || !element.enabled)) return false
  if (includeIndex && options.index !== undefined && element.index !== Number(options.index)) return false
  if (options.text !== undefined && element.text !== options.text) return false
  if (options.contains !== undefined) {
    const haystack = `${element.text}\n${element.desc}\n${element.resourceId}\n${element.className}`.toLowerCase()
    if (!haystack.includes(options.contains.toLowerCase())) return false
  }
  if (options.desc !== undefined && element.desc !== options.desc) return false
  if (options.id !== undefined && element.resourceId !== options.id) return false
  if (options.class !== undefined && element.className !== options.class) return false
  if (includeBounds && options.expectedBounds !== undefined && !sameBounds(element.bounds, options.expectedBounds)) return false
  return true
}

function selectElement(elements, options) {
  const selectorKeys = ['text', 'contains', 'desc', 'id', 'class', 'expectedBounds']
  const hasSelector = selectorKeys.some((key) => options[key] !== undefined)
  if (options.index !== undefined && !hasSelector && options.unique === undefined) {
    const match = elements.find((element) => element.index === Number(options.index))
    if (!match) throw new Error(`element_not_found: index ${options.index}`)
    return match
  }
  const matches = elements.filter((element) => matchesSelector(element, options))
  if (!hasSelector && options.index === undefined) throw new Error('element_not_found')
  if (matches.length === 0) throw new Error('element_not_found')
  if (options.unique === 'true') {
    const peers = elements.filter((element) => matchesSelector(element, options, {
      includeIndex: false,
      includeBounds: false,
    }))
    if (peers.length !== 1) throw new Error('element_not_unique')
  }
  return matches.sort((left, right) => Number(right.clickable) - Number(left.clickable) || left.bounds.y1 - right.bounds.y1)[0]
}

function publicElement(element) {
  return {
    text: element.text,
    desc: element.desc,
    resourceId: element.resourceId,
    className: element.className,
    bounds: element.bounds,
  }
}

function emit(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`)
}

function sanitizeInputText(value) {
  return String(value)
    .replace(/[\u2018\u2019\u201A\u201B]/g, "'")
    .replace(/[\u201C\u201D\u201E\u201F]/g, '"')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/\u2026/g, '...')
    .replace(/\u00A0/g, ' ')
    .normalize('NFKD')
    .replace(/[^\x00-\x7F]/g, '')
}

function inputText(value) {
  return sanitizeInputText(value)
    .replaceAll('\\', '\\\\')
    .replaceAll(' ', '%s')
    .replace(/[&<>();'"|]/g, (character) => `\\${character}`)
}

function readSensitiveStdin() {
  const input = readFileSync(0, 'utf8')
  const value = input.endsWith('\r\n') ? input.slice(0, -2) : input.endsWith('\n') ? input.slice(0, -1) : input
  if (value.length === 0) throw new Error('stdin_value_required')
  if (/[\r\n]/.test(value)) throw new Error('stdin_single_value_required')
  return value
}

function typeSensitiveInput(options, value) {
  const args = ['-s', options.serial, 'shell', 'input', 'text', inputText(value)]
  let result
  try {
    result = spawnSync('adb', args, {
      encoding: 'utf8',
      maxBuffer: 16 * 1024 * 1024,
    })
  } catch {
    throw new Error('adb_sensitive_input_failed')
  }
  if (result.error || result.status !== 0) throw new Error('adb_sensitive_input_failed')
}

function waydroidStatus() {
  const result = run('waydroid', ['status'], { allowFailure: true })
  const text = String(result.stdout || result.stderr || '')
  const ip = text.match(/^IP address:\s*(.+)$/m)?.[1]?.trim() || null
  return {
    available: result.status === 0,
    session: text.match(/^Session:\s*(.+)$/m)?.[1]?.trim() || null,
    container: text.match(/^Container:\s*(.+)$/m)?.[1]?.trim() || null,
    ip,
  }
}

async function waitForElement(options) {
  const timeoutMs = Number(options.timeoutMs || 15_000)
  const pollMs = Number(options.pollMs || 500)
  if (!Number.isFinite(timeoutMs) || timeoutMs < 0 || !Number.isFinite(pollMs) || pollMs <= 0) {
    throw new Error('invalid_wait_duration')
  }
  const started = Date.now()
  let lastError = null
  while (Date.now() - started <= timeoutMs) {
    try {
      const element = selectElement(parseUi(dumpUi(options)), options)
      return { element, waitedMs: Date.now() - started }
    } catch (error) {
      lastError = error
      await new Promise((resolvePromise) => setTimeout(resolvePromise, pollMs))
    }
  }
  throw new Error(`wait_timeout: ${lastError?.message || 'element_not_found'}`)
}

async function main() {
  const argv = process.argv.slice(2)
  let options
  try {
    options = parseArgs(argv)
  } catch (error) {
    if (argv[0] === 'type-stdin') throw new Error('type_stdin_invalid_input')
    throw error
  }
  let sensitiveInput = null
  if (options.command === 'type-stdin') {
    if (Object.keys(options).some((key) => !['command', 'serial'].includes(key))) {
      throw new Error('type_stdin_options: only --serial is allowed')
    }
    sensitiveInput = readSensitiveStdin()
  }
  if (options.rejectRegex !== undefined && options.command !== 'tap') {
    throw new Error('reject_regex_only_supported_for_tap')
  }
  if (options.command === 'tap' || options.command === 'wait') validateTapOptions(options)
  if (options.command === 'doctor') {
    const version = run('adb', ['version'], { allowFailure: true })
    emit({
      ok: version.status === 0,
      adb: version.status === 0 ? String(version.stdout).split(/\r?\n/).filter(Boolean) : [],
      devices: version.status === 0 ? devices() : [],
      waydroid: waydroidStatus(),
    })
    return
  }
  if (options.command === 'devices') {
    emit({ ok: true, devices: devices() })
    return
  }
  if (options.command === 'waydroid-status') {
    emit({ ok: true, waydroid: waydroidStatus() })
    return
  }
  if (options.command === 'start-waydroid') {
    run('sudo', ['systemctl', 'start', 'waydroid-container.service'])
    run('waydroid', ['session', 'start'])
    emit({ ok: true, waydroid: waydroidStatus() })
    return
  }
  if (options.command === 'stop-waydroid') {
    run('waydroid', ['session', 'stop'], { allowFailure: true })
    run('sudo', ['systemctl', 'stop', 'waydroid-container.service'])
    emit({ ok: true, waydroid: waydroidStatus() })
    return
  }

  options.serial = selectDevice(options)
  if (options.command === 'current') {
    const output = String(adb(options, ['shell', 'dumpsys', 'window']).stdout)
    const focus = output.split(/\r?\n/).find((line) => /mCurrentFocus|mFocusedApp/.test(line))?.trim() || null
    emit({ ok: true, serial: options.serial, focus })
    return
  }
  if (options.command === 'packages') {
    const all = String(adb(options, ['shell', 'pm', 'list', 'packages']).stdout)
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => line.replace(/^package:/, ''))
    const packages = options.package !== undefined
      ? all.filter((name) => name === options.package)
      : options.contains
        ? all.filter((name) => name.toLowerCase().includes(options.contains.toLowerCase()))
        : all
    emit({ ok: true, serial: options.serial, packages })
    return
  }
  if (options.command === 'launch') {
    if (!options.package) throw new Error('package_required')
    const target = options.activity ? ['shell', 'am', 'start', '-n', `${options.package}/${options.activity}`] : ['shell', 'monkey', '-p', options.package, '-c', 'android.intent.category.LAUNCHER', '1']
    adb(options, target)
    emit({ ok: true, serial: options.serial, action: 'launch', package: options.package })
    return
  }
  if (options.command === 'install-apk') {
    if (!options.apk) throw new Error('apk_required')
    adb(options, ['install', '-r', resolve(options.apk)])
    emit({ ok: true, serial: options.serial, action: 'install-apk', apk: resolve(options.apk) })
    return
  }
  if (options.command === 'dump') {
    const xml = dumpUi(options)
    emit({ ok: true, serial: options.serial, elements: parseUi(xml).map(publicElement) })
    return
  }
  if (options.command === 'screenshot') {
    const output = resolve(options.out || `android-${Date.now()}.png`)
    mkdirSync(dirname(output), { recursive: true, mode: 0o700 })
    writeFileSync(output, adb(options, ['exec-out', 'screencap', '-p'], { binaryOutput: true }).stdout, { mode: 0o600 })
    emit({ ok: true, serial: options.serial, out: output })
    return
  }
  if (options.command === 'tap') {
    let x = Number(options.x)
    let y = Number(options.y)
    let element = null
    let elements = null
    if (!Number.isFinite(x) || !Number.isFinite(y) || options.rejectPatterns.length > 0) {
      elements = parseUi(dumpUi(options))
    }
    if (rejectedByTapGuard(elements || [], options.rejectPatterns)) {
      throw new Error('tap_rejected_by_guard')
    }
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      element = selectElement(elements, options)
      x = element.bounds.x
      y = element.bounds.y
    }
    adb(options, ['shell', 'input', 'tap', String(x), String(y)])
    emit({ ok: true, serial: options.serial, action: 'tap', x, y, ...(element ? { element: publicElement(element) } : {}) })
    return
  }
  if (options.command === 'type') {
    if (options.text === undefined) throw new Error('text_required')
    adb(options, ['shell', 'input', 'text', inputText(options.text)])
    emit({ ok: true, serial: options.serial, action: 'type', typedLength: options.text.length })
    return
  }
  if (options.command === 'type-stdin') {
    typeSensitiveInput(options, sensitiveInput)
    emit({ ok: true, serial: options.serial, action: 'type-stdin' })
    return
  }
  if (options.command === 'key') {
    const key = String(options.name || '').toLowerCase().replaceAll('-', '_')
    const code = KEYCODES[key] || Number(options.code)
    if (!Number.isFinite(code) || code <= 0) throw new Error('key_required')
    adb(options, ['shell', 'input', 'keyevent', String(code)])
    emit({ ok: true, serial: options.serial, action: 'key', code })
    return
  }
  if (options.command === 'swipe') {
    const from = String(options.from || '').split(',').map(Number)
    const to = String(options.to || '').split(',').map(Number)
    if (![...from, ...to].every(Number.isFinite) || from.length !== 2 || to.length !== 2) throw new Error('swipe_requires_from_to')
    const duration = Number(options.duration || 300)
    if (!Number.isFinite(duration) || duration <= 0) throw new Error('invalid_swipe_duration')
    adb(options, ['shell', 'input', 'swipe', String(from[0]), String(from[1]), String(to[0]), String(to[1]), String(duration)])
    emit({ ok: true, serial: options.serial, action: 'swipe', from, to, duration })
    return
  }
  if (options.command === 'wait') {
    const { element, waitedMs } = await waitForElement(options)
    emit({ ok: true, serial: options.serial, action: 'wait', waitedMs, element: publicElement(element) })
    return
  }
  if (options.command === 'open-url') {
    if (!options.url) throw new Error('url_required')
    adb(options, ['shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', options.url])
    emit({ ok: true, serial: options.serial, action: 'open-url', url: options.url })
    return
  }
  throw new Error(`unknown_command: ${options.command}; ${usage()}`)
}

main().catch((error) => {
  emit({ ok: false, error: error.message, usage: usage() })
  process.exitCode = 1
})
