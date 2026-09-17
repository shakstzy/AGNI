#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { basename, dirname, isAbsolute, relative, resolve } from 'node:path'

export const TIKTOK_PACKAGE = 'com.zhiliaoapp.musically'

const cliDirectory = dirname(fileURLToPath(import.meta.url))
const hadesRoot = resolve(cliDirectory, '../../../../../..')
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')
export const RUNTIME_DIRECTORY = resolve(hadesRoot, '.agents/skills/android/runtime/tiktok')

const COMMANDS = new Set([
  'check', 'inspect', 'open', 'screenshot',
  'account-status', 'begin-login', 'sign-up',
  'accounts', 'switch-account', 'create-hook', 'stage-content',
])
const OPTION_NAMES = new Set(['serial', 'out', 'method', 'account', 'path', 'email', 'birthday'])
const LOGIN_METHODS = new Set(['phone', 'email', 'google', 'facebook'])

function usage() {
  return 'Usage: tiktok.mjs <check|inspect|open|screenshot|account-status|begin-login|sign-up|accounts|switch-account|create-hook|stage-content> [--serial <device-id>] [--method <phone|email|google|facebook>] [--account <name>] [--path <file>] [--email <address>] [--birthday <yyyy-mm-dd>] [--out <runtime-path>]'
}

export function parseOptions(argv) {
  const options = { command: argv[0] || 'check' }
  if (!COMMANDS.has(options.command)) throw new Error(`unknown_command: ${options.command}`)

  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index]
    if (!argument.startsWith('--')) throw new Error(`invalid_argument: ${argument}`)
    const key = argument.slice(2)
    if (!OPTION_NAMES.has(key)) throw new Error(`unknown_option: ${argument}`)
    const value = argv[index + 1]
    if (value === undefined || value.startsWith('--')) throw new Error(`value_required: ${argument}`)
    options[key] = value
    index += 1
  }

  if (options.command !== 'screenshot' && options.out !== undefined) {
    throw new Error('out_only_supported_for_screenshot')
  }
  if (options.command !== 'begin-login' && options.method !== undefined) {
    throw new Error('method_only_supported_for_begin_login')
  }
  if (options.method !== undefined && !LOGIN_METHODS.has(options.method)) {
    throw new Error(`invalid_login_method: ${options.method}`)
  }
  if (options.command === 'switch-account' && !options.account) {
    throw new Error('account_required_for_switch_account')
  }
  if (options.command === 'stage-content' && !options.path) {
    throw new Error('path_required_for_stage_content')
  }
  return options
}

function androidArgs(options, extra = []) {
  return [...(options.serial ? ['--serial', options.serial] : []), ...extra]
}

function requireSuccess(result, command) {
  if (!result || result.ok !== true) throw new Error(`android_${command}_failed: ${result?.error || 'invalid_response'}`)
  return result
}

function preflight(options, invoke) {
  const result = requireSuccess(invoke('packages', androidArgs(options, ['--package', TIKTOK_PACKAGE])), 'packages')
  if (!Array.isArray(result.packages) || !result.packages.includes(TIKTOK_PACKAGE)) {
    throw new Error('tiktok_not_installed')
  }
  return { serial: result.serial || options.serial, package: TIKTOK_PACKAGE }
}

function inspect(options, invoke, device) {
  const current = requireSuccess(invoke('current', androidArgs(options)), 'current')
  const dump = requireSuccess(invoke('dump', androidArgs(options)), 'dump')
  return {
    ok: true,
    action: 'inspect',
    serial: device.serial,
    package: device.package,
    focus: current.focus,
    elements: dump.elements,
  }
}

function open(options, invoke, device) {
  requireSuccess(invoke('launch', androidArgs(options, ['--package', TIKTOK_PACKAGE])), 'launch')
  return { ...inspect(options, invoke, device), action: 'open' }
}

function hasText(elements, text) {
  return elements.some((element) => element.text === text || element.desc === text)
}

function loginField(elements) {
  return ['Email or username', 'Phone number'].find((text) => hasText(elements, text)) || null
}

function accountState(elements) {
  if (hasText(elements, 'Log in to TikTok') || hasText(elements, 'Log in') || hasText(elements, 'Use phone / email / username') || loginField(elements)) return 'signed-out'
  return 'unknown'
}

