#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, isAbsolute, relative, resolve } from 'node:path'
import { createStandardAppAdapter } from '../../cli/standard-app.mjs'

export const DILMIL_PACKAGE = 'co.dilmil.android'

const cliDirectory = dirname(fileURLToPath(import.meta.url))
const hadesRoot = resolve(cliDirectory, '../../../../../..')
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')
export const RUNTIME_DIRECTORY = resolve(hadesRoot, '.agents/skills/android/runtime/dilmil')

const standardAdapter = createStandardAppAdapter({
  id: 'dilmil',
  name: 'Dil Mil',
  packageName: DILMIL_PACKAGE,
  runtimeDirectory: RUNTIME_DIRECTORY,
})

const STANDARD_COMMANDS = new Set(['check', 'inspect', 'open', 'screenshot'])
const AUTH_COMMANDS = new Set(['begin-login', 'fill-phone', 'verify-otp'])
const MONITORING_COMMANDS = new Set(['connections', 'matches'])
const ALL_COMMANDS = new Set([...STANDARD_COMMANDS, ...AUTH_COMMANDS, ...MONITORING_COMMANDS])

const UNSAFE_AUTH_SURFACES = Object.freeze([
  ['provider_or_account', /\b(?:choose|select)\s+(?:an?\s+)?account\b|\bcontinue as\b|\bcontinue with (?:google|facebook|apple)\b|\buse another account\b|\baccount owner\b|\bgoogle account\b|accounts\.google\.com/i],
  ['permission', /\b(?:allow|deny)\b.{0,80}\b(?:access|permission|photos?|camera|microphone|location|contacts?)\b|\bwhile using the app\b|\bonly this time\b|permissioncontroller/i],
  ['passkey_or_identity', /\bpasskey\b|\b(?:verify|confirm) your identity\b|\bscreen lock\b|\bpassword manager\b/i],
  ['two_factor', /\btwo[- ]factor\b|\b2[- ]step\b|\b2fa\b/i],
  ['captcha', /captcha|i(?:'|’)m not a robot|verify (?:that )?you(?:'re| are) human|security challenge/i],
  ['purchase', /\bpurchase\b|\bsubscribe\b|\bpayment\b|\bbilling\b|\bbuy now\b|\bdil mil (?:vip|elite|boost)\b/i],
])

export function parseOptions(argv) {
  const command = argv[0] || 'check'
  if (!ALL_COMMANDS.has(command)) {
    throw new Error(`unknown_command: ${command}`)
  }

  const options = { command }
  for (let i = 1; i < argv.length; i += 1) {
    const arg = argv[i]
    if (!arg.startsWith('--')) throw new Error(`invalid_argument: ${arg}`)
    const key = arg.slice(2)
    const val = argv[i + 1]
    if (val === undefined || val.startsWith('--')) throw new Error(`value_required: ${arg}`)
    options[key] = val
    i += 1
  }

  if (command === 'begin-login') {
    if (!options.method) throw new Error('phone_login_method_required')
    if (options.method !== 'phone') throw new Error('unsupported_login_method')
  }

  if (command === 'verify-otp') {
    if (options.confirm !== 'verify') throw new Error('verify_confirmation_required')
  }

  return options
}

function checkUnsafeSurfaces(elements) {
  for (const element of elements) {
    const label = `${element.text || ''} ${element.desc || ''}`.trim()
    if (!label) continue
    for (const [category, regex] of UNSAFE_AUTH_SURFACES) {
      if (regex.test(label)) {
        throw new Error(`unsafe_surface_detected: ${category}`)
      }
    }
  }
}

export function execute(options, invoke) {
  if (STANDARD_COMMANDS.has(options.command)) {
    return standardAdapter.execute(options, invoke)
  }

  const device = standardAdapter.execute({ command: 'check', serial: options.serial }, invoke)
  const serialArgs = options.serial ? ['--serial', options.serial] : []

  if (options.command === 'begin-login') {
    invoke('launch', [...serialArgs, '--package', DILMIL_PACKAGE])
    const dump = invoke('dump', serialArgs)
    checkUnsafeSurfaces(dump.elements)

    const phoneRouteButton = dump.elements.find((el) =>
      /sign in with phone|phone number|continue with phone/i.test(el.text || el.desc || '')
    )
    if (phoneRouteButton) {
      invoke('tap', [...serialArgs, '--text', phoneRouteButton.text || phoneRouteButton.desc])
    }

    const nextDump = invoke('dump', serialArgs)
    checkUnsafeSurfaces(nextDump.elements)

    return {
      ok: true,
      action: 'begin-login',
      serial: device.serial,
      package: DILMIL_PACKAGE,
      status: 'ready_for_phone',
    }
  }

  if (options.command === 'fill-phone') {
    let payload
    try {
      const raw = readFileSync(0, 'utf8')
      payload = JSON.parse(raw)
    } catch {
      throw new Error('invalid_phone_stdin')
    }
    if (!payload || typeof payload.phone !== 'string' || !payload.phone) {
      throw new Error('phone_string_required')
    }

    const currentDump = invoke('dump', serialArgs)
    checkUnsafeSurfaces(currentDump.elements)

    invoke('type-stdin', serialArgs, payload.phone)

    return {
      ok: true,
      action: 'fill-phone',
      serial: device.serial,
      package: DILMIL_PACKAGE,
      status: 'phone_entered',
    }
  }

  if (options.command === 'verify-otp') {
    let payload
    try {
      const raw = readFileSync(0, 'utf8')
      payload = JSON.parse(raw)
    } catch {
      throw new Error('invalid_otp_stdin')
    }
    if (!payload || typeof payload.otp !== 'string' || !payload.otp) {
      throw new Error('otp_string_required')
    }

    const currentDump = invoke('dump', serialArgs)
    checkUnsafeSurfaces(currentDump.elements)

    invoke('type-stdin', serialArgs, payload.otp)

    return {
      ok: true,
      action: 'verify-otp',
      serial: device.serial,
      package: DILMIL_PACKAGE,
      status: 'otp_submitted',
    }
  }

  if (options.command === 'connections' || options.command === 'matches') {
    const dump = invoke('dump', serialArgs)
    const matches = dump.elements
      .filter((el) => el.resourceId && el.resourceId.includes('match_row') || (el.text && el.clickable))
      .map((el) => ({ name: el.text || el.desc || 'Match', bounds: el.bounds }))

    return {
      ok: true,
      action: options.command,
      serial: device.serial,
      package: DILMIL_PACKAGE,
      count: matches.length,
      matches,
    }
  }

  throw new Error(`unhandled_command: ${options.command}`)
}

function invokeAndroid(command, args, stdin = null) {
  const result = spawnSync(process.execPath, [androidCli, command, ...args], {
    encoding: 'utf8',
    input: stdin !== null ? stdin : undefined,
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

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    process.stdout.write(`${JSON.stringify(execute(parseOptions(process.argv.slice(2)), invokeAndroid))}\n`)
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ ok: false, error: error.message, usage: standardAdapter.usage() })}\n`)
    process.exitCode = 1
  }
}
