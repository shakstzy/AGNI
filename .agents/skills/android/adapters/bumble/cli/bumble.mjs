#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { createStandardAppAdapter } from '../../cli/standard-app.mjs'

export const BUMBLE_PACKAGE = 'com.bumble.app'

const cliDirectory = dirname(fileURLToPath(import.meta.url))
const hadesRoot = resolve(cliDirectory, '../../../../../..')
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')
export const RUNTIME_DIRECTORY = resolve(hadesRoot, '.agents/skills/android/runtime/bumble')

const adapter = createStandardAppAdapter({
  id: 'bumble',
  name: 'Bumble',
  packageName: BUMBLE_PACKAGE,
  runtimeDirectory: RUNTIME_DIRECTORY,
})

const STANDARD_COMMANDS = new Set(['check', 'inspect', 'open', 'screenshot'])
const LOGIN_COMMANDS = new Set(['begin-login', 'fill-phone', 'request-code'])
const ENGAGEMENT_COMMANDS = new Set([
  'tab', 'cards', 'discover', 'open-card', 'like', 'pass', 'liked-you', 'chats', 'open-chat', 'send-message',
  'crawl-chats', 'inspect-thread', 'inspect-profile', 'ingest', 'send-batch',
])
const TAB_NAMES = Object.freeze({
  people: 'People',
  discover: 'Discover',
  'liked-you': 'Liked You',
  chats: 'Chats',
})
const TAB_BAR_MIN_Y = 1800
const PHONE_LOGIN_NAVIGATION = Object.freeze([
  Object.freeze({
    desc: 'I have an account',
    className: 'android.view.View',
    bounds: '[55,1702][1025,1834]',
  }),
  Object.freeze({
    desc: 'Continue with other methods',
    className: 'android.view.View',
    bounds: '[55,1702][1025,1834]',
  }),
  Object.freeze({
    desc: 'Use cell phone number',
    className: 'android.view.View',
    bounds: '[55,1669][1025,1801]',
  }),
])
const PHONE_SURFACE = Object.freeze({
  field: Object.freeze({
    id: 'com.bumble.app:id/reg_input_edittext',
    className: 'android.widget.EditText',
    bounds: '[325,742][1014,869]',
  }),
  continueButton: Object.freeze({
    id: 'com.bumble.app:id/reg_footer_button',
    text: '',
    desc: 'Continue',
    className: 'android.widget.Button',
  }),
})
const PROVIDER_OPTION_PATTERN = /\bcontinue with (?:google|facebook|apple)\b/
const UNSAFE_AUTH_SURFACES = Object.freeze([
  ['provider_or_account', /\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue as\b|\buse another account\b|\baccount owner\b|accounts\.google\.com/],
  ['provider_or_account', PROVIDER_OPTION_PATTERN],
  ['permission', /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/],
  ['passkey_or_identity', /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/],
  ['two_factor', /\btwo[- ]factor\b|\b2[- ]step\b|\benter (?:the )?(?:verification|authentication|security)?\s*code\b/],
  ['captcha', /captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge/],
  ['purchase', /\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b/],
  ['profile', /\bcreate (?:your )?profile\b|\bedit (?:your )?profile\b|\bcomplete (?:your )?profile\b|\bprofile setup\b/],
  ['social', /\bconnect (?:your )?(?:instagram|facebook|spotify|social)\b|\blink (?:your )?(?:instagram|facebook|spotify|social)\b/],
])
const FINAL_TAP_REJECT_PATTERNS = Object.freeze(
  UNSAFE_AUTH_SURFACES.map(([, pattern]) => pattern.source),
)
const PHONE_ROUTE_FINAL_TAP_REJECT_PATTERNS = Object.freeze(
  UNSAFE_AUTH_SURFACES
    .filter(([, pattern]) => pattern !== PROVIDER_OPTION_PATTERN)
    .map(([, pattern]) => pattern.source),
)
const ENGAGEMENT_UNSAFE_SURFACES = Object.freeze([
  ['purchase', /\b(?:subscribe|subscription|bumble boost|bumble premium|payment|billing|buy now)\b/],
  ['permission', /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/],
  ['passkey_or_identity', /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/],
])
const ENGAGEMENT_TAP_REJECT_PATTERNS = Object.freeze(
  ENGAGEMENT_UNSAFE_SURFACES.map(([, pattern]) => pattern.source),
)