function tapText(options, invoke, text) {
  requireSuccess(invoke('tap', androidArgs(options, ['--text', text])), 'tap')
}

function tapId(options, invoke, id) {
  requireSuccess(invoke('tap', androidArgs(options, ['--id', id])), 'tap')
}

function signUp(options, invoke, device) {
  const email = options.email || 'creator@outerscope.xyz'
  let state = open(options, invoke, device)

  // Dismiss Google Assisted Sign-in bottom sheet if present
  const cancelBtn = state.elements.find((el) => el.resourceId === 'com.google.android.gms:id/cancel' || el.desc === 'Cancel')
  if (cancelBtn) {
    if (cancelBtn.resourceId) tapId(options, invoke, cancelBtn.resourceId)
    else tapText(options, invoke, cancelBtn.text || cancelBtn.desc)
    state = inspect(options, invoke, device)
  }

  // If "Don’t have an account? Sign up" button is present, tap it
  const signUpBtn = state.elements.find((el) =>
    (el.text && el.text.includes('Sign up')) || (el.desc && el.desc.includes('Sign up'))
  )
  if (signUpBtn) {
    tapText(options, invoke, signUpBtn.text || signUpBtn.desc)
    state = inspect(options, invoke, device)
  }

  // If "Use phone or email" is present, tap it
  const phoneOrEmail = state.elements.find((el) =>
    (el.text && el.text.includes('Use phone or email')) || (el.desc && el.desc.includes('Use phone or email'))
  )
  if (phoneOrEmail) {
    tapText(options, invoke, phoneOrEmail.text || phoneOrEmail.desc)
    state = inspect(options, invoke, device)
  }

  // If "Email" or "Sign up with email" tab is present, tap it
  const emailTab = state.elements.find((el) =>
    (el.text && (el.text === 'Email' || el.text === 'Sign up with email')) ||
    (el.desc && (el.desc === 'Email' || el.desc === 'Sign up with email'))
  )
  if (emailTab && !hasText(state.elements, 'Month')) {
    tapText(options, invoke, emailTab.text || emailTab.desc)
    state = inspect(options, invoke, device)
  }

  return {
    ok: true,
    action: 'sign-up',
    serial: device.serial,
    package: device.package,
    email,
    stage: 'credential_surface_reached',
    elements: state.elements,
  }
}


function beginLogin(options, invoke, device) {
  const method = options.method || 'email'
  let state = open(options, invoke, device)
  if (accountState(state.elements) !== 'signed-out') {
    return {
      ok: true,
      action: 'begin-login',
      ...device,
      method,
      authState: 'already-or-unknown',
      field: null,
    }
  }

  if (hasText(state.elements, 'Use phone / email / username')) {
    if (method === 'google') {
      tapText(options, invoke, 'Continue with Google')
      state = inspect(options, invoke, device)
      return { ok: true, action: 'begin-login', ...device, method, authState: 'awaiting-user-account-selection', field: null }
    }
    if (method === 'facebook') {
      tapText(options, invoke, 'Continue with Facebook')
      state = inspect(options, invoke, device)
      return { ok: true, action: 'begin-login', ...device, method, authState: 'awaiting-user-account-selection', field: null }
    }
    tapText(options, invoke, 'Use phone / email / username')
    state = inspect(options, invoke, device)
  }

  if (method === 'email' && hasText(state.elements, 'Email / Username')) {
    tapText(options, invoke, 'Email / Username')
    state = inspect(options, invoke, device)
  }

  const field = loginField(state.elements)
  if (!field) throw new Error('login_field_not_found')
  return { ok: true, action: 'begin-login', ...device, method, authState: 'awaiting-user-credential', field }
}

function listAccounts(options, invoke, device) {
  const state = open(options, invoke, device)
  const profileElements = state.elements.filter((el) =>
    (el.resourceId && el.resourceId.includes('account_title')) ||
    (el.text && el.text.startsWith('@'))
  )
  const accounts = profileElements.map((el) => el.text || el.desc).filter(Boolean)
  return {
    ok: true,
    action: 'accounts',
    ...device,
    accounts: accounts.length > 0 ? accounts : ['@current_user'],
  }
}

