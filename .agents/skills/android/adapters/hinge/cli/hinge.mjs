#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { createStandardAppAdapter } from '../../cli/standard-app.mjs'

export const HINGE_PACKAGE = 'co.hinge.app'

const cliDirectory = dirname(fileURLToPath(import.meta.url))
const hadesRoot = resolve(cliDirectory, '../../../../../..')
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')
export const RUNTIME_DIRECTORY = resolve(hadesRoot, '.agents/skills/android/runtime/hinge')

const adapter = createStandardAppAdapter({
  id: 'hinge',
  name: 'Hinge',
  packageName: HINGE_PACKAGE,
  runtimeDirectory: RUNTIME_DIRECTORY,
})

const STANDARD_COMMANDS = new Set(['check', 'inspect', 'open', 'screenshot'])
const PHONE_LOGIN_NAVIGATION = Object.freeze({
  text: 'Sign in with Phone Number',
  className: 'android.widget.TextView',
  bounds: '[265,1678][815,1732]',
})
const PHONE_SURFACE = Object.freeze({
  title: Object.freeze({
    text: "What's your phone number?",
    className: 'android.widget.TextView',
    bounds: '[94,209][986,414]',
  }),
  field: Object.freeze({
    className: 'android.widget.EditText',
    bounds: '[460,691][1025,856]',
  }),
  continueLabel: Object.freeze({
    text: 'Continue',
    className: 'android.widget.TextView',
    bounds: '[448,1761][633,1813]',
  }),
  continueButton: Object.freeze({
    text: '',
    desc: '',
    className: 'android.widget.Button',
    bounds: '[375,1722][705,1852]',
  }),
  disclosure: Object.freeze({
    text: 'Hinge will send you a text with a verification code. Message and data rates may apply.',
    className: 'android.widget.TextView',
    bounds: '[44,1907][1036,1973]',
  }),
})
const UNSAFE_AUTH_SURFACES = Object.freeze([
  ['provider_or_account', /\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue as\b|\bcontinue with (?:google|facebook|apple)\b|\buse another account\b|\baccount owner\b|\bgoogle account\b|accounts\.google\.com/],
  ['permission', /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/],
  ['passkey_or_identity', /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/],
  ['two_factor', /\btwo[- ]factor\b|\b2[- ]step\b|\b2fa\b/],
  ['captcha', /captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge/],
  ['purchase', /\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b/],
  ['profile', /\bcreate (?:your )?profile\b|\bedit (?:your )?profile\b|\bcomplete (?:your )?profile\b|\bprofile setup\b/],
  ['social', /\b(?:connect|link|add) (?:your )?(?:instagram|facebook|spotify|social)\b/],
])

function loginUsage() {
  return 'Usage: hinge.mjs <check|inspect|open|screenshot|begin-login|fill-phone|request-code> [--serial <device-id>] [--out <runtime-path>] [--method phone] [--confirm request]'
}

function parseLoginOptions(argv) {
  const command = argv[0]
  const allowed = command === 'begin-login'
    ? new Set(['serial', 'method'])
    : command === 'request-code'
      ? new Set(['serial', 'confirm'])
      : new Set(['serial'])
  const options = { command }
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index]
    if (!argument.startsWith('--')) throw new Error(`${command.replaceAll('-', '_')}_invalid_input`)
    const key = argument.slice(2)
    if (!allowed.has(key) || Object.hasOwn(options, key)) {
      throw new Error(`${command.replaceAll('-', '_')}_options: only ${[...allowed].map((name) => `--${name}`).join(' and ')} are allowed`)
    }
    const value = argv[index + 1]
    if (value === undefined || value.startsWith('--')) {
      throw new Error(`${command.replaceAll('-', '_')}_invalid_input`)
    }
    options[key] = value
    index += 1
  }
  if (command === 'begin-login') {
    if (options.method === undefined) throw new Error('phone_login_method_required')
    if (options.method !== 'phone') throw new Error('unsupported_login_method')
  }
  if (command === 'request-code' && options.confirm !== 'request') {
    throw new Error('request_confirmation_required')
  }
  return options
}

