import { useEffect, useRef, useState } from 'react'
import { Square, Volume2, VolumeX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useT } from '@/lib/i18n'
import { hasVoice, speak, stopSpeaking } from '@/lib/pillpal'
import { cn } from '@/lib/utils'

export default function SpeakButton({ text, language, label, large = false, className }) {
  const t = useT()
  const [speaking, setSpeaking] = useState(false)
  const [available, setAvailable] = useState(true)
  const speakingRef = useRef(false)
  speakingRef.current = speaking

  useEffect(() => {
    let live = true
    hasVoice(language).then((ok) => live && setAvailable(ok))
    return () => { live = false }
  }, [language])

  // Stop only if this button is the one talking when it leaves the screen.
  useEffect(() => () => speakingRef.current && stopSpeaking(), [])

  async function toggle() {
    if (speaking) {
      stopSpeaking()
      return
    }
    setSpeaking(true)
    const started = await speak(text, language, () => setSpeaking(false))
    if (!started) {
      setSpeaking(false)
      setAvailable(false)
    }
  }

  const size = large ? 'h-12 px-5 text-base' : 'h-9 px-3 text-sm'

  // No voice for this language on this device: say so instead of reading it wrongly.
  if (!available) {
    return (
      <Button variant="secondary" disabled className={cn('rounded-full whitespace-normal', size, className)}>
        <VolumeX className={large ? 'size-5' : 'size-4'} /> {t.noVoice}
      </Button>
    )
  }

  return (
    <Button
      variant="secondary"
      onClick={toggle}
      aria-pressed={speaking}
      className={cn(
        'rounded-full font-semibold',
        size,
        speaking && 'bg-primary text-primary-foreground hover:bg-primary/90',
        className,
      )}
    >
      {speaking ? <Square className="size-4 fill-current" /> : <Volume2 className={large ? 'size-5' : 'size-4'} />}
      {speaking ? t.stop : (label ?? t.readAloud)}
    </Button>
  )
}
