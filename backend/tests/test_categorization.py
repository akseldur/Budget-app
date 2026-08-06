from app.categorization.engine import categorize

# Realistiske eksempler på hvordan DNB formaterer transaksjonsbeskrivelser
DNB_EXAMPLES = [
    ("Varekjøp REMA 1000 OSLO 06.08", "Mat", "Dagligvare"),
    ("Vipps *KIWI Majorstuen", "Mat", "Dagligvare"),
    ("AVTALEGIRO FJORDKRAFT AS", "Bolig", "Strøm"),
    ("Nettgiro HUSLEIE AUGUST", "Bolig", "Leie"),
    ("Varekjøp RUTER AS 06.08", "Transport", "Kollektiv"),
    ("Varekjøp CIRCLE K SINSEN", "Transport", "Drivstoff"),
    ("Fast trekk NETFLIX.COM", "Abonnement", "Strømming"),
    ("LØNN AKER SOLUTIONS AS", "Inntekt", "Lønn"),
]


def test_kjente_beskrivelser_gir_riktig_kategori():
    for description, expected_parent, expected_child in DNB_EXAMPLES:
        match = categorize(description)
        assert match is not None, f"Fant ingen kategori for: {description!r}"
        assert (match.parent, match.child) == (expected_parent, expected_child), (
            f"{description!r} -> forventet {expected_parent}/{expected_child}, "
            f"fikk {match.parent}/{match.child}"
        )


def test_ukjent_beskrivelse_gir_ingen_match():
    assert categorize("Overføring til Ola Nordmann") is None


def test_case_og_mellomrom_spiller_ingen_rolle():
    assert categorize("  varekjøp   rema 1000   oslo  ") is not None


def test_mest_spesifikke_treff_vinner_ved_flere_kandidater():
    # "AKER SOLUTIONS" (Inntekt/Lønn) er lengre og mer spesifikk enn en
    # eventuell kortere, mer generisk match - skal alltid vinne.
    match = categorize("LØNN AKER SOLUTIONS AS SEPTEMBER")
    assert match is not None
    assert match.matched_keyword == "AKER SOLUTIONS"


def test_delstreng_i_annet_ord_gir_ikke_falsk_treff():
    # "YX " (med mellomrom) skal ikke tilfeldig matche midt i et annet ord
    assert categorize("Varekjøp EKSTRAORDINÆRT GEBYR") is None