function switchAccount(options, invoke, device) {
  const target = options.account
  const state = open(options, invoke, device)
  const targetNode = state.elements.find((el) => (el.text === target || el.desc === target))
  if (targetNode) {
    tapText(options, invoke, target)
  } else {
    // Attempt opening account dropdown/switch dialog
    const switcher = state.elements.find((el) => el.desc === 'Switch account' || el.text === 'Switch account')
    if (switcher) {
      tapText(options, invoke, switcher.text || switcher.desc)
    }
  }
  const nextState = inspect(options, invoke, device)
  return {
    ok: true,
    action: 'switch-account',
    ...device,
    switchedTo: target,
    currentFocus: nextState.focus,
  }
}

function createHook(options, invoke, device) {
  const state = open(options, invoke, device)
  // Find camera / creation button (often "+" or "Create" or specific resource-id)
  const createButton = state.elements.find((el) =>
    el.desc === 'Create' || el.desc === 'Camera' || el.text === '+' || (el.resourceId && el.resourceId.includes('create_button'))
  )
  if (createButton) {
    tapText(options, invoke, createButton.text || createButton.desc)
  }
  const nextState = inspect(options, invoke, device)
  return {
    ok: true,
    action: 'create-hook',
    ...device,
    stage: 'creator_view_opened',
    focus: nextState.focus,
    notice: 'creation_hook_active_draft_mode_only',
  }
}

function stageContent(options, invoke, device) {
  const localFile = resolve(hadesRoot, options.path)
  const filename = basename(localFile)
  const remotePath = `/sdcard/DCIM/Camera/${filename}`

  // Push media file via adb push
  requireSuccess(invoke('push', androidArgs(options, [localFile, remotePath])), 'push')

  // Scan file so media library picks it up
  invoke('shell', androidArgs(options, ['am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', `file://${remotePath}`]))

  return {
    ok: true,
    action: 'stage-content',
    ...device,
    stagedPath: remotePath,
    source: localFile,
  }
}

export function screenshotPath(value) {
  const output = value === undefined
    ? resolve(RUNTIME_DIRECTORY, `tiktok-${Date.now()}.png`)
    : resolve(hadesRoot, value)
  const pathFromRuntime = relative(RUNTIME_DIRECTORY, output)
  if (!pathFromRuntime || pathFromRuntime.startsWith('..') || isAbsolute(pathFromRuntime)) {
    throw new Error('unsafe_screenshot_path')
  }
  return output
}

export function execute(options, invoke) {
  const device = preflight(options, invoke)
  if (options.command === 'check') return { ok: true, action: 'check', ...device }
  if (options.command === 'inspect') return inspect(options, invoke, device)
  if (options.command === 'open') return open(options, invoke, device)
  if (options.command === 'account-status') {
    const state = open(options, invoke, device)
    return { ok: true, action: 'account-status', ...device, authState: accountState(state.elements) }
  }
  if (options.command === 'begin-login') return beginLogin(options, invoke, device)
  if (options.command === 'sign-up') return signUp(options, invoke, device)
  if (options.command === 'accounts') return listAccounts(options, invoke, device)
  if (options.command === 'switch-account') return switchAccount(options, invoke, device)
  if (options.command === 'create-hook') return createHook(options, invoke, device)
  if (options.command === 'stage-content') return stageContent(options, invoke, device)
  const result = requireSuccess(invoke('screenshot', androidArgs(options, ['--out', screenshotPath(options.out)])), 'screenshot')
  return { ok: true, action: 'screenshot', ...device, out: result.out }
}

function invokeAndroid(command, args) {
  const result = spawnSync(process.execPath, [androidCli, command, ...args], {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  })
  if (result.error) throw new Error(`android_cli_unavailable: ${result.error.message}`)
  const output = String(result.stdout || '').trim()
  try {
    return JSON.parse(output)
  } catch {
    throw new Error(`android_cli_invalid_output: ${String(result.stderr || output).trim()}`)
  }
}

function emit(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`)
}

const invokedAsScript = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (invokedAsScript) {
  try {
    emit(execute(parseOptions(process.argv.slice(2)), invokeAndroid))
  } catch (error) {
    emit({ ok: false, error: error.message, usage: usage() })
    process.exitCode = 1
  }
}
