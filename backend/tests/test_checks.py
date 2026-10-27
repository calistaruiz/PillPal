from app.pipeline import checks


def test_duplicate_ingredient_is_flagged(med):
    tylenol = med("a", "Tylenol", ["acetaminophen"])
    percocet = med("b", "Percocet", ["acetaminophen", "oxycodone"])

    findings = checks.find_duplicates([tylenol, percocet])

    assert len(findings) == 1
    assert findings[0].kind == "duplicate"
    assert "acetaminophen" in findings[0].title
    assert findings[0].medication_ids == ["a", "b"]


def test_no_duplicate_for_different_ingredients(med):
    assert checks.find_duplicates([med("a", "A", ["warfarin"]), med("b", "B", ["lisinopril"])]) == []


def test_interaction_found_by_ingredient_name(med, label):
    warfarin = med("a", "Warfarin", ["warfarin"])
    other = med("b", "Fluconazole", ["fluconazole"])
    labels = {"a": label("Drugs that increase INR. Fluconazole may increase warfarin levels. Monitor closely.")}

    findings = checks.find_interactions([warfarin, other], labels)

    assert len(findings) == 1
    assert findings[0].kind == "interaction"
    assert "Fluconazole may increase warfarin levels." in findings[0].evidence
    assert findings[0].citation.url == "https://dailymed.example/abc"


def test_interaction_found_by_drug_class(med, label):
    warfarin = med("a", "Warfarin", ["warfarin"])
    ibuprofen = med("b", "Advil", ["ibuprofen"])
    labels = {"a": label("Use with NSAIDs increases the risk of bleeding.")}

    findings = checks.find_interactions([warfarin, ibuprofen], labels)

    assert len(findings) == 1
    assert "NSAIDs" in findings[0].evidence


def test_interaction_checks_both_labels(med, label):
    warfarin = med("a", "Warfarin", ["warfarin"])
    ibuprofen = med("b", "Advil", ["ibuprofen"])
    labels = {"b": label("Ask a doctor before use if you are taking a blood thinner (anticoagulant).")}

    assert len(checks.find_interactions([warfarin, ibuprofen], labels)) == 1


def test_no_interaction_without_mention(med, label):
    a = med("a", "A", ["warfarin"])
    b = med("b", "B", ["lisinopril"])
    labels = {"a": label("Antibiotics may change INR.")}

    assert checks.find_interactions([a, b], labels) == []


def test_word_boundaries_prevent_partial_matches(med, label):
    a = med("a", "A", ["warfarin"])
    b = med("b", "B", ["iron"])
    labels = {"a": label("Environmental factors may affect INR.")}

    assert checks.find_interactions([a, b], labels) == []


def test_low_confidence_and_unmatched_are_flagged(med):
    blurry = med("a", "Lisinopril", ["lisinopril"], confidence=0.4, unclear_fields=["strength"])
    unknown = med("b", "Mystery", [])
    unknown.rxcui = None

    kinds = sorted(f.kind for f in checks.find_reading_problems([blurry, unknown]))

    assert kinds == ["low_confidence", "not_found"]
