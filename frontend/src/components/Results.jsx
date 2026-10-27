import {
  AlertTriangle, Clock, CopyX, ExternalLink, Hand, Info, Moon, Pill, RotateCcw, ScanSearch,
  SearchX, ShieldAlert, ShieldCheck, Sun, Sunrise, Sunset, Target, UtensilsCrossed,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { BlurFade } from '@/components/ui/blur-fade'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import SpeakButton from '@/components/SpeakButton'
import { useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

const FINDINGS = {
  interaction: { icon: AlertTriangle, tone: 'danger' },
  duplicate: { icon: CopyX, tone: 'danger' },
  low_confidence: { icon: ScanSearch, tone: 'warn' },
  not_found: { icon: SearchX, tone: 'warn' },
}

const TONES = {
  danger: 'border-destructive/30 bg-destructive/5 [&_.finding-title]:text-destructive [&_.finding-icon]:bg-destructive/10 [&_.finding-icon]:text-destructive',
  warn: 'border-warning-foreground/25 bg-warning [&_.finding-title]:text-warning-foreground [&_.finding-icon]:bg-warning-foreground/10 [&_.finding-icon]:text-warning-foreground',
}

const SLOT_ICONS = {
  before_breakfast: UtensilsCrossed, morning: Sunrise,
  before_lunch: UtensilsCrossed, midday: Sun,
  before_dinner: UtensilsCrossed, evening: Sunset,
  bedtime: Moon, as_needed: Hand,
}

// Schedule notes arrive as codes; the translated text is in result.ui.
const noteText = (item, ui) => item.notes.map((code) => ui[code]).join(' · ')

// One color per medicine, used in the schedule and on its card, so people can match them at a glance.
const MED_COLORS = ['#0d9488', '#7c3aed', '#db2777', '#ea580c', '#2563eb', '#65a30d', '#ca8a04', '#0891b2']

export default function Results({ result, onStartOver }) {
  const t = useT()
  const { ui, language } = result
  const byId = Object.fromEntries(result.medications.map((m) => [m.id, m]))
  const colorOf = (id) => MED_COLORS[result.medications.findIndex((m) => m.id === id) % MED_COLORS.length]
  const urgent = result.findings.filter((f) => FINDINGS[f.kind].tone === 'danger').length

  const fullText = [
    ...result.findings.map((f) => `${f.title}. ${f.detail}`),
    ...result.schedule.map((s) => `${ui[s.slot]}: ${s.items.map((i) => `${i.name} ${i.dose ?? ''} ${noteText(i, ui)}`).join(', ')}.`),
    ...result.explanations.map((e) => `${e.display_name}. ${e.purpose} ${e.how_to_take}`),
    ui.disclaimer,
  ].join(' ')

  return (
    <main className="space-y-8 pt-2">
      <BlurFade>
        <Card className="rounded-3xl shadow-sm">
          <CardContent className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">{t.planTitle}</h1>
                <p className="text-muted-foreground">{t.planSub}</p>
              </div>
              <Button variant="ghost" onClick={onStartOver} className="h-10 rounded-full text-base text-primary">
                <RotateCcw /> {t.startOver}
              </Button>
            </div>
            <dl className="grid grid-cols-3 gap-3 text-center">
              <Stat value={result.medications.length} label={t.statMeds} />
              <Stat value={result.schedule.filter((s) => s.slot !== 'as_needed').length} label={t.statTimes} />
              <Stat value={result.findings.length} label={t.statReview} alert={urgent > 0} />
            </dl>
            <SpeakButton text={fullText} language={language} label={t.readAll} large className="w-full" />
          </CardContent>
        </Card>
      </BlurFade>

      <BlurFade delay={0.05}>
        <div className="flex gap-3 rounded-2xl bg-secondary px-4 py-3 text-secondary-foreground">
          <Info className="mt-0.5 size-5 shrink-0" />
          <p>{ui.disclaimer}</p>
        </div>
      </BlurFade>

      <Section icon={result.findings.length ? ShieldAlert : ShieldCheck} title={t.safetyChecks} delay={0.1}>
        {result.findings.length === 0 ? (
          <Card className="rounded-2xl">
            <CardContent className="flex items-start gap-3">
              <ShieldCheck className="size-6 shrink-0 text-primary" />
              <p>{t.noFindings}</p>
            </CardContent>
          </Card>
        ) : (
          <ul className="space-y-3">
            {result.findings.map((f, i) => (
              <BlurFade key={i} delay={0.12 + i * 0.06}>
                <Finding finding={f} />
              </BlurFade>
            ))}
          </ul>
        )}
      </Section>

      <Section icon={Clock} title={t.dailySchedule} delay={0.15}>
        <Card className="rounded-3xl shadow-sm">
          <CardContent>
            <ol className="relative space-y-6 before:absolute before:inset-y-4 before:start-5 before:w-0.5 before:bg-border">
              {result.schedule.map((slot) => {
                const Icon = SLOT_ICONS[slot.slot]
                return (
                  <li key={slot.slot} className="relative flex gap-4">
                    <span className="z-10 flex size-10 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground ring-4 ring-card">
                      <Icon className="size-5" />
                    </span>
                    <div className="flex-1 pt-1.5">
                      <p className="flex flex-wrap items-center gap-2 text-lg font-semibold">
                        {ui[slot.slot]}
                        {slot.time && <Badge variant="outline" className="h-6 text-sm">{slot.time}</Badge>}
                      </p>
                      <ul className="mt-2 space-y-2">
                        {slot.items.map((item) => (
                          <li key={item.medication_id} className="flex items-start gap-3 rounded-xl bg-muted/70 px-3 py-2.5">
                            <Pill className="mt-1 size-4 shrink-0" style={{ color: colorOf(item.medication_id) }} />
                            <div>
                              <span className="font-semibold">{item.name}</span>
                              {item.dose && <span className="text-muted-foreground"> · {item.dose}</span>}
                              {item.notes.length > 0 && (
                                <span className="block text-sm text-muted-foreground">{noteText(item, ui)}</span>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </li>
                )
              })}
            </ol>
          </CardContent>
        </Card>
      </Section>

      <Section icon={Pill} title={t.yourMedicines} delay={0.2}>
        <ul className="space-y-4">
          {result.explanations.map((e, i) => (
            <BlurFade key={e.medication_id} delay={0.25 + 0.05 * i}>
              <MedicineCard explanation={e} med={byId[e.medication_id]} color={colorOf(e.medication_id)} language={language} />
            </BlurFade>
          ))}
        </ul>
      </Section>
    </main>
  )
}

function Section({ icon: Icon, title, delay, children }) {
  return (
    <BlurFade delay={delay}>
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-xl font-bold">
          <Icon className="size-5 text-primary" /> {title}
        </h2>
        {children}
      </section>
    </BlurFade>
  )
}

function Stat({ value, label, alert = false }) {
  return (
    <div className={cn('rounded-2xl px-2 py-3', alert ? 'bg-destructive/10 text-destructive' : 'bg-muted')}>
      <dd className="text-3xl font-bold tabular-nums">{value}</dd>
      <dt className={cn('text-sm', !alert && 'text-muted-foreground')}>{label}</dt>
    </div>
  )
}

function Finding({ finding: f }) {
  const { icon: Icon, tone } = FINDINGS[f.kind]
  return (
    <li className={cn('flex gap-3 rounded-2xl border-2 p-4', TONES[tone])}>
      <span className="finding-icon flex size-10 shrink-0 items-center justify-center rounded-full">
        <Icon className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="finding-title text-lg font-semibold leading-snug">{f.title}</p>
        <p className="mt-1">{f.detail}</p>
        {f.evidence && (
          <blockquote className="mt-3 rounded-xl border-s-4 border-current/20 bg-card/70 px-3 py-2 text-sm text-muted-foreground italic">
            “{f.evidence}”
          </blockquote>
        )}
        {f.citation && <SourceLink citation={f.citation} className="mt-2" />}
      </div>
    </li>
  )
}

function MedicineCard({ explanation: e, med, color, language }) {
  const t = useT()
  const lowConfidence = med && med.extracted.confidence < 0.7
  return (
    <Card className="overflow-hidden rounded-3xl shadow-sm">
      <div className="h-1.5" style={{ background: color }} />
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl" style={{ background: `${color}1a`, color }}>
            <Pill className="size-5" />
          </span>
          <div>
            <CardTitle className="text-xl">{e.display_name}</CardTitle>
            {med?.standard_name && <p className="text-sm text-muted-foreground">{med.standard_name}</p>}
            {lowConfidence && (
              <Badge className="mt-2 h-6 bg-warning px-2.5 text-sm text-warning-foreground">
                <ScanSearch /> {t.hardToRead}
              </Badge>
            )}
          </div>
        </div>
        <SpeakButton text={`${e.display_name}. ${e.purpose} ${e.how_to_take} ${e.warnings}`} language={language} />
      </CardHeader>
      <CardContent className="space-y-4">
        <Detail icon={Target} label={t.whatFor}>{e.purpose}</Detail>
        <Detail icon={Clock} label={t.howTake}>{e.how_to_take}</Detail>
        {e.warnings && <Detail icon={AlertTriangle} label={t.important}>{e.warnings}</Detail>}
        {med?.citations.length > 0 && (
          <>
            <Separator />
            <div className="flex flex-wrap gap-2">
              {med.citations.map((c) => <SourceLink key={c.url} citation={c} pill />)}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function Detail({ icon: Icon, label, children }) {
  return (
    <div className="flex gap-3">
      <Icon className="mt-1 size-4 shrink-0 text-muted-foreground" />
      <div>
        <p className="text-sm font-semibold text-muted-foreground">{label}</p>
        <p>{children}</p>
      </div>
    </div>
  )
}

function SourceLink({ citation, pill = false, className }) {
  const t = useT()
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noreferrer"
      className={cn(
        'inline-flex items-center gap-1.5 text-sm font-medium text-primary underline-offset-4 hover:underline',
        pill && 'rounded-full border bg-card px-3 py-1 no-underline hover:bg-muted',
        className,
      )}
    >
      <ExternalLink className="size-3.5" /> {pill ? citation.label : `${t.source} ${citation.label}`}
    </a>
  )
}
