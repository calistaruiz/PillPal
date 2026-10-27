import { useRef } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Camera, ImagePlus, Lightbulb, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useT } from '@/lib/i18n'

export default function PhotoPicker({ photos, onAdd, onRemove }) {
  const t = useT()
  const cameraInput = useRef(null)
  const galleryInput = useRef(null)

  function handle(e) {
    if (e.target.files?.length) onAdd(e.target.files)
    e.target.value = '' // allow picking the same file again
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Button onClick={() => cameraInput.current.click()} className="h-14 rounded-2xl text-lg">
          <Camera className="size-5" /> {t.takePhoto}
        </Button>
        <Button variant="outline" onClick={() => galleryInput.current.click()} className="h-14 rounded-2xl border-2 text-lg">
          <ImagePlus className="size-5" /> {t.choosePhotos}
        </Button>
      </div>
      <input ref={cameraInput} type="file" accept="image/*" capture="environment" onChange={handle} hidden />
      <input ref={galleryInput} type="file" accept="image/*" multiple onChange={handle} hidden />

      {photos.length === 0 ? (
        <div className="flex items-start gap-3 rounded-2xl border-2 border-dashed bg-muted/50 p-4 text-sm text-muted-foreground">
          <Lightbulb className="mt-0.5 size-5 shrink-0 text-warning-foreground" />
          <p>
            <span className="font-semibold text-foreground">{t.tipsTitle}</span> {t.tipsBody}
          </p>
        </div>
      ) : (
        <div>
          <Badge variant="secondary" className="mb-3 h-6 px-2.5 text-sm">
            {t.photosAdded(photos.length)}
          </Badge>
          <ul className="grid grid-cols-3 gap-3 sm:grid-cols-4">
            <AnimatePresence initial={false}>
              {photos.map((photo, i) => (
                <motion.li
                  key={photo.url}
                  layout
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 28 }}
                  className="relative"
                >
                  <img
                    src={photo.url}
                    alt={t.photoAlt(i + 1)}
                    className="aspect-square w-full rounded-2xl bg-white object-contain p-1 shadow-sm ring-1 ring-border"
                  />
                  <button
                    onClick={() => onRemove(i)}
                    aria-label={t.removePhoto(i + 1)}
                    className="absolute -end-2 -top-2 flex size-8 items-center justify-center rounded-full bg-foreground text-background shadow-md"
                  >
                    <X className="size-4" />
                  </button>
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
        </div>
      )}
    </div>
  )
}