const ENGAGEMENT_COMMANDS = new Set([
  'tab', 'profile-ingest', 'candidates', 'chats', 'matches', 'open-chat', 'send-message',
])

function parseEngagementOptions(argv) {
  const command = argv[0]
  const allowed = new Set(['serial', 'name', 'confirm'])
  const options = { command }
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index]
    if (!argument.startsWith('--')) throw new Error(`${command.replaceAll('-', '_')}_invalid_input`)
    const key = argument.slice(2)
    if (!allowed.has(key)) throw new Error(`${command.replaceAll('-', '_')}_options: only ${[...allowed].map((name) => `--${name}`).join(' and ')} are allowed`)
    const value = argv[index + 1]
    if (value === undefined || value.startsWith('--')) {
      throw new Error(`${command.replaceAll('-', '_')}_invalid_input`)
    }
    options[key] = value
    index += 1
  }
  if (command === 'open-chat' && !options.name) throw new Error('name_required_for_open_chat')
  if (command === 'send-message' && options.confirm !== 'send') throw new Error('send_confirmation_required')
  return options
}

export function parseOptions(argv) {
  if (['begin-login', 'fill-phone', 'request-code'].includes(argv[0])) {
    return parseLoginOptions(argv)
  }
  if (ENGAGEMENT_COMMANDS.has(argv[0])) {
    return parseEngagementOptions(argv)
  }
  return adapter.parseOptions(argv)
}

function parsePhone(input) {
  let value
  try {
    value = JSON.parse(input)
  } catch {
    throw new Error('phone_input_invalid')
  }
  const keys = value && !Array.isArray(value) && typeof value === 'object'
    ? Object.keys(value)
    : []
  if (
    keys.length !== 1
    || keys[0] !== 'phone'
    || typeof value.phone !== 'string'
    || value.phone.length === 0
    || /[\r\n]/.test(value.phone)
  ) {
    throw new Error('phone_input_invalid')
  }
  return value.phone
}

function androidArgs(serial, extra = []) {
  return [...(serial ? ['--serial', serial] : []), ...extra]
}

function invokeLogin(invoke, command, args, input) {
  let result
  try {
    result = invoke(command, args, input, { redactErrors: true })
  } catch {
    throw new Error(`android_${command.replaceAll('-', '_')}_failed`)
  }
  if (!result || result.ok !== true) {
    throw new Error(`android_${command.replaceAll('-', '_')}_failed`)
  }
  return result
}

const CODE_ENTRY_SURFACE = /\benter (?:the )?(?:verification|authentication|security)?\s*code\b/
const FINAL_TAP_REJECT_PATTERNS = Object.freeze([
  ...UNSAFE_AUTH_SURFACES.map(([, pattern]) => pattern.source),
  CODE_ENTRY_SURFACE.source,
])

function unsafeAuthSurface(elements, { allowCodeEntry = false } = {}) {
  const visibleText = elements
    .map((element) => `${element?.text || ''}\n${element?.desc || ''}\n${element?.resourceId || ''}`)
    .join('\n')
    .toLowerCase()
  const unsafe = UNSAFE_AUTH_SURFACES.find(([, pattern]) => pattern.test(visibleText))?.[0]
  if (unsafe) return unsafe
  if (!allowCodeEntry && CODE_ENTRY_SURFACE.test(visibleText)) return 'two_factor'
  return null
}

function requireHingeFocus(current) {
  if (
    typeof current.focus !== 'string'
    || !/(?:^|[\s{])co\.hinge\.app(?:\/|[\s}])/.test(current.focus)
  ) {
    throw new Error('hinge_not_in_foreground')
  }
}

function serializedBounds(element) {
  const value = element?.bounds
  if (
    !value
    || ![value.x1, value.y1, value.x2, value.y2].every(Number.isInteger)
    || value.x2 <= value.x1
    || value.y2 <= value.y1
  ) {
    return null
  }
  return `[${value.x1},${value.y1}][${value.x2},${value.y2}]`
}

