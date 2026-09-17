#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { createStandardAppAdapter } from '../../cli/standard-app.mjs'

export const MIRCHI_PACKAGE = 'com.dating.mirchi'

const cliDirectory = dirname(fileURLToPath(import.meta.url))
const hadesRoot = resolve(cliDirectory, '../../../../../..')
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')
export const RUNTIME_DIRECTORY = resolve(hadesRoot, '.agents/skills/android/runtime/mirchi')

const adapter = createStandardAppAdapter({
  id: 'mirchi',
  name: 'Mirchi',
  packageName: MIRCHI_PACKAGE,
  runtimeDirectory: RUNTIME_DIRECTORY,
})

const STANDARD_COMMANDS = new Set(['check', 'inspect', 'open', 'screenshot'])
const PHONE_LOGIN_NAVIGATION = Object.freeze({
  text: 'SIGN IN WITH NUMBER',
  desc: '',
  resourceId: '',
  className: 'android.widget.TextView',
  bounds: '[287,1516][794,1556]',
})
const PHONE_SURFACE = Object.freeze({
  field: Object.freeze({
    desc: '',
    resourceId: 'com.dating.mirchi:id/etNumber',
    className: 'android.widget.EditText',
    bounds: '[492,537][1014,644]',
  }),
  country: Object.freeze({
    text: ' US  +1',
    desc: 'United States phone code is +1',
    resourceId: 'com.dating.mirchi:id/textView_selectedCountry',
    className: 'android.widget.TextView',
    bounds: '[214,557][368,624]',
  }),
  continueButton: Object.freeze({
    text: '',
    desc: '',
    resourceId: 'com.dating.mirchi:id/btnContinue',
    className: 'android.widget.ImageView',
    bounds: '[659,848][1014,986]',
  }),
})
const UNSAFE_AUTH_SURFACES = Object.freeze([
  ['provider_or_account', /\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue (?:as|with)\b|\buse another account\b|\baccount owner\b|accounts\.google\.com/],
  ['permission', /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/],
  ['passkey_or_identity', /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/],
  ['two_factor', /\btwo[- ]factor\b|\b2[- ]step\b|\benter (?:the )?(?:verification|authentication|security)?\s*code\b/],
  ['captcha', /captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge/],
  ['purchase', /\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b/],
  ['profile', /\bcreate (?:your )?profile\b|\bedit (?:your )?profile\b|\bcomplete (?:your )?profile\b|\bprofile setup\b/],
  ['social', /\b(?:connect|link|add) (?:your )?(?:instagram|facebook|spotify|social)\b/],
])

