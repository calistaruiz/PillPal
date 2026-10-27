"""Combine every medication into one daily schedule. Follows the label; never changes it."""

from ..models import Medication, ScheduleItem, ScheduleSlot

SLOT_ORDER = ["before_breakfast", "morning", "before_lunch", "midday",
              "before_dinner", "evening", "bedtime", "as_needed"]
SLOT_TIMES = {
    "before_breakfast": "7:30 AM", "morning": "8:00 AM",
    "before_lunch": "11:30 AM", "midday": "12:00 PM",
    "before_dinner": "5:30 PM", "evening": "6:00 PM",
    "bedtime": "9:00 PM",
}

# When a label says "twice daily" without saying when, spread doses out.
DEFAULT_SLOTS = {
    1: ["morning"],
    2: ["morning", "evening"],
    3: ["morning", "midday", "evening"],
    4: ["morning", "midday", "evening", "bedtime"],
}

# Empty-stomach medicines get their own slot before the meal, so they never share
# a time with medicines that must be taken with food.
BEFORE_MEAL = {"morning": "before_breakfast", "midday": "before_lunch", "evening": "before_dinner"}


def build_schedule(meds: list[Medication]) -> list[ScheduleSlot]:
    slots: dict[str, list[ScheduleItem]] = {name: [] for name in SLOT_ORDER}

    for med in meds:
        e = med.extracted
        notes = []
        if e.as_needed:
            targets = ["as_needed"]
        elif e.times_of_day:
            targets = [s for s in SLOT_ORDER if s in e.times_of_day]
        elif e.times_per_day in DEFAULT_SLOTS:
            targets = DEFAULT_SLOTS[e.times_per_day]
        else:
            targets = ["morning"]
            notes.append("timing_unclear")

        if e.with_food is True:
            notes.append("with_food")
        elif e.with_food is False:
            notes.append("empty_stomach")
            targets = [BEFORE_MEAL.get(slot, slot) for slot in targets]

        for slot in targets:
            slots[slot].append(ScheduleItem(
                medication_id=med.id,
                name=e.name,
                dose=e.strength,
                notes=notes,
            ))

    return [
        ScheduleSlot(slot=name, time=SLOT_TIMES.get(name), items=items)
        for name, items in slots.items()
        if items
    ]