function exactControl(elements, control, error) {
  const candidates = elements.filter((element) => (
    element?.resourceId === ''
    && element.className === control.className
    && (control.text === undefined || element.text === control.text)
    && (control.desc === undefined || element.desc === control.desc)
  ))
  if (candidates.length !== 1) throw new Error(error)
  const matches = candidates.filter((element) => serializedBounds(element) === control.bounds)
  if (matches.length !== 1) throw new Error(error)
  return {
    index: elements.indexOf(matches[0]),
    text: control.text,
    desc: control.desc,
    id: '',
    className: control.className,
    bounds: control.bounds,
  }
}

function requireExactInitialNavigation(elements) {
  if (!Array.isArray(elements)) throw new Error('phone_login_navigation_not_exact_unique')
  return exactControl(
    elements,
    PHONE_LOGIN_NAVIGATION,
    'phone_login_navigation_not_exact_unique',
  )
}

function requireExactPhoneSurface(elements, { emptyPhone = false } = {}) {
  const error = 'phone_surface_not_exact_unique'
  if (!Array.isArray(elements)) throw new Error(error)
  exactControl(elements, PHONE_SURFACE.title, error)
  const field = exactControl(
    elements,
    emptyPhone ? { ...PHONE_SURFACE.field, text: '', desc: '' } : PHONE_SURFACE.field,
    error,
  )
  exactControl(elements, PHONE_SURFACE.continueLabel, error)
  const continueButton = exactControl(elements, PHONE_SURFACE.continueButton, error)
  exactControl(elements, PHONE_SURFACE.disclosure, error)
  return { field, continueButton }
}

function inspectLoginSurface(serial, invoke, validator) {
  const current = invokeLogin(invoke, 'current', androidArgs(serial))
  requireHingeFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeAuthSurface(dump.elements || [])
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
  return validator(dump.elements)
}

function inspectPostRequestSurface(serial, invoke) {
  const current = invokeLogin(invoke, 'current', androidArgs(serial))
  requireHingeFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeAuthSurface(dump.elements || [], { allowCodeEntry: true })
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
}

function loginPackagePreflight(options, invoke) {
  const packages = invokeLogin(
    invoke,
    'packages',
    androidArgs(options.serial, ['--package', HINGE_PACKAGE]),
  )
  if (!Array.isArray(packages.packages) || !packages.packages.includes(HINGE_PACKAGE)) {
    throw new Error('hinge_not_installed')
  }
  return packages.serial || options.serial
}

function freshLoginPreflight(options, invoke, validator) {
  const serial = loginPackagePreflight(options, invoke)
  return { serial, controls: inspectLoginSurface(serial, invoke, validator) }
}

function loginIdentity(serial) {
  return {
    id: adapter.id,
    name: adapter.name,
    serial,
    package: HINGE_PACKAGE,
  }
}

function guardedTapArgs(serial, control) {
  return androidArgs(serial, [
    '--index', String(control.index),
    ...(control.text === undefined ? [] : ['--text', control.text]),
    ...(control.desc === undefined ? [] : ['--desc', control.desc]),
    '--id', control.id,
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    ...FINAL_TAP_REJECT_PATTERNS.flatMap((pattern) => ['--reject-regex', pattern]),
  ])
}

function waitForExactAnchor(serial, invoke, control, { timeoutMs, pollMs } = {}) {
  return invokeLogin(invoke, 'wait', androidArgs(serial, [
    ...(control.text === undefined ? [] : ['--text', control.text]),
    ...(control.desc === undefined ? [] : ['--desc', control.desc]),
    '--id', '',
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    ...(timeoutMs === undefined ? [] : ['--timeout-ms', String(timeoutMs)]),
    ...(pollMs === undefined ? [] : ['--poll-ms', String(pollMs)]),
  ]))
}

function phoneSurfaceReady(serial, invoke) {
  inspectLoginSurface(serial, invoke, (elements) => requireExactPhoneSurface(elements, { emptyPhone: true }))
  return {
    ok: true,
    action: 'begin-login',
    ...loginIdentity(serial),
    method: 'phone',
    status: 'phone-surface-ready',
    codeRequested: false,
  }
}