function loginUsage() {
  return 'Usage: mirchi.mjs <check|inspect|open|screenshot|begin-login|fill-phone|request-code> [--serial <device-id>] [--out <runtime-path>] [--method phone] [--confirm request]'
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
      throw new Error(`${command.replaceAll('-', '_')}_options`)
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

export function parseOptions(argv) {
  if (['begin-login', 'fill-phone', 'request-code'].includes(argv[0])) {
    return parseLoginOptions(argv)
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

function visibleAuthText(elements) {
  return elements
    .map((element) => `${element?.text || ''}\n${element?.desc || ''}\n${element?.resourceId || ''}`)
    .join('\n')
    .toLowerCase()
}

function unsafeAuthCategories(elements) {
  const visibleText = visibleAuthText(elements)
  return UNSAFE_AUTH_SURFACES
    .filter(([, pattern]) => pattern.test(visibleText))
    .map(([category]) => category)
}

function unsafeAuthSurface(elements) {
  return unsafeAuthCategories(elements)[0] || null
}

function neutralCodeEntrySurface(elements) {
  return elements.some((element) => [element?.text, element?.desc].some((value) => (
    typeof value === 'string'
    && /^(?:enter (?:the )?)?(?:verification )?code$/i.test(value.trim())
  )))
}

function explicitTwoFactorWarning(elements) {
  return elements.some((element) => [element?.text, element?.desc].some((value) => (
    typeof value === 'string'
    && /\b(?:two[- ]factor|2[- ]step|2fa)\b/i.test(value)
  )))
}

function requireMirchiFocus(current) {
  if (
    typeof current.focus !== 'string'
    || !/(?:^|[\s{])com\.dating\.mirchi(?:\/|[\s}])/.test(current.focus)
  ) {
    throw new Error('mirchi_not_in_foreground')
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
    element?.resourceId === control.resourceId
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
    resourceId: control.resourceId,
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
  const field = exactControl(
    elements,
    emptyPhone ? { ...PHONE_SURFACE.field, text: '1234567890' } : PHONE_SURFACE.field,
    error,
  )
  exactControl(elements, PHONE_SURFACE.country, error)
  const continueButton = exactControl(elements, PHONE_SURFACE.continueButton, error)
  return { field, continueButton }
}

function inspectLoginSurface(serial, invoke, validator) {
  const current = invokeLogin(invoke, 'current', androidArgs(serial))
  requireMirchiFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeAuthSurface(dump.elements || [])
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
  return validator(dump.elements)
}

function inspectPostRequestSurface(serial, invoke) {
  const current = invokeLogin(invoke, 'current', androidArgs(serial))
  requireMirchiFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  if (!Array.isArray(dump.elements)) throw new Error('post_request_surface_invalid')
  const elements = dump.elements
  const unsafe = unsafeAuthCategories(elements)
  const neutralCodeEntry = unsafe.length === 1
    && unsafe[0] === 'two_factor'
    && neutralCodeEntrySurface(elements)
    && !explicitTwoFactorWarning(elements)
  if (unsafe.length > 0 && !neutralCodeEntry) {
    throw new Error(`unsafe_auth_surface: ${unsafe[0]}`)
  }
}

function freshLoginPreflight(options, invoke, validator) {
  const serial = loginDevice(options, invoke)
  return { serial, controls: inspectLoginSurface(serial, invoke, validator) }
}

function loginDevice(options, invoke) {
  const packages = invokeLogin(
    invoke,
    'packages',
    androidArgs(options.serial, ['--package', MIRCHI_PACKAGE]),
  )
  if (!Array.isArray(packages.packages) || !packages.packages.includes(MIRCHI_PACKAGE)) {
    throw new Error('mirchi_not_installed')
  }
  return packages.serial || options.serial
}

function loginIdentity(serial) {
  return {
    id: adapter.id,
    name: adapter.name,
    serial,
    package: MIRCHI_PACKAGE,
  }
}

function guardedTapArgs(serial, control) {
  return androidArgs(serial, [
    '--index', String(control.index),
    ...(control.text === undefined ? [] : ['--text', control.text]),
    ...(control.desc === undefined ? [] : ['--desc', control.desc]),
    '--id', control.resourceId,
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    ...UNSAFE_AUTH_SURFACES.flatMap(([, pattern]) => ['--reject-regex', pattern.source]),
  ])
}

function waitArgs(serial, control) {
  return androidArgs(serial, [
    ...(control.text === undefined ? [] : ['--text', control.text]),
    ...(control.desc === undefined ? [] : ['--desc', control.desc]),
    '--id', control.resourceId,
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    '--timeout-ms', '3000',
    '--poll-ms', '250',
  ])
}

function waitForExactControl(serial, invoke, control) {
  try {
    const result = invoke('wait', waitArgs(serial, control))
    return result?.ok === true
  } catch {
    return false
  }
}

function phoneLoginResult(serial) {
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
  const serial = loginDevice(options, invoke)
  invokeLogin(invoke, 'launch', androidArgs(serial, ['--package', MIRCHI_PACKAGE]))

  if (waitForExactControl(serial, invoke, { ...PHONE_SURFACE.field, text: '1234567890' })) {
    inspectLoginSurface(serial, invoke, (elements) => requireExactPhoneSurface(elements, { emptyPhone: true }))
    return phoneLoginResult(serial)
  }

  if (!waitForExactControl(serial, invoke, PHONE_LOGIN_NAVIGATION)) {
    inspectLoginSurface(serial, invoke, requireExactInitialNavigation)
  }
  const controls = inspectLoginSurface(serial, invoke, requireExactInitialNavigation)
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, controls))
  if (!waitForExactControl(serial, invoke, { ...PHONE_SURFACE.field, text: '1234567890' })) {
    inspectLoginSurface(serial, invoke, (elements) => requireExactPhoneSurface(elements, { emptyPhone: true }))
  }
  inspectLoginSurface(serial, invoke, (elements) => requireExactPhoneSurface(elements, { emptyPhone: true }))
  return phoneLoginResult(serial)
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

export function execute(options, invoke, phoneInput) {
  if (STANDARD_COMMANDS.has(options.command)) return adapter.execute(options, invoke)
  if (options.command === 'begin-login') return beginLogin(options, invoke)
  if (options.command === 'fill-phone') return fillPhone(options, invoke, phoneInput)
  if (options.command === 'request-code') return requestCode(options, invoke)
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
