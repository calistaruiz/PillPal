import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Direction } from 'radix-ui'
import { AlertCircle, CalendarClock, FlaskConical, Globe, ListChecks, ShieldCheck, Sparkles } from 'lucide-react'
import { I18nContext, getStrings } from '@/lib/i18n'
import { LANGUAGES, analyze, getHealth, prepareImage } from '@/lib/pillpal'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DotPattern } from '@/components/ui/dot-pattern'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ShimmerButton } from '@/components/ui/shimmer-button'
import LoadingCard from '@/components/LoadingCard'
import PhotoPicker from '@/components/PhotoPicker'
import Results from '@/components/Results'
import { cn } from '@/lib/utils'

const FEATURES = [
  { icon: ListChecks, key: 'featList' },
  { icon: CalendarClock, key: 'featSchedule' },
  { icon: ShieldCheck, key: 'featSafety' },
]

const fade = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.3, ease: 'easeOut' },
}

const LANGUAGE_KEY = 'pillpal-language'

function savedLanguage() {
  try {
    const saved = localStorage.getItem(LANGUAGE_KEY)
    return LANGUAGES.some((l) => l.code === saved) ? saved : 'en'
  } catch {
    return 'en'
  }
}

export default function App() {
  const [language, setLanguage] = useState(savedLanguage)
  const [photos, setPhotos] = useState([]) // [{ file, url }]
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [demoMode, setDemoMode] = useState(false)

  const t = getStrings(language)
  const dir = LANGUAGES.find((l) => l.code === language)?.rtl ? 'rtl' : 'ltr'
  const canSubmit = status !== 'loading' && (photos.length > 0 || demoMode)

  useEffect(() => {
    getHealth().then((h) => setDemoMode(h.demo_mode)).catch(() => {})
  }, [])

  // Keep the page language in sync for screen readers, then remember the choice.
  useEffect(() => {
    document.documentElement.lang = language
    document.documentElement.dir = dir
    try {
      localStorage.setItem(LANGUAGE_KEY, language)
    } catch {
      // Storage can be unavailable (private browsing); the choice just isn't remembered.
    }
  }, [language, dir])

  async function addFiles(fileList) {
    const prepared = await Promise.all([...fileList].map((file) => prepareImage(file)))
    setPhotos((prev) => [...prev, ...prepared.map((file) => ({ file, url: URL.createObjectURL(file) }))])
  }

  function removePhoto(index) {
    setPhotos((prev) => {
      URL.revokeObjectURL(prev[index].url)
      return prev.filter((_, i) => i !== index)
    })
  }

  async function submit() {
    setStatus('loading')
    setError('')
    try {
      setResult(await analyze(photos.map((p) => p.file), language))
      setStatus('done')
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e) {
      setError(e.message)
      setStatus('error')
    }
  }

  function startOver() {
    photos.forEach((p) => URL.revokeObjectURL(p.url))
    setPhotos([])
    setResult(null)
    setStatus('idle')
  }

  return (
    <I18nContext.Provider value={t}>
      <Direction.DirectionProvider dir={dir}>
        <div dir={dir} className="relative min-h-screen overflow-x-hidden">
          <DotPattern
            width={22}
            height={22}
            className="h-[480px] text-primary/25 [mask-image:radial-gradient(ellipse_at_top,white_20%,transparent_70%)]"
          />

          <div className="relative mx-auto max-w-2xl px-4 pb-20">
            <header className="flex items-center justify-between gap-4 py-5">
              <button onClick={startOver} className="flex items-center gap-3 rounded-xl text-start">
                <img src="/icon.svg" alt="" className="size-11 drop-shadow-sm" />
                <span>
                  <span className="block text-2xl font-bold tracking-tight text-primary">PillPal</span>
                  <span className="hidden text-sm text-muted-foreground sm:block">{t.tagline}</span>
                </span>
              </button>

              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger aria-label={t.language} className="h-11 gap-2 rounded-xl bg-card px-3 text-base shadow-sm">
                  <Globe className="size-4 text-primary" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent position="popper" align="end">
                  {LANGUAGES.map((l) => (
                    <SelectItem key={l.code} value={l.code} lang={l.code} className="py-2 text-base">
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </header>

            {demoMode && (
              <div className="mb-5 flex items-start gap-2 rounded-xl border border-dashed border-primary/30 bg-card/70 px-3 py-2 text-sm text-muted-foreground backdrop-blur">
                <FlaskConical className="mt-0.5 size-4 shrink-0 text-primary" />
                <p>
                  <span className="font-semibold text-foreground">{t.demoTitle}</span> {t.demoBody}
                </p>
              </div>
            )}

            <AnimatePresence mode="wait">
              {status === 'done' && result ? (
                <motion.div key="results" {...fade}>
                  <Results result={result} onStartOver={startOver} />
                </motion.div>
              ) : status === 'loading' ? (
                <motion.div key="loading" {...fade}>
                  <LoadingCard />
                </motion.div>
              ) : (
                <motion.main key="form" {...fade} className="space-y-6">
                  <section className="pt-4 pb-2 text-center">
                    <h1 className="text-balance text-3xl font-bold tracking-tight sm:text-4xl">
                      {t.heroA} <span className="text-primary">{t.heroB}</span>
                    </h1>
                    <p className="mx-auto mt-3 max-w-lg text-pretty text-muted-foreground">{t.heroBody}</p>
                    <ul className="mt-5 flex flex-wrap justify-center gap-2">
                      {FEATURES.map(({ icon: Icon, key }) => (
                        <li key={key} className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 text-sm font-medium text-secondary-foreground">
                          <Icon className="size-4" /> {t[key]}
                        </li>
                      ))}
                    </ul>
                  </section>

                  <Card className="rounded-3xl shadow-sm">
                    <CardHeader>
                      <StepTitle n={1}>{t.step1Title}</StepTitle>
                      <CardDescription className="text-base">{t.step1Body}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <PhotoPicker photos={photos} onAdd={addFiles} onRemove={removePhoto} />
                    </CardContent>
                  </Card>

                  <Card className="rounded-3xl shadow-sm">
                    <CardHeader>
                      <StepTitle n={2}>{t.step2Title}</StepTitle>
                      <CardDescription className="text-base">{t.step2Body}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <ShimmerButton
                        onClick={submit}
                        disabled={!canSubmit}
                        background="var(--primary)"
                        borderRadius="1.1rem"
                        shimmerColor="#a7f3d0"
                        className={cn('h-16 w-full gap-2 text-lg font-semibold', !canSubmit && 'cursor-not-allowed opacity-45')}
                      >
                        <Sparkles className="size-5" /> {t.explain}
                      </ShimmerButton>
                      {!canSubmit && (
                        <p className="text-center text-sm text-muted-foreground">{t.addPhotoFirst}</p>
                      )}
                      {status === 'error' && (
                        <Alert variant="destructive" className="border-destructive/30 bg-destructive/5 text-base">
                          <AlertCircle />
                          <AlertTitle>{t.errorTitle}</AlertTitle>
                          <AlertDescription>
                            {t.genericError}
                            {/* Server details stay in English; useful when reporting a problem. */}
                            {error && <span className="mt-1 block text-sm opacity-80">{error}</span>}
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                </motion.main>
              )}
            </AnimatePresence>

            <footer className="mt-10 flex flex-col items-center gap-2 text-center text-sm text-muted-foreground">
              <p className="flex items-center gap-1.5">
                <ShieldCheck className="size-4 text-primary" /> {t.footerSources}
              </p>
              <p>{t.footerNoChanges}</p>
            </footer>
          </div>
        </div>
      </Direction.DirectionProvider>
    </I18nContext.Provider>
  )
}

function StepTitle({ n, children }) {
  return (
    <CardTitle className="flex items-center gap-3 text-xl">
      <span className="flex size-8 items-center justify-center rounded-full bg-primary text-base text-primary-foreground">
        {n}
      </span>
      {children}
    </CardTitle>
  )
}
