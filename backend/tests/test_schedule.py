from app.pipeline.schedule import build_schedule


def _slots(schedule):
    return {s.slot: [i.name for i in s.items] for s in schedule}


def test_explicit_times_win(med):
    schedule = build_schedule([med("a", "Warfarin", [], times_per_day=1, times_of_day=["evening"])])
    assert _slots(schedule) == {"evening": ["Warfarin"]}


def test_times_per_day_spreads_doses(med):
    schedule = build_schedule([med("a", "Metformin", [], times_per_day=2)])
    assert _slots(schedule) == {"morning": ["Metformin"], "evening": ["Metformin"]}


def test_as_needed_goes_in_its_own_slot(med):
    schedule = build_schedule([med("a", "Ibuprofen", [], as_needed=True, times_per_day=4)])
    assert _slots(schedule) == {"as_needed": ["Ibuprofen"]}


def test_unclear_timing_is_flagged(med):
    schedule = build_schedule([med("a", "Mystery", [])])
    assert schedule[0].slot == "morning"
    assert schedule[0].items[0].notes == ["timing_unclear"]


def test_slots_are_in_day_order_and_food_notes_kept(med):
    schedule = build_schedule([
        med("a", "B", [], times_of_day=["bedtime"]),
        med("b", "A", [], times_of_day=["morning"], with_food=True),
    ])
    assert [s.slot for s in schedule] == ["morning", "bedtime"]
    assert schedule[0].items[0].notes == ["with_food"]


def test_empty_stomach_never_shares_a_slot_with_food(med):
    schedule = build_schedule([
        med("a", "Metformin", [], times_per_day=2, with_food=True),
        med("b", "Pantoprazole", [], times_of_day=["morning"], with_food=False),
        med("c", "Lisinopril", [], times_of_day=["morning"]),
    ])
    assert _slots(schedule) == {
        "before_breakfast": ["Pantoprazole"],
        "morning": ["Metformin", "Lisinopril"],
        "evening": ["Metformin"],
    }
    assert schedule[0].time == "7:30 AM"
    assert schedule[0].items[0].notes == ["empty_stomach"]


def test_empty_stomach_twice_daily_goes_before_each_meal(med):
    schedule = build_schedule([med("a", "Omeprazole", [], times_per_day=2, with_food=False)])
    assert _slots(schedule) == {"before_breakfast": ["Omeprazole"], "before_dinner": ["Omeprazole"]}


def test_empty_stomach_at_bedtime_stays_at_bedtime(med):
    schedule = build_schedule([med("a", "Alendronate", [], times_of_day=["bedtime"], with_food=False)])
    assert _slots(schedule) == {"bedtime": ["Alendronate"]}