function loginUsage() {
  return 'Usage: bumble.mjs <check|inspect|open|screenshot|begin-login|fill-phone|request-code|tab|cards|discover|open-card|like|pass|liked-you|chats|open-chat|send-message|crawl-chats|inspect-thread|inspect-profile|ingest|send-batch> [--serial <device-id>] [--out <runtime-path>] [--method phone] [--name <tab-or-match>] [--confirm <request|like|pass|send>] [--limit <number>] [--scrolls <number>]'
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

function parseEngagementOptions(argv) {
  const command = argv[0]
  const allowed = command === 'tab' || command === 'open-chat' || command === 'open-card'
    ? new Set(['serial', 'name'])
    : command === 'inspect-thread'
      ? new Set(['serial', 'name'])
      : command === 'inspect-profile'
        ? new Set(['serial', 'name', 'out'])
        : command === 'crawl-chats'
          ? new Set(['serial', 'limit', 'scrolls'])
          : command === 'ingest'
            ? new Set(['serial', 'limit', 'scrolls', 'out'])
            : command === 'like' || command === 'pass' || command === 'send-message' || command === 'send-batch'
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
  if (command === 'tab') {
    if (options.name === undefined) throw new Error('tab_name_required')
    if (TAB_NAMES[options.name] === undefined) throw new Error('unsupported_tab')
  }
  if (command === 'open-chat' && !options.name) throw new Error('chat_name_required')
  if (command === 'open-card' && !options.name) throw new Error('card_name_required')
  if (command === 'like' && options.confirm !== 'like') throw new Error('like_confirmation_required')
  if (command === 'pass' && options.confirm !== 'pass') throw new Error('pass_confirmation_required')
  if (command === 'send-message' && options.confirm !== 'send') throw new Error('send_confirmation_required')
  if (command === 'inspect-thread' && !options.name) throw new Error('chat_name_required')
  if (command === 'inspect-profile' && !options.name) throw new Error('profile_name_required')
  if (command === 'send-batch' && options.confirm !== 'send') throw new Error('send_confirmation_required')
  return options
}

export function parseOptions(argv) {
  if (LOGIN_COMMANDS.has(argv[0])) return parseLoginOptions(argv)
  if (ENGAGEMENT_COMMANDS.has(argv[0])) return parseEngagementOptions(argv)
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

function unsafeAuthSurface(elements, { allowProviderOptions = false } = {}) {
  const visibleText = elements
    .map((element) => `${element?.text || ''}\n${element?.desc || ''}\n${element?.resourceId || ''}`)
    .join('\n')
    .toLowerCase()
  return UNSAFE_AUTH_SURFACES.find(([category, pattern]) => (
    !(allowProviderOptions && pattern === PROVIDER_OPTION_PATTERN)
    && pattern.test(visibleText)
  ))?.[0] || null
}

function isBumbleFocus(current) {
  return (
    typeof current.focus !== 'string'
    ? false
    : /(?:^|[\s{])com\.bumble\.app(?:\/|[\s}])/.test(current.focus)
  )
}

function requireBumbleFocus(current) {
  if (!isBumbleFocus(current)) throw new Error('bumble_not_in_foreground')
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
    control.id === undefined
      ? element?.resourceId === '' && element.desc === control.desc
      : element?.resourceId === control.id
  ))
  if (candidates.length !== 1) throw new Error(error)
  const element = candidates[0]
  const bounds = serializedBounds(element)
  if (
    element.className !== control.className
    || (control.desc !== undefined && element.desc !== control.desc)
    || (control.text !== undefined && element.text !== control.text)
    || bounds === null
    || (control.bounds !== undefined && bounds !== control.bounds)
  ) {
    throw new Error(error)
  }
  return {
    index: elements.indexOf(element),
    ...(control.id === undefined ? {} : { id: control.id }),
    ...(control.desc === undefined ? {} : { desc: control.desc }),
    ...(control.text === undefined ? {} : { text: control.text }),
    className: control.className,
    bounds,
  }
}

function requireExactNavigationStep(step) {
  return (elements) => {
    if (!Array.isArray(elements)) throw new Error('phone_login_navigation_not_exact_unique')
    return exactControl(
      elements,
      PHONE_LOGIN_NAVIGATION[step],
      'phone_login_navigation_not_exact_unique',
    )
  }
}

function requireExactPhoneSurface(elements, { emptyPhone = false } = {}) {
  const error = 'phone_surface_not_exact_unique'
  if (!Array.isArray(elements)) throw new Error(error)
  return {
    field: exactControl(
      elements,
      emptyPhone ? { ...PHONE_SURFACE.field, text: '', desc: '' } : PHONE_SURFACE.field,
      error,
    ),
    continueButton: exactControl(elements, PHONE_SURFACE.continueButton, error),
  }
}

function inspectLoginSurface(serial, invoke, validator, options) {
  const current = invokeLogin(invoke, 'current', androidArgs(serial))
  requireBumbleFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeAuthSurface(dump.elements || [], options)
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
  return validator(dump.elements)
}

