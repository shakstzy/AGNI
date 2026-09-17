#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createStandardAppAdapter } from '../../cli/standard-app.mjs'

export const PLENTY_OF_FISH_PACKAGE = 'com.pof.android'

const cliDirectory = dirname(fileURLToPath(import.meta.url))
const hadesRoot = resolve(cliDirectory, '../../../../../..')
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')
export const RUNTIME_DIRECTORY = resolve(hadesRoot, '.agents/skills/android/runtime/plenty-of-fish')

const adapter = createStandardAppAdapter({
  id: 'plenty-of-fish',
  name: 'Plenty of Fish',
  packageName: PLENTY_OF_FISH_PACKAGE,
  runtimeDirectory: RUNTIME_DIRECTORY,
})

const STANDARD_COMMANDS = new Set(['check', 'inspect', 'open', 'screenshot'])
const LOGIN_CONTROLS = Object.freeze({
  username: Object.freeze({
    id: 'com.pof.android:id/username',
    className: 'android.widget.EditText',
    label: 'Username or email',
    bounds: '[120,581][960,727]',
  }),
  password: Object.freeze({
    id: 'com.pof.android:id/password',
    className: 'android.widget.EditText',
    label: 'Password',
  }),
  submit: Object.freeze({
    id: 'com.pof.android:id/login',
    className: 'android.widget.Button',
    label: 'Log in',
  }),
})

