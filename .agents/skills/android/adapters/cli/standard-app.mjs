import { lstatSync } from 'node:fs'
import { isAbsolute, join, relative, resolve, sep } from 'node:path'

const COMMANDS = new Set(['check', 'inspect', 'open', 'screenshot'])
const OPTION_NAMES = new Set(['serial', 'out'])

function requireString(value, name) {
  if (typeof value !== 'string' || !value) throw new Error(`${name}_required`)
  return value
}

function requireSuccess(result, command) {
  if (!result || result.ok !== true) throw new Error(`android_${command}_failed: ${result?.error || 'invalid_response'}`)
  return result
}

export function createStandardAppAdapter({ id, name, packageName, runtimeDirectory }) {
  const app = {
    id: requireString(id, 'id'),
    name: requireString(name, 'name'),
    packageName: requireString(packageName, 'package_name'),
    runtimeDirectory: resolve(requireString(runtimeDirectory, 'runtime_directory')),
  }

  function usage() {
    return `Usage: ${app.id}.mjs <check|inspect|open|screenshot> [--serial <device-id>] [--out <runtime-path>]`
  }

  function parseOptions(argv) {
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

    if (options.command !== 'screenshot' && options.out !== undefined) throw new Error('out_only_supported_for_screenshot')
    return options
  }

  function androidArgs(options, extra = []) {
    return [...(options.serial ? ['--serial', options.serial] : []), ...extra]
  }

  function preflight(options, invoke) {
    const result = requireSuccess(invoke('packages', androidArgs(options, ['--package', app.packageName])), 'packages')
    if (!Array.isArray(result.packages) || !result.packages.includes(app.packageName)) {
      throw new Error(`${app.id}_not_installed`)
    }
    return { serial: result.serial || options.serial, package: app.packageName }
  }

  function inspect(options, invoke, device) {
    const current = requireSuccess(invoke('current', androidArgs(options)), 'current')
    const dump = requireSuccess(invoke('dump', androidArgs(options)), 'dump')
    return {
      ok: true,
      action: 'inspect',
      id: app.id,
      name: app.name,
      serial: device.serial,
      package: device.package,
      focus: current.focus,
      elements: dump.elements,
    }
  }

  function screenshotPath(value) {
    const output = value === undefined
      ? resolve(app.runtimeDirectory, `${app.id}-${Date.now()}.png`)
      : isAbsolute(value)
        ? resolve(value)
        : resolve(app.runtimeDirectory, value)
    const pathFromRuntime = relative(app.runtimeDirectory, output)
    if (!pathFromRuntime || pathFromRuntime.startsWith('..') || isAbsolute(pathFromRuntime)) {
      throw new Error('unsafe_screenshot_path')
    }
    let component = app.runtimeDirectory
    for (const segment of pathFromRuntime.split(sep)) {
      try {
        if (lstatSync(component).isSymbolicLink()) throw new Error('unsafe_screenshot_path')
      } catch (error) {
        if (error.code === 'ENOENT') break
        throw error
      }
      component = join(component, segment)
    }
    try {
      if (lstatSync(component).isSymbolicLink()) throw new Error('unsafe_screenshot_path')
    } catch (error) {
      if (error.code !== 'ENOENT') throw error
    }
    return output
  }

  function execute(options, invoke) {
    const device = preflight(options, invoke)
    const identity = { id: app.id, name: app.name, ...device }
    if (options.command === 'check') return { ok: true, action: 'check', ...identity }
    if (options.command === 'inspect') return inspect(options, invoke, device)
    if (options.command === 'open') {
      requireSuccess(invoke('launch', androidArgs(options, ['--package', app.packageName])), 'launch')
      return { ...inspect(options, invoke, device), action: 'open' }
    }
    const result = requireSuccess(invoke('screenshot', androidArgs(options, ['--out', screenshotPath(options.out)])), 'screenshot')
    return { ok: true, action: 'screenshot', ...identity, out: result.out }
  }

  return Object.freeze({
    id: app.id,
    name: app.name,
    packageName: app.packageName,
    runtimeDirectory: app.runtimeDirectory,
    usage,
    parseOptions,
    execute,
    screenshotPath,
  })
}
