"""Regelmotorens data: hvilke ord i en transaksjonsbeskrivelse peker mot hvilken kategori.

Redigeres direkte i denne filen. Legg til nye nøkkelord i eksisterende regel,
eller en ny Rule for en ny underkategori. Rekkefølge spiller ingen rolle —
motoren i engine.py velger alltid det mest spesifikke (lengste) treffet.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    parent: str
    child: str
    keywords: tuple[str, ...]


RULES: tuple[Rule, ...] = (
    Rule("Bolig", "Leie", ("HUSLEIE", "LEIEKONTRAKT")),
    Rule("Bolig", "Strøm", ("FJORDKRAFT", "TIBBER", "HAFSLUND", "FORTUM")),
    Rule("Bolig", "Internett", ("TELENOR", "ALTIBOX", "GET AS")),
    Rule("Mat", "Dagligvare", ("REMA", "KIWI", "COOP", "EXTRA", "SPAR", "BUNNPRIS", "MENY")),
    Rule("Mat", "Restaurant", ("MCDONALD", "BURGER KING", "NARVESEN", "DELI DE LUCA", "PEPPES", "DOMINO")),
    Rule("Transport", "Kollektiv", ("RUTER", " VY ", "FLYTOGET", "KOLLEKTIVTRANSPORT")),
    Rule("Transport", "Drivstoff", ("CIRCLE K", "SHELL", "ESSO", "UNO-X", "YX ")),
    Rule("Abonnement", "Strømming", ("NETFLIX", "SPOTIFY", "HBO", "DISNEY+", "VIAPLAY")),
    Rule("Abonnement", "Treningssenter", ("SATS", "FRESH FITNESS", "EVO")),
    Rule("Inntekt", "Lønn", ("LØNN", "AKER SOLUTIONS")),
    Rule("Inntekt", "Freelance", ("FAKTURA UTBETALING", "FREELANCE")),
)