const UNSAFE_AUTH_SURFACES = Object.freeze([
  ['account_selection', /\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue as\b|\baccount owner\b|\bwho(?:'s| is) using\b/],
  ['provider_or_account', /\bcontinue with (?:google|facebook|apple)\b/],
  ['permission', /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/],
  ['passkey_or_identity', /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/],
  ['two_factor', /\btwo[- ]factor\b|\b2[- ]step\b|\bverification code\b|\bauthentication code\b|\bsecurity code\b|\benter (?:the )?code\b/],
  ['captcha', /captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge/],
  ['purchase', /\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b/],
  ['profile', /\bcreate (?:your )?profile\b|\bedit (?:your )?profile\b|\bcomplete (?:your )?profile\b|\bprofile setup\b/],
  ['social', /\b(?:connect|link|add) (?:your )?(?:instagram|facebook|spotify|social)\b/],
])

function authUsage() {
  return 'Usage: plenty-of-fish.mjs <check|inspect|open|screenshot|fill-login|submit-login> [--serial <device-id>] [--out <runtime-path>] [--confirm submit]'
}

function parseAuthOptions(argv) {
  const command = argv[0]
  const allowed = command === 'fill-login' ? new Set(['serial']) : new Set(['serial', 'confirm'])
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
  if (command === 'submit-login' && options.confirm !== 'submit') {
    throw new Error('submit_confirmation_required')
  }
  return options
}

export function parseOptions(argv) {
  if (argv[0] === 'fill-login' || argv[0] === 'submit-login') return parseAuthOptions(argv)
  return adapter.parseOptions(argv)
}

function parseCredentials(input) {
  let value
  try {
    value = JSON.parse(input)
  } catch {
    throw new Error('credential_input_invalid')
  }
  const keys = value && !Array.isArray(value) && typeof value === 'object'
    ? Object.keys(value).sort()
    : []
  if (
    keys.length !== 2
    || keys[0] !== 'password'
    || keys[1] !== 'username'
    || typeof value.username !== 'string'
    || typeof value.password !== 'string'
    || value.username.length === 0
    || value.password.length === 0
    || /[\r\n]/.test(value.username)
    || /[\r\n]/.test(value.password)
  ) {
    throw new Error('credential_input_invalid')
  }
  return value
}

function androidArgs(serial, extra = []) {
  return [...(serial ? ['--serial', serial] : []), ...extra]
}

function invokeAuth(invoke, command, args, input) {
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

function unsafeAuthSurface(elements) {
  const visibleText = elements
    .map((element) => `${element?.text || ''}\n${element?.desc || ''}\n${element?.resourceId || ''}`)
    .join('\n')
    .toLowerCase()
  return UNSAFE_AUTH_SURFACES.find(([, pattern]) => pattern.test(visibleText))?.[0] || null
}

function requirePofFocus(current) {
  if (
    typeof current.focus !== 'string'
    || !/(?:^|[\s{])com\.pof\.android(?:\/|[\s}])/.test(current.focus)
  ) {
    throw new Error('pof_not_in_foreground')
  }
}

function labelMatches(element, control, populatedValue, allowAnyPopulated) {
  if (element.text === control.label || element.desc === control.label) return true
  if (populatedValue !== undefined && element.text === populatedValue) return true
  return allowAnyPopulated === true && typeof element.text === 'string' && element.text.length > 0
}

function observedBounds(element) {
  const value = element?.bounds
  if (
    !value
    || ![value.x1, value.y1, value.x2, value.y2].every(Number.isInteger)
    || value.x2 <= value.x1
    || value.y2 <= value.y1
  ) {
    throw new Error('login_form_not_exact_unique')
  }
  return `[${value.x1},${value.y1}][${value.x2},${value.y2}]`
}

function requireExactLoginForm(elements, { usernameValue, allowAnyPopulated = false } = {}) {
  if (!Array.isArray(elements)) throw new Error('login_form_not_exact_unique')
  const observed = {}
  for (const [name, control] of Object.entries(LOGIN_CONTROLS)) {
    const matches = elements.filter((element) => element?.resourceId === control.id)
    const element = matches[0]
    const populatedValue = name === 'username' ? usernameValue : undefined
    if (
      matches.length !== 1
      || element.className !== control.className
      || !labelMatches(element, control, populatedValue, allowAnyPopulated && name !== 'submit')
    ) {
      throw new Error('login_form_not_exact_unique')
    }
    observed[name] = {
      index: elements.indexOf(element),
      id: element.resourceId,
      className: element.className,
      bounds: observedBounds(element),
    }
  }
  return observed
}

function inspectAuthSurface(serial, invoke, formOptions) {
  const current = invokeAuth(invoke, 'current', androidArgs(serial))
  requirePofFocus(current)
  const dump = invokeAuth(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeAuthSurface(dump.elements || [])
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
  const controls = formOptions ? requireExactLoginForm(dump.elements, formOptions) : null
  return { elements: dump.elements || [], controls }
}

function inspectPostSubmitSurface(serial, invoke) {
  const current = invokeAuth(invoke, 'current', androidArgs(serial))
  requirePofFocus(current)
  const dump = invokeAuth(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeAuthSurface(dump.elements || [])
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
}

function freshLoginPreflight(options, invoke, formOptions) {
  const serial = loginPackagePreflight(options, invoke)
  const surface = inspectAuthSurface(serial, invoke, formOptions)
  return { serial, controls: surface.controls }
}

function loginPackagePreflight(options, invoke) {
  const packages = invokeAuth(
    invoke,
    'packages',
    androidArgs(options.serial, ['--package', PLENTY_OF_FISH_PACKAGE]),
  )
  if (!Array.isArray(packages.packages) || !packages.packages.includes(PLENTY_OF_FISH_PACKAGE)) {
    throw new Error('plenty-of-fish_not_installed')
  }
  return packages.serial || options.serial
}

function authIdentity(serial) {
  return {
    id: adapter.id,
    name: adapter.name,
    serial,
    package: PLENTY_OF_FISH_PACKAGE,
  }
}

function guardedTapArgs(serial, control) {
  return androidArgs(serial, [
    '--index', String(control.index),
    '--id', control.id,
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    ...UNSAFE_AUTH_SURFACES.flatMap(([, pattern]) => ['--reject-regex', pattern.source]),
  ])
}

function waitForExactLoginControl(serial, invoke, control) {
  invokeAuth(invoke, 'wait', androidArgs(serial, [
    '--id', control.id,
    '--text', control.label,
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    '--timeout-ms', '3000',
    '--poll-ms', '250',
  ]))
}

function fillLogin(options, invoke, credentialInput) {
  const credentials = parseCredentials(credentialInput)
  let serial = loginPackagePreflight(options, invoke)
  invokeAuth(invoke, 'launch', androidArgs(serial, ['--package', PLENTY_OF_FISH_PACKAGE]))
  waitForExactLoginControl(serial, invoke, LOGIN_CONTROLS.username)
  let preflight = {
    serial,
    controls: inspectAuthSurface(serial, invoke, {}).controls,
  }

  invokeAuth(invoke, 'tap', guardedTapArgs(serial, preflight.controls.username))
  inspectAuthSurface(serial, invoke, {})
  invokeAuth(invoke, 'type-stdin', androidArgs(serial), credentials.username)

  preflight = freshLoginPreflight({ ...options, serial }, invoke, { usernameValue: credentials.username })
  serial = preflight.serial
  invokeAuth(invoke, 'tap', guardedTapArgs(serial, preflight.controls.password))
  inspectAuthSurface(serial, invoke, { usernameValue: credentials.username })
  invokeAuth(invoke, 'type-stdin', androidArgs(serial), credentials.password)
  inspectAuthSurface(serial, invoke)

  return {
    ok: true,
    action: 'fill-login',
    ...authIdentity(serial),
    status: 'credentials-filled',
    submitted: false,
  }
}

function submitLogin(options, invoke) {
  if (options.confirm !== 'submit') throw new Error('submit_confirmation_required')
  const preflight = freshLoginPreflight(options, invoke, { allowAnyPopulated: true })
  const { serial } = preflight
  invokeAuth(invoke, 'tap', guardedTapArgs(serial, preflight.controls.submit))
  inspectPostSubmitSurface(serial, invoke)
  return {
    ok: true,
    action: 'submit-login',
    ...authIdentity(serial),
    status: 'submission-observed',
    authentication: 'unverified',
  }
}

export function execute(options, invoke, credentialInput) {
  if (STANDARD_COMMANDS.has(options.command)) return adapter.execute(options, invoke)
  if (options.command === 'fill-login') return fillLogin(options, invoke, credentialInput)
  if (options.command === 'submit-login') return submitLogin(options, invoke)
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
    let credentialInput
    if (options.command === 'fill-login') {
      try {
        credentialInput = readFileSync(0, 'utf8')
      } catch {
        throw new Error('credential_input_invalid')
      }
    }
    process.stdout.write(`${JSON.stringify(execute(options, invokeAndroid, credentialInput))}\n`)
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ ok: false, error: error.message, usage: authUsage() })}\n`)
    process.exitCode = 1
  }
}