function freshLoginPreflight(options, invoke, validator) {
  const serial = packagePreflight(options, invoke)
  return { serial, controls: inspectLoginSurface(serial, invoke, validator) }
}

function packagePreflight(options, invoke) {
  const packages = invokeLogin(
    invoke,
    'packages',
    androidArgs(options.serial, ['--package', BUMBLE_PACKAGE]),
  )
  if (!Array.isArray(packages.packages) || !packages.packages.includes(BUMBLE_PACKAGE)) {
    throw new Error('bumble_not_installed')
  }
  return packages.serial || options.serial
}

function loginIdentity(serial) {
  return {
    id: adapter.id,
    name: adapter.name,
    serial,
    package: BUMBLE_PACKAGE,
  }
}

function guardedTapArgs(serial, control, { allowProviderOptions = false } = {}) {
  const rejectPatterns = allowProviderOptions
    ? PHONE_ROUTE_FINAL_TAP_REJECT_PATTERNS
    : FINAL_TAP_REJECT_PATTERNS
  return androidArgs(serial, [
    '--index', String(control.index),
    ...(control.desc === undefined ? [] : ['--desc', control.desc]),
    ...(control.text === undefined ? [] : ['--text', control.text]),
    ...(control.id === undefined ? [] : ['--id', control.id]),
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    ...rejectPatterns.flatMap((pattern) => ['--reject-regex', pattern]),
  ])
}

function waitForExactControl(serial, invoke, control, { allowTimeout = false } = {}) {
  let result
  try {
    result = invoke('wait', androidArgs(serial, [
      ...(control.desc === undefined ? [] : ['--desc', control.desc]),
      ...(control.text === undefined ? [] : ['--text', control.text]),
      ...(control.id === undefined ? [] : ['--id', control.id]),
      '--class', control.className,
      '--bounds', control.bounds,
      '--unique', 'true',
      '--timeout-ms', '3000',
      '--poll-ms', '250',
    ]), undefined, { redactErrors: true })
  } catch {
    throw new Error('android_wait_failed')
  }
  if (result?.ok === true) return true
  if (allowTimeout && typeof result?.error === 'string' && result.error.startsWith('wait_timeout:')) {
    return false
  }
  throw new Error('android_wait_failed')
}

function inspectPostRequestSurface(serial, invoke) {
  const current = invokeLogin(invoke, 'current', androidArgs(serial))
  requireBumbleFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  if (!Array.isArray(dump.elements)) throw new Error('post_request_surface_invalid')
  const unsafe = unsafeAuthSurface(dump.elements)
  if (unsafe) throw new Error(`unsafe_auth_surface: ${unsafe}`)
}

function waitForEmptyPhoneForm(serial, invoke, { allowTimeout = false } = {}) {
  return waitForExactControl(serial, invoke, { ...PHONE_SURFACE.field, text: '', desc: '' }, { allowTimeout })
}

function beginLoginResult(serial) {
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
  const serial = packagePreflight(options, invoke)
  invokeLogin(invoke, 'launch', androidArgs(serial, ['--package', BUMBLE_PACKAGE]))
  if (waitForEmptyPhoneForm(serial, invoke, { allowTimeout: true })) {
    inspectLoginSurface(
      serial,
      invoke,
      (elements) => requireExactPhoneSurface(elements, { emptyPhone: true }),
    )
    return beginLoginResult(serial)
  }

  waitForExactControl(serial, invoke, PHONE_LOGIN_NAVIGATION[0])
  const account = inspectLoginSurface(serial, invoke, requireExactNavigationStep(0))
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, account))

  waitForExactControl(serial, invoke, PHONE_LOGIN_NAVIGATION[1])
  const otherMethods = inspectLoginSurface(serial, invoke, requireExactNavigationStep(1))
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, otherMethods))

  waitForExactControl(serial, invoke, PHONE_LOGIN_NAVIGATION[2])
  const phoneMethod = inspectLoginSurface(
    serial,
    invoke,
    requireExactNavigationStep(2),
    { allowProviderOptions: true },
  )
  invokeLogin(invoke, 'tap', guardedTapArgs(serial, phoneMethod, { allowProviderOptions: true }))
  waitForEmptyPhoneForm(serial, invoke)
  inspectLoginSurface(
    serial,
    invoke,
    (elements) => requireExactPhoneSurface(elements, { emptyPhone: true }),
  )

  return beginLoginResult(serial)
}

