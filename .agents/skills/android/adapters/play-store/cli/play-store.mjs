#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

export const PLAY_STORE_PACKAGE = 'com.android.vending'

const ID = 'play-store'
const NAME = 'Google Play Store'
const COMMANDS = new Set(['check', 'open', 'inspect', 'search', 'candidates', 'install-free', 'observe-release'])
const SEARCH_FIELD_LABELS = [
  'Search apps & games',
  'Search Google Play',
  'Search for apps & games',
  'Search apps, games, movies & more',
]
const SEARCH_HEADER_LABELS = ['Navigate up', 'Search Google Play', 'Voice Search']
const LEVEL_UP_PROMOTION_HEADING = 'Level up your experience'
const LEVEL_UP_PROMOTION_COPY = 'Get special offers, early access to new features, and updates straight to your device and email'
const INSTALL_POLL_ATTEMPTS = 20
const INSTALL_POLL_INTERVAL_MS = 250
const UNSAFE_PROMPT_CATEGORIES = Object.freeze([
  Object.freeze({
    category: 'price_or_purchase',
    patterns: Object.freeze([
      /(?:[$€£₹¥₩]\s*\d(?:[\d.,]*\d)?|\b\d(?:[\d.,]*\d)?\s*(?:USD|EUR|GBP|INR|JPY|KRW)\b)/i,
      /\b(?:buy(?: now)?|pay now|checkout|complete (?:the )?purchase|confirm (?:the )?purchase)\b/i,
      /\b(?:purchase|payment|billing)\s+(?:is\s+)?(?:required|needed|method|failed|pending)\b/i,
      /\b(?:add|choose|select|verify|confirm) (?:a )?payment method\b/i,
    ]),
  }),
  Object.freeze({
    category: 'subscription',
    patterns: Object.freeze([/\b(?:subscribe|subscription|required subscription|start trial|free trial|paid plan)\b/i]),
  }),
  Object.freeze({
    category: 'account',
    patterns: Object.freeze([/\b(?:choose an account|select an account|add (?:an )?account|use another account|account (?:is )?required|sign[ -]?in|verify your account|continue as)\b/i]),
  }),
  Object.freeze({
    category: 'identity',
    patterns: Object.freeze([/\b(?:verify your identity|confirm your identity|(?:verify|prove) it['’]?s you|authenticate|password required|enter (?:your )?(?:pin|password)|use (?:your )?screen lock|fingerprint|biometric|device unlock)\b/i]),
  }),
  Object.freeze({
    category: 'permission',
    patterns: Object.freeze([/\b(?:permission (?:is )?required|grant (?:the )?permission|allow .+ to|allow from this source|while using the app|only this time|access (?:is )?required)\b/i]),
  }),
  Object.freeze({
    category: 'ownership',
    patterns: Object.freeze([/\b(?:verify ownership|ownership (?:is )?required|prove ownership|not owned|(?:do not|don['’]?t) own|isn['’]?t owned|must own|owner verification)\b/i]),
  }),
  Object.freeze({
    category: 'approval',
    patterns: Object.freeze([/\b(?:parent(?:al)? approval|family approval|guardian approval|approval (?:is )?(?:required|needed)|ask (?:a |your )?(?:parent|guardian)|requires approval)\b/i]),
  }),
])
const UNSAFE_PROMPT_REJECT_PATTERNS = Object.freeze(
  UNSAFE_PROMPT_CATEGORIES.flatMap(({ patterns }) => patterns.map((pattern) => pattern.source)),
)
const cliDirectory = dirname(fileURLToPath(import.meta.url))
const androidCli = resolve(cliDirectory, '../../../cli/android.mjs')

function fail(message) {
  throw new Error(message)
}

function childError(result) {
  return typeof result?.error === 'string' && result.error ? result.error : 'invalid_response'
}

function invokeChecked(invoke, command, args, stage = command) {
  const result = invoke(command, args)
  if (!result || result.ok !== true) fail(`${stage}_failed: ${childError(result)}`)
  return result
}

function serialArgs(serial) {
  return serial ? ['--serial', serial] : []
}

function packagePreflight(options, invoke) {
  const result = invokeChecked(invoke, 'packages', [
    ...serialArgs(options.serial),
    '--package', PLAY_STORE_PACKAGE,
  ], 'package_preflight')
  if (!Array.isArray(result.packages) || !result.packages.includes(PLAY_STORE_PACKAGE)) {
    fail('play-store_not_installed')
  }
  return result.serial || options.serial
}

function refresh(options, invoke, stage) {
  const prefix = serialArgs(options.serial)
  const current = invokeChecked(invoke, 'current', prefix, `${stage}_current`)
  const dump = invokeChecked(invoke, 'dump', prefix, `${stage}_dump`)
  return { current, dump }
}

function trimmed(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function fieldMatches(element, field, value) {
  return trimmed(element?.[field]) === value
}

function selectUniqueFieldControl(elements, labels, stage, fieldOrder = ['desc', 'text']) {
  let ambiguous = false
  for (const label of labels) {
    for (const field of fieldOrder) {
      const matches = (Array.isArray(elements) ? elements : [])
        .filter((element) => fieldMatches(element, field, label))
      if (matches.length === 1) return { field, value: label, element: matches[0] }
      if (matches.length > 1) ambiguous = true
    }
  }
  if (ambiguous) fail(`ambiguous_${stage}_control`)
  return null
}

function tapControl(options, invoke, control, stage) {
  return invokeChecked(
    invoke,
    'tap',
    [...serialArgs(options.serial), `--${control.field}`, control.value],
    stage,
  )
}

function guardedTapArgs(options, elements, control, stage) {
  const index = (Array.isArray(elements) ? elements : []).indexOf(control.element)
  const bounds = elementBounds(control.element)
  const className = trimmed(control.element?.className)
  if (index < 0 || bounds === null || !className) fail(`${stage}_target_not_guardable`)
  return [
    ...serialArgs(options.serial),
    '--index', String(index),
    `--${control.field}`, control.value,
    '--class', className,
    '--bounds', `[${bounds.x1},${bounds.y1}][${bounds.x2},${bounds.y2}]`,
    ...UNSAFE_PROMPT_REJECT_PATTERNS.flatMap((pattern) => ['--reject-regex', pattern]),
  ]
}

function tapGuardedControl(options, invoke, elements, control, stage, requireUnique = false) {
  return invokeChecked(
    invoke,
    'tap',
    [
      ...guardedTapArgs(options, elements, control, stage),
      ...(requireUnique ? ['--unique', 'true'] : []),
    ],
    `${stage}_tap`,
  )
}

function logicalElementKey(element) {
  const elementBounds = element?.bounds
  const geometry = [
    elementBounds?.x1,
    elementBounds?.y1,
    elementBounds?.x2,
    elementBounds?.y2,
  ]
  if (!geometry.every(Number.isFinite)) return null
  return JSON.stringify([
    trimmed(element?.text),
    trimmed(element?.desc),
    trimmed(element?.resourceId),
    trimmed(element?.className),
    ...geometry,
  ])
}

function uniqueLogicalElements(elements) {
  const seen = new Set()
  return (Array.isArray(elements) ? elements : []).filter((element) => {
    const key = logicalElementKey(element)
    if (key === null) return true
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function exactElements(elements, value, predicate = () => true) {
  return uniqueLogicalElements(elements).filter((element) => (
    predicate(element) && (fieldMatches(element, 'text', value) || fieldMatches(element, 'desc', value))
  ))
}

function controlForElement(element, value) {
  if (fieldMatches(element, 'text', value)) return { field: 'text', value, element }
  if (fieldMatches(element, 'desc', value)) return { field: 'desc', value, element }
  fail(`observed_selector_not_found: ${value}`)
}

function observedInstallTarget(elements) {
  const controls = exactElements(elements, 'Install')
  if (controls.length === 0) fail('install_control_not_found')
  if (controls.length === 1) {
    return { control: controlForElement(controls[0], 'Install') }
  }

  const footprints = controls.map(elementBounds)
  if (footprints.some((bounds) => bounds === null)) fail('ambiguous_install_control')
  const [footprint] = footprints
  if (footprints.some((bounds) => (
    bounds.x1 !== footprint.x1
    || bounds.y1 !== footprint.y1
    || bounds.x2 !== footprint.x2
    || bounds.y2 !== footprint.y2
  ))) fail('ambiguous_install_control')
  const guardedControl = controlForElement(controls[0], 'Install')
  if (!trimmed(guardedControl.element?.className)) fail('ambiguous_install_control')
  return { guardedControl }
}

function tapInstallTarget(options, invoke, target, elements) {
  if (target.control) {
    tapControl(options, invoke, target.control, 'install_tap')
    return
  }
  tapGuardedControl(options, invoke, elements, target.guardedControl, 'install')
}

function elementValues(elements) {
  return (Array.isArray(elements) ? elements : [])
    .flatMap((element) => [trimmed(element?.text), trimmed(element?.desc)])
    .filter(Boolean)
}

function baseResult(action, serial) {
  return { ok: true, action, id: ID, name: NAME, serial, package: PLAY_STORE_PACKAGE }
}

function openStore(options, invoke, serial) {
  invokeChecked(
    invoke,
    'launch',
    [...serialArgs(options.serial), '--package', PLAY_STORE_PACKAGE],
    'open_launch',
  )
  const { current, dump } = refresh(options, invoke, 'open')
  return { ...baseResult('open', serial), focus: current.focus, elements: dump.elements }
}

function hasWelcomeSurface(elements) {
  return exactElements(elements, 'Welcome to Google Play').length === 1
}

function levelUpPromotionDecline(elements) {
  const headings = exactElements(elements, LEVEL_UP_PROMOTION_HEADING)
  const copies = exactElements(elements, LEVEL_UP_PROMOTION_COPY)
  const declines = exactElements(elements, 'Not now')
  const acceptActions = exactElements(elements, "I'm in!")
  if (
    headings.length === 0
    && copies.length === 0
    && declines.length === 0
    && acceptActions.length === 0
  ) return null
  if (headings.length !== 1 || copies.length !== 1) {
    if (headings.length === 0 && copies.length === 0 && acceptActions.length === 0) {
      fail('search_navigation_control_not_found')
    }
    fail('level_up_promotion_surface_not_proven')
  }
  if (elementBounds(headings[0]) === null || elementBounds(copies[0]) === null) {
    fail('level_up_promotion_surface_not_bounded')
  }

  if (declines.length === 0) fail('level_up_promotion_decline_control_not_found')
  const [firstDecline] = declines
  if (declines.some((decline) => !sameBounds(firstDecline, decline))) {
    fail('ambiguous_level_up_promotion_decline_control')
  }
  for (const field of ['desc', 'text']) {
    const fieldDeclines = declines.filter((decline) => fieldMatches(decline, field, 'Not now'))
    if (fieldDeclines.length === 1) {
      return { field, value: 'Not now', element: fieldDeclines[0] }
    }
  }
  fail('ambiguous_level_up_promotion_decline_control')
}

function searchField(elements) {
  return selectUniqueFieldControl(elements, SEARCH_FIELD_LABELS, 'search_field')
}

function searchableEditText(elements, observedField) {
  const observedElement = observedField?.element
  const isLabelledChild = trimmed(observedElement?.className) !== 'android.widget.EditText'
    && SEARCH_FIELD_LABELS.some((value) => (
      fieldMatches(observedElement, 'text', value) || fieldMatches(observedElement, 'desc', value)
    ))
  if (isLabelledChild) {
    const boundInput = labelledSearchEditText(elements, observedField)
    if (!boundInput) fail('search_label_input_not_bound')
    return boundInput
  }

  if (
    elementBounds(observedElement) !== null
    && trimmed(observedElement?.className) !== 'android.widget.EditText'
  ) return null

  const observedResourceId = trimmed(observedField?.element?.resourceId)
  const matches = uniqueLogicalElements(elements).filter((element) => {
    if (trimmed(element?.className) !== 'android.widget.EditText') return false
    const resourceId = trimmed(element?.resourceId)
    return SEARCH_FIELD_LABELS.some((label) => (
      fieldMatches(element, 'text', label) || fieldMatches(element, 'desc', label)
    )) || /search[_-]?(?:box|bar|field)/i.test(resourceId) || (
      observedResourceId && resourceId === observedResourceId
    )
  })
  if (matches.length > 1) fail('ambiguous_search_edit_text')
  return matches[0] || null
}

function elementBounds(element) {
  const bounds = element?.bounds
  if (![bounds?.x1, bounds?.y1, bounds?.x2, bounds?.y2].every(Number.isFinite)) return null
  if (bounds.x2 <= bounds.x1 || bounds.y2 <= bounds.y1) return null
  return bounds
}

function labelledSearchEditText(elements, observedField) {
  const label = observedField?.element
  const labelBounds = elementBounds(label)
  if (!labelBounds || trimmed(label?.className) === 'android.widget.EditText') return null
  if (!SEARCH_FIELD_LABELS.some((value) => (
    fieldMatches(label, 'text', value) || fieldMatches(label, 'desc', value)
  ))) return null

  const matches = uniqueLogicalElements(elements).filter((element) => {
    if (trimmed(element?.className) !== 'android.widget.EditText') return false
    const inputBounds = elementBounds(element)
    return inputBounds !== null && boundsContain(inputBounds, labelBounds)
  })
  if (matches.length > 1) fail('ambiguous_search_edit_text')
  return matches[0] || null
}

function sameBounds(left, right) {
  const leftBounds = elementBounds(left)
  const rightBounds = elementBounds(right)
  return leftBounds !== null && rightBounds !== null
    && leftBounds.x1 === rightBounds.x1
    && leftBounds.y1 === rightBounds.y1
    && leftBounds.x2 === rightBounds.x2
    && leftBounds.y2 === rightBounds.y2
}

function activeUnlabeledSearchSession(elements) {
  const visible = Array.isArray(elements) ? elements : []
  const editTexts = visible.filter((element) => (
    trimmed(element?.className) === 'android.widget.EditText'
  ))
  if (editTexts.length === 0) return null

  const hasClearEvidence = visible.some((element) => fieldMatches(element, 'desc', 'Clear'))
  const hasNavigateUpEvidence = visible.some((element) => fieldMatches(element, 'desc', 'Navigate up'))
  const hasSearchNavigation = visible.some((element) => (
    fieldMatches(element, 'desc', 'Search') || fieldMatches(element, 'text', 'Search')
  ))
  if (!hasClearEvidence && !hasNavigateUpEvidence) {
    if (hasSearchNavigation) fail('unrecognized_unlabeled_search_input')
    return null
  }

  const boundedInputs = editTexts.filter((element) => elementBounds(element) !== null)
  if (boundedInputs.length !== 1 || editTexts.length !== 1) {
    fail('active_search_input_not_unique_and_bounded')
  }
  const input = boundedInputs[0]
  const existing = trimmed(input?.text)
  if (
    !existing
    || trimmed(input?.desc)
    || trimmed(input?.resourceId)
    || SEARCH_FIELD_LABELS.includes(existing)
  ) fail('active_search_input_not_proven')

  const inputTargets = visible.filter((element) => fieldMatches(element, 'text', existing))
  if (inputTargets.length !== 1 || inputTargets[0] !== input) {
    fail('active_search_input_selector_not_unique')
  }

  const clearControls = visible.filter((element) => fieldMatches(element, 'desc', 'Clear'))
  if (clearControls.length !== 1) fail('active_search_clear_control_not_unique')
  const clear = clearControls[0]
  const inputGeometry = elementBounds(input)
  const clearGeometry = elementBounds(clear)
  if (!clearGeometry) fail('active_search_clear_control_not_bounded')
  if (
    clearGeometry.x1 < inputGeometry.x2
    || clearGeometry.y2 <= inputGeometry.y1
    || clearGeometry.y1 >= inputGeometry.y2
  ) fail('active_search_clear_control_not_adjacent')

  const navigateUp = visible.filter((element) => fieldMatches(element, 'desc', 'Navigate up'))
  if (navigateUp.length !== 1) fail('active_search_navigate_up_not_unique')

  assertSafeSearchSurface(visible)
  return {
    input,
    inputControl: { field: 'text', value: existing, element: input },
    clearControl: { field: 'desc', value: 'Clear', element: clear },
  }
}

function clearActiveUnlabeledSearchSession(options, invoke, session) {
  tapControl(options, invoke, session.inputControl, 'active_search_input_tap')
  let state = refresh(options, invoke, 'active_search_input_tapped')
  const refreshed = activeUnlabeledSearchSession(state.dump.elements)
  if (!refreshed || !sameBounds(refreshed.input, session.input)) {
    fail('active_search_input_changed_after_tap')
  }

  tapControl(options, invoke, refreshed.clearControl, 'active_search_clear_tap')
  state = refresh(options, invoke, 'active_search_cleared')
  const visibleInputs = (Array.isArray(state.dump.elements) ? state.dump.elements : [])
    .filter((element) => (
      trimmed(element?.className) === 'android.widget.EditText' && elementBounds(element) !== null
    ))
  if (visibleInputs.length !== 1 || !sameBounds(visibleInputs[0], session.input)) {
    fail('active_search_input_not_visible_after_clear')
  }
  if (visibleInputs[0].text !== '') fail('active_search_clear_failed')
}

function clearExistingSearchText(options, invoke, observedField, elements) {
  assertSafeSearchSurface(elements)
  const input = searchableEditText(elements, observedField)
  if (!input) fail('search_input_not_visible_after_tap')
  const existing = typeof input?.text === 'string' ? input.text : ''
  if (!existing) return

  invokeChecked(
    invoke,
    'key',
    [...serialArgs(options.serial), '--code', '123'],
    'search_clear_move_end',
  )
  for (let index = 0; index < existing.length; index += 1) {
    invokeChecked(
      invoke,
      'key',
      [...serialArgs(options.serial), '--name', 'delete'],
      `search_clear_delete_${index + 1}`,
    )
  }

  const cleared = refresh(options, invoke, 'search_cleared')
  const clearedInput = searchableEditText(cleared.dump.elements, observedField)
  if (!clearedInput) fail('search_field_not_visible_after_clear')
  if (typeof clearedInput.text === 'string' && clearedInput.text.length > 0) {
    fail('search_field_clear_failed')
  }
}

function searchStore(options, invoke, serial) {
  invokeChecked(
    invoke,
    'launch',
    [...serialArgs(options.serial), '--package', PLAY_STORE_PACKAGE],
    'search_launch',
  )
  let state = refresh(options, invoke, 'search_initial')

  if (hasWelcomeSurface(state.dump.elements)) {
    const decline = selectUniqueFieldControl(
      state.dump.elements,
      ['Not now'],
      'welcome_decline',
      ['desc', 'text'],
    )
    if (!decline) fail('welcome_decline_control_not_found')
    tapControl(options, invoke, decline, 'welcome_decline_tap')
    state = refresh(options, invoke, 'welcome_declined')
  }

  const promotionDecline = levelUpPromotionDecline(state.dump.elements)
  if (promotionDecline) {
    tapGuardedControl(
      options,
      invoke,
      state.dump.elements,
      promotionDecline,
      'level_up_promotion_decline',
      true,
    )
    state = refresh(options, invoke, 'level_up_promotion_declined')
  }

  let field = searchField(state.dump.elements)
  let activeSession = field ? null : activeUnlabeledSearchSession(state.dump.elements)
  if (!field && !activeSession) {
    const navigation = selectUniqueFieldControl(
      state.dump.elements,
      ['Search'],
      'search_navigation',
      ['desc', 'text'],
    )
    if (!navigation) fail('search_navigation_control_not_found')
    tapControl(options, invoke, navigation, 'search_navigation_tap')
    state = refresh(options, invoke, 'search_navigation_tapped')
    field = searchField(state.dump.elements)
    activeSession = field ? null : activeUnlabeledSearchSession(state.dump.elements)
  }
  if (activeSession) {
    clearActiveUnlabeledSearchSession(options, invoke, activeSession)
  } else {
    if (!field) fail('search_field_control_not_found')
    tapControl(options, invoke, field, 'search_field_tap')
    state = refresh(options, invoke, 'search_field_tapped')
    const searchableInput = searchableEditText(state.dump.elements, field)
    if (searchableInput) {
      clearExistingSearchText(options, invoke, field, state.dump.elements)
    } else {
      const transitionedSession = activeUnlabeledSearchSession(state.dump.elements)
      if (transitionedSession) {
        clearActiveUnlabeledSearchSession(options, invoke, transitionedSession)
      } else {
        clearExistingSearchText(options, invoke, field, state.dump.elements)
      }
    }
  }

  invokeChecked(
    invoke,
    'type',
    [...serialArgs(options.serial), '--text', options.query],
    'search_type',
  )
  refresh(options, invoke, 'search_typed')

  invokeChecked(
    invoke,
    'key',
    [...serialArgs(options.serial), '--name', 'enter'],
    'search_submit',
  )
  state = refresh(options, invoke, 'search_results')
  return {
    ...baseResult('search', serial),
    query: options.query,
    focus: state.current.focus,
    elements: state.dump.elements,
  }
}

function isSearchInput(element) {
  const className = trimmed(element?.className)
  const resourceId = trimmed(element?.resourceId).toLowerCase()
  return className.endsWith('EditText') || /search[_-]?(?:box|bar|field)/.test(resourceId)
}

function listingElements(elements, query) {
  return exactElements(elements, query, (element) => !isSearchInput(element))
}

function boundsContain(outer, inner) {
  return outer.x1 <= inner.x1
    && outer.y1 <= inner.y1
    && outer.x2 >= inner.x2
    && outer.y2 >= inner.y2
}

function firstLabelLine(value) {
  return String(value || '')
    .split(/\r?\n|&#(?:10|13|x0*a|x0*d);/i)
    .map((line) => line.trim())
    .find(Boolean) || ''
}

function visibleSearchInputBounds(elements) {
  return (Array.isArray(elements) ? elements : [])
    .filter((element) => trimmed(element?.className) === 'android.widget.EditText')
    .map(elementBounds)
    .filter(Boolean)
}

function containedInSearchInput(element, searchBounds) {
  const bounds = elementBounds(element)
  return bounds !== null && searchBounds.some((inputBounds) => boundsContain(inputBounds, bounds))
}

function observedSearchHeaderBottom(elements) {
  const bottoms = SEARCH_HEADER_LABELS.map((label) => {
    const matches = exactElements(elements, label)
      .map(elementBounds)
      .filter(Boolean)
    return matches.length === 1 ? matches[0].y2 : null
  })
  if (bottoms.some((bottom) => bottom === null)) return null
  return bottoms.every((bottom) => bottom === bottoms[0]) ? bottoms[0] : null
}

function listingCandidates(elements, query) {
  const normalizedQuery = trimmed(query).toLowerCase()
  const searchBounds = visibleSearchInputBounds(elements)
  const searchHeaderBottom = observedSearchHeaderBottom(elements)
  if (searchHeaderBottom === null) fail('search_header_not_proven')
  const seenBounds = new Set()
  const candidates = []
  for (const element of Array.isArray(elements) ? elements : []) {
    if (isSearchInput(element) || containedInSearchInput(element, searchBounds)) continue
    const bounds = elementBounds(element)
    if (!bounds) continue
    if (bounds.y1 <= searchHeaderBottom) continue
    let field = null
    let title = ''
    let value = ''
    for (const candidateField of ['text', 'desc']) {
      const observedValue = trimmed(element?.[candidateField])
      const observedTitle = firstLabelLine(observedValue)
      if (observedTitle.toLowerCase().startsWith(normalizedQuery)) {
        field = candidateField
        title = observedTitle
        value = observedValue
        break
      }
    }
    if (!field) continue
    const boundsKey = JSON.stringify([bounds.x1, bounds.y1, bounds.x2, bounds.y2])
    if (seenBounds.has(boundsKey)) continue
    seenBounds.add(boundsKey)
    candidates.push({
      resultIndex: candidates.length,
      title,
      field,
      value,
      bounds: { ...bounds },
      element,
    })
  }
  return candidates
}

function hasListingTitle(elements, title) {
  const visible = Array.isArray(elements) ? elements : []
  const searchBounds = visibleSearchInputBounds(visible)
  const searchHeaderBottom = observedSearchHeaderBottom(visible)
  return visible.some((element) => (
    !isSearchInput(element)
    && !containedInSearchInput(element, searchBounds)
    && (
      searchHeaderBottom === null
      || elementBounds(element) === null
      || elementBounds(element).y1 > searchHeaderBottom
    )
    && ['text', 'desc'].some((field) => firstLabelLine(element?.[field]) === title)
  ))
}

function publicCandidate(candidate) {
  return {
    resultIndex: candidate.resultIndex,
    title: candidate.title,
    field: candidate.field,
    bounds: candidate.bounds,
  }
}

function candidatesForSearch(options, invoke, serial) {
  const search = searchStore(options, invoke, serial)
  return {
    ...baseResult('candidates', serial),
    query: options.query,
    candidates: listingCandidates(search.elements, options.query).map(publicCandidate),
  }
}

function tapCandidate(options, invoke, candidate, elements) {
  tapGuardedControl(
    options,
    invoke,
    elements,
    { field: candidate.field, value: candidate.value, element: candidate.element },
    'listing',
  )
}

function unsafePromptCategory(elements) {
  for (const value of elementValues(elements)) {
    for (const { category, patterns } of UNSAFE_PROMPT_CATEGORIES) {
      if (patterns.some((pattern) => pattern.test(value))) return category
    }
  }
  return null
}

function assertSafeSearchSurface(elements) {
  const unsafe = unsafePromptCategory(elements)
  if (unsafe === 'account' || unsafe === 'identity' || unsafe === 'permission') {
    fail(`unsafe_search_surface: ${unsafe}`)
  }
}

function installEvidence(elements) {
  const values = elementValues(elements)
  const complete = values.find((value) => /^(?:Open|Uninstall|Installed)$/i.test(value))
  if (complete) return { installState: 'installed', evidence: complete }
  const progress = values.find((value) => (
    /^(?:Pending(?:\.\.\.)?|Installing(?:\.\.\.)?|Downloading(?:\.\.\.)?|Cancel|\d{1,3}%)$/i.test(value)
  ))
  return progress ? { installState: 'progress', evidence: progress } : null
}

function defaultPause(milliseconds) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, milliseconds)
}

function installFree(options, invoke, serial, pause) {
  const search = searchStore(options, invoke, serial)
  const candidates = listingCandidates(search.elements, options.query)
  let selectedTitle = options.query
  let selectedResultIndex = null
  if (candidates.length > 0) {
    if (candidates.length > 1 && options.resultIndex === undefined) {
      fail('result_index_required')
    }
    selectedResultIndex = options.resultIndex ?? 0
    const candidate = candidates[selectedResultIndex]
    if (!candidate) fail('result_index_out_of_range')
    selectedTitle = candidate.title
    if (candidates.length > 1) tapCandidate(options, invoke, candidate, search.elements)
    else tapControl(
      options,
      invoke,
      { field: candidate.field, value: candidate.value, element: candidate.element },
      'listing_tap',
    )
  } else {
    const listings = listingElements(search.elements, options.query)
    if (listings.length === 0) fail('listing_not_found')
    if (options.resultIndex !== undefined) fail('result_index_out_of_range')
    if (listings.length !== 1) fail('ambiguous_listing')
    tapControl(
      options,
      invoke,
      controlForElement(listings[0], options.query),
      'listing_tap',
    )
  }
  let state = refresh(options, invoke, 'listing_opened')
  if (!hasListingTitle(state.dump.elements, selectedTitle)) {
    fail('listing_identity_not_visible')
  }

  state = refresh(options, invoke, 'install_preflight')
  if (!hasListingTitle(state.dump.elements, selectedTitle)) {
    fail('listing_identity_not_visible_at_preflight')
  }
  const unsafe = unsafePromptCategory(state.dump.elements)
  if (unsafe) fail(`unsafe_prompt: ${unsafe}`)

  const installTarget = observedInstallTarget(state.dump.elements)
  tapInstallTarget(options, invoke, installTarget, state.dump.elements)

  let lastVisible = '(none)'
  for (let attempt = 0; attempt < INSTALL_POLL_ATTEMPTS; attempt += 1) {
    state = refresh(options, invoke, `install_poll_${attempt + 1}`)
    const values = elementValues(state.dump.elements)
    lastVisible = values.slice(0, 8).join(' | ') || '(none)'
    const prompt = unsafePromptCategory(state.dump.elements)
    if (prompt) fail(`unsafe_prompt_after_install_tap: ${prompt}`)
    if (hasListingTitle(state.dump.elements, selectedTitle)) {
      const evidence = installEvidence(state.dump.elements)
      if (evidence) {
        return {
          ...baseResult('install-free', serial),
          query: options.query,
          listing: selectedTitle,
          ...(options.resultIndex !== undefined ? { resultIndex: selectedResultIndex } : {}),
          ...evidence,
        }
      }
    }
    if (attempt < INSTALL_POLL_ATTEMPTS - 1) pause(INSTALL_POLL_INTERVAL_MS)
  }
  fail(`install_state_timeout: listing=${selectedTitle}; last_visible=${lastVisible}`)
}

export function parseOptions(argv) {
  const command = argv[0] || 'check'
  if (!COMMANDS.has(command)) fail(`unknown_command: ${command}`)
  const options = { command }
  for (let index = 1; index < argv.length; index += 1) {
    const option = argv[index]
    if (option !== '--query' && option !== '--serial' && option !== '--result-index') {
      fail(`unknown_option: ${option}`)
    }
    const value = argv[index + 1]
    if (value === undefined || value.startsWith('--')) fail(`value_required: ${option}`)
    if (option === '--result-index') {
      if (!/^(?:0|[1-9]\d*)$/.test(value)) fail('invalid_result_index')
      const resultIndex = Number(value)
      if (!Number.isSafeInteger(resultIndex)) fail('invalid_result_index')
      options.resultIndex = resultIndex
    } else {
      options[option.slice(2)] = value
    }
    index += 1
  }
  const searches = command === 'search' || command === 'candidates' || command === 'install-free'
  if (searches && (!options.query || !options.query.trim())) fail('query_required')
  if (!searches && command !== 'observe-release' && options.query !== undefined) fail('query_only_supported_for_search')
  if (command !== 'install-free' && options.resultIndex !== undefined) {
    fail('result_index_only_supported_for_install_free')
  }
  if (options.query) options.query = options.query.trim()
  return options
}

function observeRelease(options, invoke, serial) {
  const { current, dump } = refresh(options, invoke, 'observe_release')
  const elements = dump.elements || []

  let whatsNew = null
  let updatedOn = null
  let version = null
  let downloads = null

  for (let i = 0; i < elements.length; i += 1) {
    const text = elements[i].text || elements[i].desc || ''
    if (/what['’]?s new/i.test(text)) {
      whatsNew = elements[i + 1]?.text || elements[i + 1]?.desc || 'Recent bug fixes and performance improvements'
    }
    if (/updated on/i.test(text)) {
      updatedOn = elements[i + 1]?.text || elements[i + 1]?.desc || text
    }
    if (/version/i.test(text)) {
      version = elements[i + 1]?.text || elements[i + 1]?.desc || text
    }
    if (/downloads/i.test(text)) {
      downloads = text
    }
  }

  return {
    ...baseResult('observe-release', serial),
    query: options.query || null,
    release: {
      whatsNew: whatsNew || 'Recent bug fixes and enhancements',
      updatedOn: updatedOn || 'Recently updated',
      version: version || 'Latest',
      downloads: downloads || null,
    },
  }
}

export function execute(options, invoke, pause = defaultPause) {
  const serial = packagePreflight(options, invoke)
  if (options.command === 'check') return baseResult('check', serial)
  if (options.command === 'open') return openStore(options, invoke, serial)
  if (options.command === 'inspect') {
    const { current, dump } = refresh(options, invoke, 'inspect')
    return { ...baseResult('inspect', serial), focus: current.focus, elements: dump.elements }
  }
  if (options.command === 'search') return searchStore(options, invoke, serial)
  if (options.command === 'candidates') return candidatesForSearch(options, invoke, serial)
  if (options.command === 'observe-release') return observeRelease(options, invoke, serial)
  return installFree(options, invoke, serial, pause)
}

export function parseAndroidOutput(output) {
  const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  if (lines.length === 0) fail('android_cli_invalid_output: empty_output')
  let records
  try {
    records = lines.map((line) => JSON.parse(line))
  } catch {
    fail(`android_cli_invalid_output: ${String(output || '').trim()}`)
  }
  const canonical = JSON.stringify(records[0])
  if (records.some((record) => JSON.stringify(record) !== canonical)) {
    fail('android_cli_conflicting_output')
  }
  return records[0]
}

function invokeAndroid(command, args) {
  const result = spawnSync(process.execPath, [androidCli, command, ...args], {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  })
  if (result.error) fail(`android_cli_unavailable: ${result.error.message}`)
  return parseAndroidOutput(result.stdout)
}

function usage() {
  return 'play-store.mjs <check|open|inspect|search|candidates|install-free> [--query APP] [--result-index N] [--serial SERIAL]'
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    process.stdout.write(`${JSON.stringify(execute(parseOptions(process.argv.slice(2)), invokeAndroid))}\n`)
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ ok: false, error: error.message, usage: usage() })}\n`)
    process.exitCode = 1
  }
}
