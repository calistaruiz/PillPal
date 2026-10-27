import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { Check, Loader2, Pill } from 'lucide-react'
import { BorderBeam } from '@/components/ui/border-beam'
import { Card, CardContent } from '@/components/ui/card'
import { useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

export default function LoadingCard() {
  const t = useT()
  // The real pipeline stages, shown one after another while the request runs.
  const stages = t.stages
  const [stage, setStage] = useState(0)
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    const timer = setInterval(() => setStage((s) => Math.min(s + 1, stages.length - 1)), 2200)
    return () => clearInterval(timer)
  }, [])

  return (
    <Card className="relative mt-6 overflow-hidden rounded-3xl shadow-sm">
      <CardContent className="flex flex-col items-center gap-6 py-10" role="status" aria-live="polite">
        <motion.div
          animate={{ rotate: [0, -12, 12, 0], y: [0, -6, 0] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
          className="flex size-16 items-center justify-center rounded-2xl bg-secondary text-primary"
        >
          <Pill className="size-8" />
        </motion.div>
        <p className="text-xl font-semibold">{t.loadingTitle}</p>
        <ol className="w-full max-w-xs space-y-2">
          {stages.map((label, i) => (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: i <= stage ? 1 : 0.4, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={cn('flex items-center gap-3', i === stage ? 'font-semibold' : 'text-muted-foreground')}
            >
              <span
                className={cn(
                  'flex size-6 shrink-0 items-center justify-center rounded-full',
                  i < stage ? 'bg-primary text-primary-foreground' : 'bg-muted',
                )}
              >
                {i < stage ? <Check className="size-3.5" /> : i === stage ? <Loader2 className="size-3.5 animate-spin text-primary" /> : null}
              </span>
              {label}
            </motion.li>
          ))}
        </ol>
      </CardContent>
      {!reduceMotion && <BorderBeam size={120} duration={5} colorFrom="#14b8a6" colorTo="#5eead4" borderWidth={2} />}
    </Card>
  )
}