function beginLogin(options, invoke) {
  if (options.method !== 'phone') throw new Error('unsupported_login_method')
  const serial = loginPackagePreflight(options, invoke)
  invokeLogin(invoke, 'launch', androidArgs(serial, ['--package', HINGE_PACKAGE]))
  try {
    waitForExactAnchor(serial, invoke, PHONE_SURFACE.title, { timeoutMs: 3_000, pollMs: 250 })
    return phoneSurfaceReady(serial, invoke)
  } catch (error) {
    if (error.message !== 'android_wait_failed') throw error
  }

  waitForExactAnchor(serial, invoke, PHONE_LOGIN_NAVIGATION, { timeoutMs: 15_000 })
  const controls = inspectLoginSurface(serial, invoke, requireExactInitialNavigation)
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, controls))
  waitForExactAnchor(serial, invoke, PHONE_SURFACE.title, { timeoutMs: 15_000 })
  return phoneSurfaceReady(serial, invoke)
}

function fillPhone(options, invoke, phoneInput) {
  const phone = parsePhone(phoneInput)
  const requireEmptyPhoneSurface = (elements) => requireExactPhoneSurface(elements, { emptyPhone: true })
  const preflight = freshLoginPreflight(options, invoke, requireEmptyPhoneSurface)
  const { serial } = preflight
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, preflight.controls.field))
  inspectLoginSurface(serial, invoke, requireEmptyPhoneSurface)
  invokeLogin(invoke, 'type-stdin', androidArgs(serial), phone)
  inspectLoginSurface(serial, invoke, requireExactPhoneSurface)
  return {
    ok: true,
    action: 'fill-phone',
    ...loginIdentity(serial),
    status: 'phone-filled',
    codeRequested: false,
  }
}

function requestCode(options, invoke) {
  if (options.confirm !== 'request') throw new Error('request_confirmation_required')
  const preflight = freshLoginPreflight(options, invoke, requireExactPhoneSurface)
  const { serial } = preflight
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, preflight.controls.continueButton))
  inspectPostRequestSurface(serial, invoke)
  return {
    ok: true,
    action: 'request-code',
    ...loginIdentity(serial),
    status: 'submission-observed',
    authentication: 'unverified',
  }
}

