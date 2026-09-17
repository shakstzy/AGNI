#!/usr/bin/env node
/**
 * HADES Vision-Driven Screen OCR & VLM Parsing Controller
 * Provides visual element location, text extraction, scene description,
 * and visual state verification using local VLM endpoints (Qwen/vLLM/FreeLLMAPI).
 */

import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { defaultInvokeAndroid } from './coordinator.mjs'

const DEFAULT_VLM_URL = process.env.VLM_ENDPOINT_URL || 'http://127.0.0.1:8000/v1'
const DEFAULT_VLM_MODEL = process.env.VLM_MODEL_NAME || 'qwen3.8-27b-fp8'

export function encodeImageToBase64(filePath) {
  if (!existsSync(filePath)) throw new Error(`file_not_found: ${filePath}`)
  const buffer = readFileSync(filePath)
  return buffer.toString('base64')
}

export async function callVlmApi(prompt, imagePath, options = {}, context = {}) {
  const fetchFn = context.fetch || globalThis.fetch
  const endpoint = options.endpoint || DEFAULT_VLM_URL
  const model = options.model || DEFAULT_VLM_MODEL
  const base64Image = options.imageBase64 || encodeImageToBase64(imagePath)

  const payload = {
    model,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          {
            type: 'image_url',
            image_url: {
              url: `data:image/png;base64,${base64Image}`,
            },
          },
        ],
      },
    ],
    temperature: 0.1,
    max_tokens: 1024,
  }

  const response = await fetchFn(`${endpoint}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(options.apiKey ? { Authorization: `Bearer ${options.apiKey}` } : {}),
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`vlm_request_failed: ${response.status} ${errorText}`)
  }

  const json = await response.json()
  return json.choices?.[0]?.message?.content || ''
}

export async function locateElement(prompt, options = {}, context = {}) {
  let imagePath = options.image
  if (!imagePath) {
    const invoke = context.invokeAndroid || defaultInvokeAndroid
    const serialArgs = options.serial ? ['--serial', options.serial] : []
    const shot = invoke(['screenshot', ...serialArgs])
    imagePath = shot.out
  }

  const systemPrompt = `You are a precise Android UI locator.
Locate the element matching the query: "${prompt}".
Respond with ONLY valid JSON with no markdown wrapping, in this format:
{"found": true, "label": "description", "bounds": [x1, y1, x2, y2], "center": [x, y], "confidence": 0.95}
If not found, respond with:
{"found": false, "reason": "not_visible"}`

  const responseText = await (context.vlmResponse !== undefined
    ? Promise.resolve(context.vlmResponse)
    : callVlmApi(systemPrompt, imagePath, options, context))

  try {
    const cleaned = responseText.trim().replace(/^```json/, '').replace(/```$/, '').trim()
    const parsed = JSON.parse(cleaned)
    return {
      ok: true,
      action: 'locate',
      query: prompt,
      image: imagePath,
      ...parsed,
    }
  } catch (err) {
    return {
      ok: false,
      action: 'locate',
      query: prompt,
      image: imagePath,
      rawResponse: responseText,
      error: `failed_to_parse_vlm_output: ${err.message}`,
    }
  }
}

export async function describeScreen(options = {}, context = {}) {
  let imagePath = options.image
  if (!imagePath) {
    const invoke = context.invokeAndroid || defaultInvokeAndroid
    const serialArgs = options.serial ? ['--serial', options.serial] : []
    const shot = invoke(['screenshot', ...serialArgs])
    imagePath = shot.out
  }

  const prompt = options.prompt || 'Provide a concise, factual summary of the visible mobile screen UI, current state, buttons, and text.'
  const text = await (context.vlmResponse !== undefined
    ? Promise.resolve(context.vlmResponse)
    : callVlmApi(prompt, imagePath, options, context))

  return {
    ok: true,
    action: 'describe',
    image: imagePath,
    description: text.trim(),
  }
}

export async function ocrScreen(options = {}, context = {}) {
  let imagePath = options.image
  if (!imagePath) {
    const invoke = context.invokeAndroid || defaultInvokeAndroid
    const serialArgs = options.serial ? ['--serial', options.serial] : []
    const shot = invoke(['screenshot', ...serialArgs])
    imagePath = shot.out
  }

  const prompt = `Perform OCR on this screen. List all visible text blocks with their approximate positions.
Output ONLY valid JSON with format:
{"lines": [{"text": "...", "bounds": [x1, y1, x2, y2]}]}`

  const text = await (context.vlmResponse !== undefined
    ? Promise.resolve(context.vlmResponse)
    : callVlmApi(prompt, imagePath, options, context))

  try {
    const cleaned = text.trim().replace(/^```json/, '').replace(/```$/, '').trim()
    const parsed = JSON.parse(cleaned)
    return {
      ok: true,
      action: 'ocr',
      image: imagePath,
      ...parsed,
    }
  } catch (err) {
    return {
      ok: false,
      action: 'ocr',
      image: imagePath,
      rawResponse: text,
      error: err.message,
    }
  }
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
    } else if (!options.prompt) {
      options.prompt = arg
    }
  }
  return { command, options }
}

async function main() {
  const { command, options } = parseCliArgs(process.argv)
  if (!command) {
    console.error('Usage: vision.mjs <locate|describe|ocr> [--prompt P] [--image PATH] [--serial S]')
    process.exit(1)
  }

  try {
    let result
    switch (command) {
      case 'locate':
        result = await locateElement(options.prompt, options)
        break
      case 'describe':
        result = await describeScreen(options)
        break
      case 'ocr':
        result = await ocrScreen(options)
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

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) {
  main()
}
