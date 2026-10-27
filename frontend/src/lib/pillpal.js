// Backend URL: empty in development (Vite proxies /api), set VITE_API_URL in production.
const API_URL = import.meta.env.VITE_API_URL ?? ''

export const LANGUAGES = [
  { code: 'en', name: 'English', speech: 'en-US' },
  { code: 'es', name: 'Español', speech: 'es-ES' },
  { code: 'zh', name: '中文', speech: 'zh-CN' },
  { code: 'vi', name: 'Tiếng Việt', speech: 'vi-VN' },
  { code: 'tl', name: 'Tagalog', speech: 'fil-PH' },
  { code: 'ko', name: '한국어', speech: 'ko-KR' },
  { code: 'ru', name: 'Русский', speech: 'ru-RU' },
  { code: 'ar', name: 'العربية', speech: 'ar-SA', rtl: true },
  { code: 'hi', name: 'हिन्दी', speech: 'hi-IN' },
  { code: 'fr', name: 'Français', speech: 'fr-FR' },
  { code: 'ht', name: 'Kreyòl ayisyen', speech: 'ht-HT' },
  { code: 'pt', name: 'Português', speech: 'pt-BR' },
]

export async function getHealth() {
  const response = await fetch(`${API_URL}/api/health`)
  if (!response.ok) throw new Error('Server is not responding.')
  return response.json()
}

export async function analyze(files, language) {
  const form = new FormData()
  form.append('language', language)
  for (const file of files) form.append('files', file)

  const response = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body: form })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'Something went wrong. Please try again.')
  return body
}

// Shrink phone photos (often 5-10 MB) to a JPEG under the 5 MB API limit.
export async function prepareImage(file, maxSide = 1800) {
  let bitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    return file // browser can't decode it (e.g. HEIC on some browsers); let the server decide
  }
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(bitmap.width * scale)
  canvas.height = Math.round(bitmap.height * scale)
  canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85))
  return new File([blob], file.name.replace(/\.\w+$/, '') + '.jpg', { type: 'image/jpeg' })
}

// ---------- Read-aloud with the browser's built-in voices (free, no API key) ----------

// Voice language codes to accept per app language. Filipino voices are tagged fil- or tl-.
const VOICE_PREFIXES = { tl: ['fil', 'tl'] }

let voicesReady = null

// Browsers load their voice list a moment after the page opens; wait for it.
function loadVoices() {
  const synth = window.speechSynthesis
  if (!synth) return Promise.resolve([])
  if (!voicesReady) {
    voicesReady = new Promise((resolve) => {
      const done = () => {
        const voices = synth.getVoices()
        if (!voices.length) voicesReady = null // try again next time
        resolve(voices)
      }
      if (synth.getVoices().length) return done()
      synth.addEventListener('voiceschanged', done, { once: true })
      setTimeout(done, 2000) // some browsers never fire voiceschanged
    })
  }
  return voicesReady
}

const normalize = (lang) => lang.toLowerCase().replace('_', '-')

// Prefer natural-sounding voices, and the exact regional variant (zh-CN Mandarin, not zh-HK Cantonese).
function voiceScore(voice, region) {
  const name = voice.name.toLowerCase()
  let score = 0
  if (normalize(voice.lang) === region) score += 5
  if (name.includes('natural')) score += 4
  if (name.includes('online') || name.includes('neural')) score += 3
  if (name.includes('google')) score += 2
  return score
}

function pickVoice(voices, languageCode) {
  const region = normalize(LANGUAGES.find((l) => l.code === languageCode)?.speech ?? 'en-US')
  const prefixes = VOICE_PREFIXES[languageCode] ?? [languageCode]
  const matches = voices.filter((v) => prefixes.includes(normalize(v.lang).split('-')[0]))
  return matches.sort((a, b) => voiceScore(b, region) - voiceScore(a, region))[0] ?? null
}

// The voice read-aloud will use for a language, or null. Handy for debugging in the console.
export async function voiceFor(languageCode) {
  return pickVoice(await loadVoices(), languageCode)
}

export async function hasVoice(languageCode) {
  return (await voiceFor(languageCode)) !== null
}

// Chrome's online voices stop silently after ~15 seconds of continuous speech,
// so long text is spoken a sentence or two at a time.
function splitForSpeech(text, maxLength = 200) {
  const sentences = text.match(/[^.!?。！？।]+[.!?。！？।]*\s*/g) ?? [text]
  const chunks = []
  for (const sentence of sentences) {
    const last = chunks.length - 1
    if (last >= 0 && chunks[last].length + sentence.length <= maxLength) chunks[last] += sentence
    else chunks.push(sentence)
  }
  return chunks.map((c) => c.trim()).filter(Boolean)
}

let session = 0
let finishCurrent = null

function finish() {
  const callback = finishCurrent
  finishCurrent = null
  callback?.()
}

// Returns false when this device has no voice for the language.
export async function speak(text, languageCode, onEnd) {
  const synth = window.speechSynthesis
  if (!synth) return false
  const voice = pickVoice(await loadVoices(), languageCode)
  if (!voice) return false

  stopSpeaking() // also resets any other read-aloud button
  const id = session
  finishCurrent = onEnd
  const chunks = splitForSpeech(text)
  chunks.forEach((chunk, i) => {
    const utterance = new SpeechSynthesisUtterance(chunk)
    utterance.voice = voice
    utterance.lang = voice.lang
    utterance.rate = 0.9 // a little slower, easier for older listeners
    if (i === chunks.length - 1) utterance.onend = () => id === session && finish()
    utterance.onerror = () => {
      if (id !== session) return
      session++
      synth.cancel()
      finish()
    }
    synth.speak(utterance)
  })
  return true
}

export function stopSpeaking() {
  session++
  window.speechSynthesis?.cancel()
  finish()
}
