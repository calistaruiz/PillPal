# Test samples

**Synthetic only.** Never add photos of a real person's medications or paperwork.

## Ready-made labels

`labels/` holds fake pharmacy labels and a hospital discharge sheet for one fictional
patient, Rosa Martinez, after a hip fracture repair. Every image is marked as a sample.
Regenerate them with:

```bash
pip install pillow
python samples/make_labels.py
```

| File | Medicine | Why it's there |
|---|---|---|
| `01-warfarin.png` | Warfarin 5 mg, evenings | Blood thinner; interacts with ibuprofen |
| `02-ibuprofen.png` | Ibuprofen 400 mg, as needed | NSAID; the interaction partner |
| `03-oxycodone-acetaminophen.png` | Oxycodone-acetaminophen 5-325 mg | Contains acetaminophen (duplicate test) |
| `04-lisinopril.png` | Lisinopril 10 mg, mornings | Plain once-daily medicine |
| `05-metformin-spanish.png` | Metformin 500 mg, twice daily | Spanish label; "twice daily" with no times |
| `06-atorvastatin-chinese.png` | Atorvastatin 20 mg, bedtime | Chinese label |
| `07-amlodipine-vietnamese.png` | Amlodipine 5 mg, mornings | Vietnamese label |
| `08-otc-acetaminophen.png` | Store-brand acetaminophen 500 mg | Over-the-counter; second acetaminophen source |
| `09-discharge-sheet.png` | 5 medicines incl. new pantoprazole | Overlaps with bottles; one medicine only on paper |
| `10-lisinopril-blurry.png` | Lisinopril, blurred and washed out | Should be flagged "please double-check" |

You can upload the PNGs directly, or open `labels/print.html`, print at 100% scale, tape
the labels onto empty bottles, and photograph them (more convincing in a live demo).

## Demo scenarios

**1. The headline demo** (upload `01`, `02`, `03`, `08`, `09`)

- Warfarin, ibuprofen, oxycodone-acetaminophen, acetaminophen, lisinopril, metformin and
  pantoprazole, each listed once even though four appear on both a bottle and the sheet
- Possible interaction: warfarin + ibuprofen (bleeding risk)
- Same ingredient twice: acetaminophen in both the Percocet generic and the store brand
- Pantoprazole comes only from the discharge sheet

**2. Your language** (upload `05`, `06`, `07`, choose Spanish, Chinese or Vietnamese)

- All three read correctly from non-English labels
- Schedule: amlodipine morning; metformin morning and evening; atorvastatin bedtime
- Explanations come back in the chosen language

**3. Honest about uncertainty** (upload `10`)

- Lisinopril is flagged "please double-check" rather than guessed

## Adding your own cases

Photograph fake labels you make yourself and add a folder per case with an
`expected.json` describing what PillPal should find:

```json
{
  "medications": ["warfarin 5 mg", "ibuprofen 400 mg"],
  "must_flag": ["interaction: warfarin + ibuprofen"],
  "language": "es"
}
```