function executeEngagement(options, invoke, messageInput) {
  const preflight = adapter.execute({ command: 'check', serial: options.serial }, invoke)
  const { serial } = preflight
  const serialArgs = serial ? ['--serial', serial] : []

  if (options.command === 'tab') {
    const dump = invokeLogin(invoke, 'dump', serialArgs)
    const tabName = options.name || 'Discover'
    const tabElement = dump.elements.find((el) =>
      (el.text && el.text.toLowerCase() === tabName.toLowerCase()) ||
      (el.desc && el.desc.toLowerCase() === tabName.toLowerCase())
    )
    if (!tabElement) throw new Error(`tab_not_found: ${tabName}`)
    invokeLogin(invoke, 'tap', guardedTapArgs(serial, tabElement))
    return { ok: true, action: 'tab', ...loginIdentity(serial), tab: tabName }
  }

  if (options.command === 'profile-ingest' || options.command === 'candidates') {
    const dump = invokeLogin(invoke, 'dump', serialArgs)
    const ignoredNav = new Set(['discover', 'standouts', 'likes', 'matches', 'profile', 'home'])
    const textNodes = dump.elements.filter((el) => el.text && el.text.trim())
    const prompts = []
    let candidateName = 'Unknown'

    for (let i = 0; i < textNodes.length; i += 1) {
      const text = textNodes[i].text.trim()
      if (candidateName === 'Unknown' && !ignoredNav.has(text.toLowerCase()) && !text.includes(' ') && text.length < 30) {
        candidateName = text
      }
      if (text.endsWith('?') || /my simple pleasures|typical sunday|together we could|best travel story/i.test(text)) {
        prompts.push({
          prompt: text,
          answer: textNodes[i + 1] ? textNodes[i + 1].text.trim() : '',
        })
      }
    }

    return {
      ok: true,
      action: options.command,
      ...loginIdentity(serial),
      profile: {
        name: candidateName,
        prompts,
        photoCount: dump.elements.filter((el) => el.className && el.className.includes('ImageView')).length,
      },
    }
  }

  if (options.command === 'chats' || options.command === 'matches') {
    const dump = invokeLogin(invoke, 'dump', serialArgs)
    const matches = dump.elements
      .filter((el) => (el.resourceId && el.resourceId.includes('match')) || (el.clickable && el.text))
      .map((el) => ({ name: el.text || el.desc || 'Match', bounds: el.bounds }))

    return {
      ok: true,
      action: options.command,
      ...loginIdentity(serial),
      count: matches.length,
      matches,
    }
  }

  if (options.command === 'open-chat') {
    const dump = invokeLogin(invoke, 'dump', serialArgs)
    const matchNode = dump.elements.find((el) => el.text === options.name || el.desc === options.name)
    if (!matchNode) throw new Error(`match_not_found: ${options.name}`)

    invokeLogin(invoke, 'tap', guardedTapArgs(serial, matchNode))
    return {
      ok: true,
      action: 'open-chat',
      ...loginIdentity(serial),
      opened: options.name,
    }
  }

  if (options.command === 'send-message') {
    if (options.confirm !== 'send') throw new Error('send_confirmation_required')
    let message
    try {
      const parsed = JSON.parse(messageInput)
      message = parsed.message
    } catch {
      throw new Error('message_stdin_invalid_json')
    }
    if (!message || typeof message !== 'string') throw new Error('message_text_required')

    const dump = invokeLogin(invoke, 'dump', serialArgs)
    const editField = dump.elements.find((el) => el.className && el.className.includes('EditText'))
    if (!editField) throw new Error('chat_input_not_found')

    invokeLogin(invoke, 'tap', guardedTapArgs(serial, editField))
    invokeLogin(invoke, 'type-stdin', serialArgs, message, { redactErrors: true })

    return {
      ok: true,
      action: 'send-message',
      ...loginIdentity(serial),
      status: 'message_typed',
    }
  }

  throw new Error(`unhandled_command: ${options.command}`)
}

export function execute(options, invoke, phoneInput) {
  if (STANDARD_COMMANDS.has(options.command)) return adapter.execute(options, invoke)
  if (options.command === 'begin-login') return beginLogin(options, invoke)
  if (options.command === 'fill-phone') return fillPhone(options, invoke, phoneInput)
  if (options.command === 'request-code') return requestCode(options, invoke)
  if (ENGAGEMENT_COMMANDS.has(options.command)) return executeEngagement(options, invoke, phoneInput)
  throw new Error(`unknown_command: ${options.command}`)
}

function invokeAndroid(command, args, input, settings = {}) {
  const result = spawnSync(process.execPath, [androidCli, command, ...args], {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
    ...(input === undefined ? {} : { input }),
  })
  const redactErrors = settings.redactErrors === true || command === 'type-stdin'
  if (result.error) {
    if (redactErrors) throw new Error(`android_${command.replaceAll('-', '_')}_failed`)
    throw new Error(`android_cli_unavailable: ${result.error.message}`)
  }
  const output = String(result.stdout || '').trim()
  try {
    return JSON.parse(output)
  } catch {
    if (redactErrors) throw new Error(`android_${command.replaceAll('-', '_')}_failed`)
    throw new Error(`android_cli_invalid_output: ${String(result.stderr || output).trim()}`)
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const options = parseOptions(process.argv.slice(2))
    let phoneInput
    if (options.command === 'fill-phone') {
      try {
        phoneInput = readFileSync(0, 'utf8')
      } catch {
        throw new Error('phone_input_invalid')
      }
    }
    process.stdout.write(`${JSON.stringify(execute(options, invokeAndroid, phoneInput))}\n`)
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ ok: false, error: error.message, usage: loginUsage() })}\n`)
    process.exitCode = 1
  }
}
