"""Generate fake pharmacy labels and a discharge sheet for demos and testing.

Everything here is fictional: the patient, doctors, pharmacy, hospital, and Rx
numbers. Every image is marked as a sample. Phone numbers use the 555-01xx range
reserved for fiction.

Usage (from the repo root):
    pip install pillow
    python samples/make_labels.py

Output goes to samples/labels/: one PNG per bottle label (4 x 2 in at 300 dpi),
a discharge sheet, a blurry copy for the low-confidence test, and print.html for
printing labels to stick on empty bottles.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent / "labels"
SAMPLE_NOTICE = "SAMPLE LABEL FOR SOFTWARE TESTING - NOT A REAL PRESCRIPTION"

PATIENT = "ROSA MARTINEZ"
PHARMACY = ("MAPLE STREET PHARMACY", "120 Maple St, Springfield  (555) 010-0142")
FILLED = "10/20/2026"

# ---------- Fonts (Windows first, then common Linux/macOS locations) ----------

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu"),
             Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts")]
FONT_FILES = {
    "regular": ["arial.ttf", "DejaVuSans.ttf", "Arial.ttf"],
    "bold": ["arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"],
    "mono": ["consola.ttf", "DejaVuSansMono.ttf", "Courier New.ttf"],
    "cjk": ["msyh.ttc", "NotoSansCJK-Regular.ttc", "PingFang.ttc", "Arial Unicode.ttf"],
    "cjk_bold": ["msyhbd.ttc", "NotoSansCJK-Bold.ttc", "PingFang.ttc", "Arial Unicode.ttf"],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for name in FONT_FILES[kind]:
        for folder in FONT_DIRS:
            if (folder / name).exists():
                return ImageFont.truetype(str(folder / name), size)
    raise SystemExit(f"No font found for {kind!r}. Install DejaVu or Noto fonts.")


# ---------- Label data ----------
# Each label: file name, drug line, strength/form, directions, prescriber, qty,
# refills, optional auxiliary sticker, and the script ("latin" or "cjk").

LABELS = [
    dict(file="01-warfarin.png", drug="WARFARIN SODIUM 5 MG TABLET", generic="Generic for Coumadin",
         directions="TAKE 1 TABLET BY MOUTH ONCE DAILY IN THE EVENING.",
         prescriber="DR. ANITA PATEL", qty="30", refills="3", rx="RX 4471029",
         sticker=("DO NOT TAKE ASPIRIN OR NSAIDS WITHOUT ASKING YOUR DOCTOR", "#facc15")),
    dict(file="02-ibuprofen.png", drug="IBUPROFEN 400 MG TABLET", generic="Generic for Motrin",
         directions="TAKE 1 TABLET BY MOUTH EVERY 6 HOURS AS NEEDED FOR PAIN. TAKE WITH FOOD.",
         prescriber="DR. KEVIN NGUYEN", qty="40", refills="0", rx="RX 4471563",
         sticker=("TAKE WITH FOOD OR MILK", "#fb923c")),
    dict(file="03-oxycodone-acetaminophen.png", drug="OXYCODONE-ACETAMINOPHEN 5-325 MG TAB",
         generic="Generic for Percocet",
         directions="TAKE 1 TABLET BY MOUTH EVERY 6 HOURS AS NEEDED FOR SEVERE PAIN.",
         prescriber="DR. KEVIN NGUYEN", qty="20", refills="0", rx="RX 4471564",
         sticker=("MAY CAUSE DROWSINESS. DO NOT DRINK ALCOHOL", "#f87171")),
    dict(file="04-lisinopril.png", drug="LISINOPRIL 10 MG TABLET", generic="Generic for Zestril",
         directions="TAKE 1 TABLET BY MOUTH EVERY MORNING.",
         prescriber="DR. ANITA PATEL", qty="90", refills="2", rx="RX 4470988", sticker=None),
    dict(file="05-metformin-spanish.png", drug="METFORMINA 500 MG TABLETA", generic="Metformin HCl 500 mg",
         directions="TOME 1 TABLETA POR VIA ORAL DOS VECES AL DIA CON LAS COMIDAS.",
         prescriber="DRA. ELENA CASTILLO", qty="60", refills="5", rx="RX 4469120",
         sticker=("TOMAR CON ALIMENTOS", "#fb923c")),
    dict(file="06-atorvastatin-chinese.png", drug="阿托伐他汀 20 毫克 片剂", generic="Atorvastatin 20 mg",
         directions="每晚睡前口服 1 片。", prescriber="DR. MEI LIN", qty="30", refills="5",
         rx="RX 4468731", sticker=None, script="cjk"),
    dict(file="07-amlodipine-vietnamese.png", drug="AMLODIPINE 5 MG VIÊN NÉN", generic="Generic for Norvasc",
         directions="UỐNG 1 VIÊN MỖI NGÀY VÀO BUỔI SÁNG.",
         prescriber="DR. MINH TRAN", qty="30", refills="5", rx="RX 4468802", sticker=None),
]

# Over-the-counter bottle (no pharmacy label): fictional store brand.
OTC = dict(file="08-otc-acetaminophen.png", brand="CAREWELL", title="Extra Strength Pain Relief",
           drug="Acetaminophen 500 mg", count="100 Caplets",
           directions="Adults: take 2 caplets every 6 hours while symptoms last. "
                      "Do not take more than 6 caplets in 24 hours.")

DISCHARGE = dict(
    file="09-discharge-sheet.png",
    hospital="CEDAR VALLEY REGIONAL HOSPITAL",
    meds=[
        ("Warfarin 5 mg tablet", "1 tablet by mouth once daily in the evening", "Continue"),
        ("Oxycodone-acetaminophen 5-325 mg", "1 tablet every 6 hours as needed for severe pain", "New"),
        ("Lisinopril 10 mg tablet", "1 tablet by mouth every morning", "Continue"),
        ("Metformin 500 mg tablet", "1 tablet twice daily with meals", "Continue"),
        ("Pantoprazole 40 mg tablet", "1 tablet once daily before breakfast", "New"),
    ],
)


# ---------- Drawing helpers ----------

def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    """Wrap by words, or by character for scripts without spaces."""
    units = text.split(" ") if " " in text else list(text)
    joiner = " " if " " in text else ""
    lines, line = [], ""
    for unit in units:
        candidate = f"{line}{joiner}{unit}" if line else unit
        if draw.textlength(candidate, font=fnt) <= width:
            line = candidate
        else:
            lines.append(line)
            line = unit
    return lines + [line] if line else lines


def bottle_label(data: dict) -> Image.Image:
    w, h = 1200, 600
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    cjk = data.get("script") == "cjk"
    body = font("cjk" if cjk else "regular", 30)
    bold = font("cjk_bold" if cjk else "bold", 44)
    small = font("regular", 24)
    mono = font("mono", 26)

    # Pharmacy header band
    d.rectangle([0, 0, w, 92], fill="#1e3a5f")
    d.text((32, 14), PHARMACY[0], font=font("bold", 36), fill="white")
    d.text((32, 56), PHARMACY[1], font=small, fill="#cbd5e1")
    d.text((w - 32, 30), data["rx"], font=mono, fill="white", anchor="ra")

    y = 112
    d.text((32, y), PATIENT, font=font("bold", 40), fill="#111")
    d.text((w - 32, y + 8), f"FILLED {FILLED}", font=small, fill="#444", anchor="ra")
    y += 62

    text_width = w - 64 - (300 if data.get("sticker") else 0)
    for line in wrap(d, data["directions"], body if cjk else font("bold", 32), text_width):
        d.text((32, y), line, font=body if cjk else font("bold", 32), fill="#111")
        y += 44
    y += 10

    d.text((32, y), data["drug"], font=bold, fill="#111")
    y += 72 if cjk else 58  # CJK fonts sit lower in their line box
    d.text((32, y), data["generic"], font=small, fill="#444")
    y += 40

    d.line([32, y, w - 32, y], fill="#94a3b8", width=2)
    y += 14
    d.text((32, y), f"QTY: {data['qty']}", font=small, fill="#222")
    d.text((220, y), f"REFILLS: {data['refills']}", font=small, fill="#222")
    d.text((470, y), f"PRESCRIBER: {data['prescriber']}", font=small, fill="#222")

    if data.get("sticker"):
        text, color = data["sticker"]
        box = [w - 300, 180, w - 32, 400]
        d.rounded_rectangle(box, radius=18, fill=color)
        sticker_font = font("bold", 26)
        lines = wrap(d, text, sticker_font, 230)
        ty = (box[1] + box[3]) / 2 - len(lines) * 17
        for line in lines:
            d.text(((box[0] + box[2]) / 2, ty), line, font=sticker_font, fill="#111", anchor="ma")
            ty += 34

    d.text((w / 2, h - 30), SAMPLE_NOTICE, font=font("regular", 18), fill="#9ca3af", anchor="mm")
    return img


def otc_label(data: dict) -> Image.Image:
    w, h = 1200, 600
    img = Image.new("RGB", (w, h), "#fff7ed")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 360, h], fill="#b91c1c")
    d.text((180, 120), data["brand"], font=font("bold", 48), fill="white", anchor="mm")
    d.text((180, 300), "500", font=font("bold", 120), fill="white", anchor="mm")
    d.text((180, 380), "mg each", font=font("regular", 32), fill="white", anchor="mm")
    d.text((180, 500), data["count"], font=font("bold", 30), fill="white", anchor="mm")

    x, y = 400, 50
    d.text((x, y), data["title"], font=font("bold", 50), fill="#7f1d1d")
    y += 76
    d.text((x, y), data["drug"], font=font("bold", 40), fill="#111")
    y += 60
    d.text((x, y), "Pain reliever / fever reducer", font=font("regular", 30), fill="#444")
    y += 70
    d.text((x, y), "Directions", font=font("bold", 30), fill="#111")
    y += 42
    for line in wrap(d, data["directions"], font("regular", 28), w - x - 40):
        d.text((x, y), line, font=font("regular", 28), fill="#222")
        y += 38
    d.text((w / 2 + 180, h - 30), SAMPLE_NOTICE, font=font("regular", 18), fill="#9ca3af", anchor="mm")
    return img


def discharge_sheet(data: dict) -> Image.Image:
    w, h = 1700, 2200
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    serif_bold = font("bold", 44)
    body = font("regular", 30)
    bold = font("bold", 30)

    d.text((100, 100), data["hospital"], font=serif_bold, fill="#0f3d5e")
    d.text((100, 160), "Discharge Instructions: Medication List", font=font("regular", 36), fill="#333")
    d.line([100, 220, w - 100, 220], fill="#0f3d5e", width=4)

    y = 260
    for label, value in [("Patient:", "Rosa Martinez"), ("Date of birth:", "03/14/1951"),
                         ("Discharge date:", FILLED), ("Attending physician:", "Dr. Kevin Nguyen"),
                         ("Reason for stay:", "Right hip fracture repair")]:
        d.text((100, y), label, font=bold, fill="#111")
        d.text((480, y), value, font=body, fill="#111")
        y += 48

    y += 40
    cols = [100, 720, 1420]
    d.rectangle([100, y, w - 100, y + 60], fill="#e2e8f0")
    for x, title in zip(cols, ["Medication", "How to take", "Status"]):
        d.text((x + 16, y + 14), title, font=bold, fill="#111")
    y += 60
    for name, how, status in data["meds"]:
        row_lines = wrap(d, how, body, cols[2] - cols[1] - 40)
        row_h = max(80, 24 + 42 * len(row_lines))
        d.rectangle([100, y, w - 100, y + row_h], outline="#cbd5e1", width=2)
        d.text((cols[0] + 16, y + 20), name, font=bold if status == "New" else body, fill="#111")
        for i, line in enumerate(row_lines):
            d.text((cols[1] + 16, y + 20 + 42 * i), line, font=body, fill="#111")
        d.text((cols[2] + 16, y + 20), status, font=bold if status == "New" else body,
               fill="#b91c1c" if status == "New" else "#111")
        y += row_h

    y += 60
    d.text((100, y), "Follow-up", font=bold, fill="#111")
    y += 48
    for line in ["See Dr. Anita Patel in 1 week to check your INR (blood thinning level).",
                 "Call (555) 010-0177 with questions about your medicines."]:
        d.text((100, y), line, font=body, fill="#111")
        y += 44

    d.text((w / 2, h - 80), "SAMPLE DOCUMENT FOR SOFTWARE TESTING - NOT A REAL MEDICAL RECORD",
           font=font("regular", 24), fill="#9ca3af", anchor="mm")
    return img


PRINT_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PillPal sample labels</title>
<style>
  body { font-family: Arial, sans-serif; margin: 0.5in; }
  h1 { font-size: 16pt; }
  p { font-size: 10pt; color: #555; }
  .labels { display: flex; flex-wrap: wrap; gap: 0.25in; }
  .labels img { width: 4in; height: 2in; border: 1px dashed #bbb; }
  .sheet { page-break-before: always; width: 7.5in; }
  @media print { h1, p { display: none; } }
</style>
</head>
<body>
<h1>PillPal sample labels</h1>
<p>Print at 100% scale. Cut out each label and tape it around an empty bottle, then photograph it.
All names and numbers are fictional.</p>
<div class="labels">
{labels}
</div>
<img class="sheet" src="09-discharge-sheet.png" alt="Sample discharge sheet">
</body>
</html>
"""


def main():
    OUT.mkdir(exist_ok=True)
    files = []
    for data in LABELS:
        bottle_label(data).save(OUT / data["file"], dpi=(300, 300))
        files.append(data["file"])
    otc_label(OTC).save(OUT / OTC["file"], dpi=(300, 300))
    files.append(OTC["file"])
    discharge_sheet(DISCHARGE).save(OUT / DISCHARGE["file"], dpi=(200, 200))

    # Blurry, tilted copy of the lisinopril label for the low-confidence test.
    # Washed out (like glare) and blurred enough that the strength is hard to read.
    blurry = Image.open(OUT / "04-lisinopril.png").rotate(4, expand=True, fillcolor="white")
    blurry = Image.blend(blurry, Image.new("RGB", blurry.size, "white"), 0.45)
    blurry.filter(ImageFilter.GaussianBlur(8)).save(OUT / "10-lisinopril-blurry.png")

    tags = "\n".join(f'  <img src="{f}" alt="{f}">' for f in files)
    (OUT / "print.html").write_text(PRINT_HTML.replace("{labels}", tags), encoding="utf-8")
    print(f"Wrote {len(files) + 2} images and print.html to {OUT}")


if __name__ == "__main__":
    main()