function fillPhone(options, invoke, phoneInput) {
  const phone = parsePhone(phoneInput)
  const requireEmptyPhoneSurface = (elements) => (
    requireExactPhoneSurface(elements, { emptyPhone: true })
  )
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

function parseMessage(input) {
  let value
  try {
    value = JSON.parse(input)
  } catch {
    throw new Error('message_input_invalid')
  }
  const keys = value && !Array.isArray(value) && typeof value === 'object'
    ? Object.keys(value)
    : []
  if (
    keys.length !== 1
    || keys[0] !== 'message'
    || typeof value.message !== 'string'
    || value.message.trim().length === 0
  ) {
    throw new Error('message_input_invalid')
  }
  return value.message.replace(/[\r\n]+/g, ' ').trim()
}

function unsafeEngagementSurface(elements) {
  const visibleText = (elements || [])
    .map((element) => `${element?.text || ''}\n${element?.desc || ''}\n${element?.resourceId || ''}`)
    .join('\n')
    .toLowerCase()
  return ENGAGEMENT_UNSAFE_SURFACES.find(([, pattern]) => pattern.test(visibleText))?.[0] || null
}

function sleepSync(ms) {
  try {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
  } catch {}
}

function inspectEngagement(serial, invoke, validator) {
  let current = invokeLogin(invoke, 'current', androidArgs(serial))
  for (let attempt = 0; attempt < 5 && !isBumbleFocus(current); attempt += 1) {
    sleepSync(250)
    current = invokeLogin(invoke, 'current', androidArgs(serial))
  }
  requireBumbleFocus(current)
  const dump = invokeLogin(invoke, 'dump', androidArgs(serial))
  const unsafe = unsafeEngagementSurface(dump.elements || [])
  if (unsafe) throw new Error(`unsafe_engagement_surface: ${unsafe}`)
  return validator(dump.elements || [])
}

function engagementTapArgs(serial, control) {
  return androidArgs(serial, [
    '--index', String(control.index),
    ...(control.desc === undefined ? [] : ['--desc', control.desc]),
    ...(control.text === undefined ? [] : ['--text', control.text]),
    ...(control.id ? ['--id', control.id] : []),
    '--class', control.className,
    '--bounds', control.bounds,
    '--unique', 'true',
    ...ENGAGEMENT_TAP_REJECT_PATTERNS.flatMap((pattern) => ['--reject-regex', pattern]),
  ])
}

function uniqueDescControl(elements, desc, { minY, error } = {}) {
  const matches = elements.filter((element) => (
    element?.desc === desc
    && serializedBounds(element)
    && (minY === undefined || element.bounds.y1 >= minY)
  ))
  if (matches.length !== 1) throw new Error(error || 'control_not_exact_unique')
  const element = matches[0]
  return {
    index: elements.indexOf(element),
    desc,
    className: element.className,
    bounds: serializedBounds(element),
    ...(element.resourceId ? { id: element.resourceId } : {}),
  }
}

function peopleCards(elements) {
  const cards = []
  for (const element of elements) {
    const match = String(element?.text || '').match(/^([^,]+), (\d+)$/)
    if (!match || !element.bounds || element.bounds.y1 >= TAB_BAR_MIN_Y) continue
    const subtitle = elements.find((other) => (
      other?.text
      && other.bounds
      && other.bounds.y1 >= element.bounds.y2
      && other.bounds.y1 <= element.bounds.y2 + 160
      && !/^([^,]+), (\d+)$/.test(other.text)
    ))
    cards.push({
      name: match[1],
      age: Number(match[2]),
      subtitle: subtitle?.text || '',
    })
  }
  return cards
}

function discoverCards(elements) {
  const cards = []
  for (const element of elements) {
    const match = String(element?.desc || '').match(/^(.+), (\d+), profile (\d+) of (\d+)$/)
    if (!match) continue
    cards.push({
      name: match[1],
      age: Number(match[2]),
      index: Number(match[3]),
      total: Number(match[4]),
    })
  }
  return cards
}

function likedYouProfiles(elements) {
  const profiles = []
  for (const element of elements) {
    const match = String(element?.desc || '').match(/^Check out (.+)['’]s profile$/)
    if (match) profiles.push({ name: match[1] })
  }
  return profiles
}

function chatRows(elements) {
  const chats = []
  for (let index = 0; index < elements.length; index += 1) {
    if (elements[index]?.resourceId !== 'com.bumble.app:id/connectionsItem_personName') continue
    const row = { name: elements[index].text || '', preview: '', badge: '' }
    for (let next = index + 1; next < elements.length; next += 1) {
      const id = elements[next]?.resourceId
      if (id === 'com.bumble.app:id/connectionsItem_personName') break
      if (id === 'com.bumble.app:id/connectionsItem_message') row.preview = elements[next].text || ''
      if (id === 'com.bumble.app:id/connectionItem_badge') row.badge = elements[next].text || ''
    }
    chats.push(row)
  }
  return chats
}

function tabCommand(options, invoke) {
  const label = TAB_NAMES[options.name]
  const serial = packagePreflight(options, invoke)
  let current = invokeLogin(invoke, 'current', androidArgs(serial))
  if (typeof current?.focus === 'string' && current.focus.includes('ConversationActivity')) {
    try { invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back']) } catch {}
    sleepSync(400)
  }
  const control = inspectEngagement(
    serial,
    invoke,
    (elements) => uniqueDescControl(elements, label, {
      minY: TAB_BAR_MIN_Y,
      error: 'tab_not_exact_unique',
    }),
  )
  invokeLogin(invoke, 'tap', engagementTapArgs(serial, control))
  inspectEngagement(serial, invoke, () => null)
  return {
    ok: true,
    action: 'tab',
    ...loginIdentity(serial),
    tab: options.name,
  }
}

function listCommand(options, invoke, action, parser, key) {
  const serial = packagePreflight(options, invoke)
  const items = inspectEngagement(serial, invoke, parser)
  return { ok: true, action, ...loginIdentity(serial), [key]: items }
}

function voteCommand(options, invoke, { confirm, desc, status, error }) {
  if (options.confirm !== confirm) throw new Error(`${confirm}_confirmation_required`)
  const serial = packagePreflight(options, invoke)
  const control = inspectEngagement(
    serial,
    invoke,
    (elements) => uniqueDescControl(elements, desc, { error }),
  )
  invokeLogin(invoke, 'tap', engagementTapArgs(serial, control))
  inspectEngagement(serial, invoke, () => null)
  return {
    ok: true,
    action: options.command,
    ...loginIdentity(serial),
    status,
  }
}

function openCard(options, invoke) {
  const serial = packagePreflight(options, invoke)
  const control = inspectEngagement(serial, invoke, (elements) => {
    const desc = (elements || [])
      .map((element) => element?.desc || '')
      .find((value) => value.startsWith(`${options.name}, `) && /profile \d+ of \d+$/.test(value))
    if (!desc) throw new Error('card_not_found')
    return uniqueDescControl(elements, desc, { error: 'card_not_exact_unique' })
  })
  invokeLogin(invoke, 'tap', engagementTapArgs(serial, control))
  inspectEngagement(serial, invoke, () => null)
  return {
    ok: true,
    action: 'open-card',
    ...loginIdentity(serial),
    name: options.name,
  }
}

function openChat(options, invoke) {
  const serial = packagePreflight(options, invoke)
  let current = invokeLogin(invoke, 'current', androidArgs(serial))
  for (let a = 0; a < 3 && typeof current?.focus === 'string' && current.focus.includes('ConversationActivity'); a += 1) {
    try { invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back']) } catch {}
    sleepSync(300)
    try { current = invokeLogin(invoke, 'current', androidArgs(serial)) } catch {}
  }

  const findTargetControl = (elements) => {
    const desc = elements
      .map((element) => element?.desc || '')
      .find((value) => value.startsWith(`${options.name}, `))
    if (desc) return uniqueDescControl(elements, desc, { error: 'chat_row_not_exact_unique' })
    const nameMatch = elements.find((element) => (
      element?.resourceId === 'com.bumble.app:id/connectionsItem_personName' && element.text === options.name
    ))
    if (nameMatch && serializedBounds(nameMatch)) {
      return {
        index: elements.indexOf(nameMatch),
        id: nameMatch.resourceId,
        text: nameMatch.text,
        className: nameMatch.className,
        bounds: serializedBounds(nameMatch),
      }
    }
    return null
  }

  let control = null
  try {
    const initialSurface = inspectEngagement(serial, invoke, (elements) => {
      const target = findTargetControl(elements)
      const hasChatRows = elements.some((el) => el?.resourceId === 'com.bumble.app:id/connectionsItem_personName')
      return { target, hasChatRows }
    })
    if (initialSurface.target) {
      control = initialSurface.target
    } else if (!initialSurface.hasChatRows) {
      tabCommand({ command: 'tab', name: 'chats', serial }, invoke)
    }
  } catch {}

  if (!control) {
    for (let attempt = 0; attempt < 5; attempt += 1) {
      try {
        control = inspectEngagement(serial, invoke, findTargetControl)
        if (control) break
      } catch {}
      if (attempt < 4) {
        try {
          invoke('swipe', [...(serial ? ['--serial', serial] : []), '--from', '500,1600', '--to', '500,700'])
          sleepSync(300)
        } catch {
          break
        }
      }
    }
  }

  if (!control) {
    for (let attempt = 0; attempt < 5; attempt += 1) {
      try {
        invoke('swipe', [...(serial ? ['--serial', serial] : []), '--from', '500,700', '--to', '500,1600'])
        sleepSync(200)
      } catch {
        break
      }
    }
    try {
      control = inspectEngagement(serial, invoke, findTargetControl)
    } catch {}
  }

  if (!control) {
    throw new Error('chat_row_not_found')
  }

  invokeLogin(invoke, 'tap', engagementTapArgs(serial, control))
  inspectEngagement(serial, invoke, () => null)
  return {
    ok: true,
    action: 'open-chat',
    ...loginIdentity(serial),
    name: options.name,
  }
}

function sendMessage(options, invoke, messageInput) {
  if (options.confirm !== 'send') throw new Error('send_confirmation_required')
  const message = parseMessage(messageInput)
  const serial = packagePreflight(options, invoke)
  const field = inspectEngagement(serial, invoke, (elements) => {
    const matches = elements.filter((element) => (
      element?.resourceId === 'com.bumble.app:id/chatInput_text'
      && serializedBounds(element)
    ))
    if (matches.length !== 1) throw new Error('chat_input_not_exact_unique')
    const element = matches[0]
    return {
      index: elements.indexOf(element),
      id: element.resourceId,
      className: element.className,
      bounds: serializedBounds(element),
    }
  })
  invokeLogin(invoke, 'tap', engagementTapArgs(serial, field))
  inspectEngagement(serial, invoke, () => null)
  invokeLogin(invoke, 'type-stdin', androidArgs(serial), message)
  const send = inspectEngagement(
    serial,
    invoke,
    (elements) => {
      const matches = elements.filter((element) => (
        (element?.desc === 'Send' || element?.desc === 'Send message' || element?.resourceId === 'com.bumble.app:id/chatInput_button_send')
        && serializedBounds(element)
      ))
      if (matches.length !== 1) throw new Error('send_control_not_exact_unique')
      const element = matches[0]
      return {
        index: elements.indexOf(element),
        desc: element.desc || 'Send',
        className: element.className,
        bounds: serializedBounds(element),
        ...(element.resourceId ? { id: element.resourceId } : {}),
      }
    },
  )
  invokeLogin(invoke, 'tap', engagementTapArgs(serial, send))
  inspectEngagement(serial, invoke, () => null)
  return {
    ok: true,
    action: 'send-message',
    ...loginIdentity(serial),
    status: 'message-submitted',
  }
}

function crawlChats(options, invoke) {
  const serial = packagePreflight(options, invoke)
  let dump = inspectEngagement(serial, invoke, (elements) => elements)
  let rows = chatRows(dump)
  if (rows.length === 0) {
    try {
      tabCommand({ command: 'tab', name: 'chats', serial }, invoke)
      dump = inspectEngagement(serial, invoke, (elements) => elements)
      rows = chatRows(dump)
    } catch {}
  }

  const maxScrolls = Number(options.scrolls || 10)
  const limit = Number(options.limit || 50)
  const seenMap = new Map()

  for (const row of rows) {
    if (row.name && !seenMap.has(row.name)) {
      seenMap.set(row.name, row)
    }
  }

  for (let s = 0; s < maxScrolls; s += 1) {
    if (seenMap.size >= limit) break

    try {
      invoke('swipe', [...(serial ? ['--serial', serial] : []), '--from', '500,1600', '--to', '500,600'])
    } catch {
      break
    }

    const nextDump = inspectEngagement(serial, invoke, (elements) => elements)
    const nextRows = chatRows(nextDump)
    let newFound = 0
    for (const row of nextRows) {
      if (row.name && !seenMap.has(row.name)) {
        seenMap.set(row.name, row)
        newFound += 1
      }
    }
    if (newFound === 0) break
  }

  return {
    ok: true,
    action: 'crawl-chats',
    ...loginIdentity(serial),
    total_found: seenMap.size,
    chats: [...seenMap.values()].slice(0, limit),
  }
}

function extractMessages(elements, matchName) {
  const messages = []
  const phoneRegex = /(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})/
  let phone = ''

  for (const element of elements) {
    const text = String(element?.text || '').trim()
    const id = element?.resourceId || ''
    const bounds = element?.bounds || {}
    if (!text || text === 'Aa' || text === matchName || id.includes('Toolbar') || id.includes('chatInput')) continue
    if (element?.className === 'android.widget.Button' || element?.className === 'android.widget.ImageButton') continue
    if (text === 'Voice call' || text === 'Video call' || text === 'Send' || text === 'Navigate up' || text === 'Back') continue

    const isFromMe = (bounds.x !== undefined && bounds.x > 500) || (bounds.x1 !== undefined && bounds.x1 > 350)
    const sender = isFromMe ? 'You' : matchName

    messages.push({
      sender,
      text,
      bounds,
    })

    if (!phone) {
      const pm = text.match(phoneRegex)
      if (pm) phone = `${pm[1]}${pm[2]}${pm[3]}`
    }
  }
  return { messages, phone }
}

function inspectThread(options, invoke) {
  const serial = packagePreflight(options, invoke)
  openChat({ command: 'open-chat', name: options.name, serial }, invoke)

  const elements = inspectEngagement(serial, invoke, (el) => el)
  const { messages, phone } = extractMessages(elements, options.name)

  try {
    const backBtn = elements.find((item) => (
      item?.desc === 'Navigate up' || item?.desc === 'Back' || (item?.className === 'android.widget.ImageButton' && item?.bounds?.y1 < 300)
    ))
    if (backBtn && serializedBounds(backBtn)) {
      invokeLogin(invoke, 'tap', engagementTapArgs(serial, {
        index: elements.indexOf(backBtn),
        desc: backBtn.desc || 'Navigate up',
        className: backBtn.className,
        bounds: serializedBounds(backBtn),
      }))
      inspectEngagement(serial, invoke, () => null)
    } else {
      invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back'])
    }
  } catch {
    try { invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back']) } catch {}
  }

  for (let a = 0; a < 3; a += 1) {
    try {
      const cur = invokeLogin(invoke, 'current', androidArgs(serial))
      if (!cur?.focus || !cur.focus.includes('ConversationActivity')) break
      invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back'])
      sleepSync(300)
    } catch {
      break
    }
  }

  const lastMsg = messages[messages.length - 1]
  const hasInbound = messages.some((m) => m.sender === options.name)
  const lastFrom = lastMsg ? (lastMsg.sender === 'You' ? 'me' : options.name) : ''

  return {
    ok: true,
    action: 'inspect-thread',
    ...loginIdentity(serial),
    name: options.name,
    messages,
    has_phone: Boolean(phone),
    phone: phone || null,
    has_inbound: hasInbound,
    last_from: lastFrom,
  }
}

function inspectProfile(options, invoke) {
  const serial = packagePreflight(options, invoke)
  try {
    openChat({ command: 'open-chat', name: options.name, serial }, invoke)
  } catch {}

  try {
    const avatar = inspectEngagement(serial, invoke, (elements) => {
      const match = elements.find((el) => (
        el?.desc === 'View profile' || el?.resourceId === 'com.bumble.app:id/chatToolbar_avatar'
      ))
      if (!match) return null
      return {
        desc: match.desc || 'View profile',
        className: match.className,
        bounds: serializedBounds(match),
      }
    })
    if (avatar) {
      invokeLogin(invoke, 'tap', engagementTapArgs(serial, avatar))
      inspectEngagement(serial, invoke, () => null)
    }
  } catch {}

  const p1 = inspectEngagement(serial, invoke, (elements) => elements)
  try {
    invoke('swipe', [...(serial ? ['--serial', serial] : []), '--x1', '500', '--y1', '1600', '--x2', '500', '--y2', '600'])
  } catch {}
  const p2 = inspectEngagement(serial, invoke, (elements) => elements)

  let age = null
  let occupation = ''
  let education = ''
  const prompts = []
  const bioLines = []

  const allElements = [...p1, ...p2]
  for (const el of allElements) {
    const text = String(el?.text || '').trim()
    if (!text || text === 'Aa' || text === 'Send') continue
    const ageMatch = text.match(/^([^,]+),\s*(\d+)$/)
    if (ageMatch && !age) {
      age = Number(ageMatch[2])
      continue
    }
    if (text.includes('Engineer') || text.includes('Doctor') || text.includes('Manager') || text.includes('Director') || text.includes('Designer') || text.includes('at ')) {
      if (!occupation) occupation = text
    } else if (text.includes('University') || text.includes('College') || text.includes('School') || text.includes('UT') || text.includes('Texas') || text.includes('High School')) {
      if (!education) education = text
    } else if (text.length > 20) {
      bioLines.push(text)
    }
  }

  try {
    const closeBtn = p1.find((item) => item?.desc === 'Close' || item?.desc === 'Back' || item?.desc === 'Navigate up')
    if (closeBtn && serializedBounds(closeBtn)) {
      invokeLogin(invoke, 'tap', engagementTapArgs(serial, {
        index: p1.indexOf(closeBtn),
        desc: closeBtn.desc || 'Close',
        className: closeBtn.className,
        bounds: serializedBounds(closeBtn),
      }))
      inspectEngagement(serial, invoke, () => null)
    } else {
      invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back'])
    }
  } catch {
    try { invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back']) } catch {}
  }

  try {
    invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back'])
  } catch {}

  return {
    ok: true,
    action: 'inspect-profile',
    ...loginIdentity(serial),
    name: options.name,
    profile: {
      name: options.name,
      age,
      occupation,
      education,
      bio: bioLines.join(' '),
      prompts,
    },
  }
}

function parseBatchInput(input) {
  let list
  try {
    list = JSON.parse(input)
  } catch {
    throw new Error('batch_input_invalid')
  }
  if (!Array.isArray(list)) throw new Error('batch_input_must_be_array')
  return list
}

function sendBatch(options, invoke, batchInput) {
  if (options.confirm !== 'send') throw new Error('send_confirmation_required')
  const items = parseBatchInput(batchInput)
  const serial = packagePreflight(options, invoke)
  const results = []

  for (const item of items) {
    const name = item?.name
    const message = item?.message
    if (!name || !message) continue

    try {
      openChat({ command: 'open-chat', name, serial }, invoke)
      sendMessage({ command: 'send-message', confirm: 'send', serial }, invoke, JSON.stringify({ message }))

      for (let a = 0; a < 3; a += 1) {
        try {
          const cur = invokeLogin(invoke, 'current', androidArgs(serial))
          if (!cur?.focus || !cur.focus.includes('ConversationActivity')) break
          invoke('key', [...(serial ? ['--serial', serial] : []), '--name', 'back'])
          sleepSync(300)
        } catch {
          break
        }
      }

      results.push({ name, status: 'sent' })
    } catch (err) {
      results.push({ name, status: 'failed', error: err.message })
    }
  }

  return {
    ok: true,
    action: 'send-batch',
    ...loginIdentity(serial),
    sent_count: results.filter((r) => r.status === 'sent').length,
    results,
  }
}

function ingest(options, invoke) {
  const serial = packagePreflight(options, invoke)
  const crawl = crawlChats(options, invoke)
  const limit = Number(options.limit || 50)
  const targetChats = (crawl.chats || []).slice(0, limit)
  const ingested = []

  for (const chat of targetChats) {
    try {
      const thread = inspectThread({ command: 'inspect-thread', name: chat.name, serial }, invoke)
      let profile = null
      try {
        profile = inspectProfile({ command: 'inspect-profile', name: chat.name, serial, out: options.out }, invoke)
      } catch {}
      ingested.push({
        name: chat.name,
        badge: chat.badge,
        preview: chat.preview,
        messages: thread.messages || [],
        phone: thread.phone || null,
        profile: profile?.profile || null,
      })
    } catch (err) {
      ingested.push({
        name: chat.name,
        badge: chat.badge,
        preview: chat.preview,
        error: err.message,
      })
    }
  }

  return {
    ok: true,
    action: 'ingest',
    ...loginIdentity(serial),
    total_found: crawl.total_found,
    ingested_count: ingested.length,
    profiles: ingested,
  }
}

function executeEngagement(options, invoke, messageInput) {
  if (options.command === 'tab') return tabCommand(options, invoke)
  if (options.command === 'cards') return listCommand(options, invoke, 'cards', peopleCards, 'cards')
  if (options.command === 'discover') return listCommand(options, invoke, 'discover', discoverCards, 'cards')
  if (options.command === 'liked-you') {
    return listCommand(options, invoke, 'liked-you', likedYouProfiles, 'profiles')
  }
  if (options.command === 'chats') return listCommand(options, invoke, 'chats', chatRows, 'chats')
  if (options.command === 'like') {
    return voteCommand(options, invoke, {
      confirm: 'like',
      desc: 'Like',
      status: 'like-observed',
      error: 'like_control_not_exact_unique',
    })
  }
  if (options.command === 'pass') {
    return voteCommand(options, invoke, {
      confirm: 'pass',
      desc: 'Not for me',
      status: 'pass-observed',
      error: 'pass_control_not_exact_unique',
    })
  }
  if (options.command === 'open-card') return openCard(options, invoke)
  if (options.command === 'open-chat') return openChat(options, invoke)
  if (options.command === 'send-message') return sendMessage(options, invoke, messageInput)
  if (options.command === 'crawl-chats') return crawlChats(options, invoke)
  if (options.command === 'inspect-thread') return inspectThread(options, invoke)
  if (options.command === 'inspect-profile') return inspectProfile(options, invoke)
  if (options.command === 'ingest') return ingest(options, invoke)
  if (options.command === 'send-batch') return sendBatch(options, invoke, messageInput)
  throw new Error(`unknown_command: ${options.command}`)
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
    if (options.command === 'fill-phone' || options.command === 'send-message' || options.command === 'send-batch') {
      try {
        phoneInput = readFileSync(0, 'utf8')
      } catch {
        throw new Error(options.command === 'send-batch' ? 'batch_input_invalid' : options.command === 'send-message' ? 'message_input_invalid' : 'phone_input_invalid')
      }
    }
    process.stdout.write(`${JSON.stringify(execute(options, invokeAndroid, phoneInput))}\n`)
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ ok: false, error: error.message, usage: loginUsage() })}\n`)
    process.exitCode = 1
  }
}
