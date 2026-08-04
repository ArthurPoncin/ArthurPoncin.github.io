#!/usr/bin/env python3
"""Audit du QCM : detecte les biais qui rendent une bonne reponse devinable.

Les QCM generes par IA presentent deux biais recurrents :
  1. la bonne reponse est la plus longue ;
  2. la bonne reponse est toujours au meme rang (souvent la 2e ou la 3e).

Ce script mesure les deux et sort en code 1 si un seuil est depasse.

Usage : python3 audit_qcm.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

QCM = Path(__file__).resolve().parent / "_src" / "qcm.json"

# Une bonne reponse la plus longue reste normale de temps en temps (1 chance
# sur 4 au hasard). On s'alarme au-dela d'un tiers.
SEUIL_PLUS_LONGUE = 0.33
# Repartition des rangs : au hasard chaque rang sort 25 % du temps. On tolere
# une derive jusqu'a 35 % sur un rang donne.
SEUIL_RANG = 0.35


def texte_nu(html: str) -> str:
    """Longueur percue par le lecteur : on retire les balises."""
    return re.sub(r"<[^>]+>", "", html).strip()


def main() -> int:
    data = json.loads(QCM.read_text(encoding="utf-8"))
    questions = data["questions"]
    themes = data["themes"]
    total = len(questions)

    rangs = Counter()
    plus_longue = 0
    plus_courte = 0
    par_theme = Counter()
    ecarts: list[tuple[int, str, int]] = []
    problemes: list[str] = []

    for i, q in enumerate(questions):
        par_theme[q["t"]] += 1
        c = q["c"]
        rangs[c] += 1

        if q["t"] not in themes:
            problemes.append(f"Q{i + 1} : theme inconnu '{q['t']}'")
        if len(q["a"]) != 4:
            problemes.append(f"Q{i + 1} : {len(q['a'])} propositions au lieu de 4")
        if not 0 <= c < len(q["a"]):
            problemes.append(f"Q{i + 1} : index de bonne reponse hors bornes")
            continue

        longueurs = [len(texte_nu(a)) for a in q["a"]]
        lc = longueurs[c]
        autres = [x for j, x in enumerate(longueurs) if j != c]

        if lc == max(longueurs):
            plus_longue += 1
        if lc == min(longueurs):
            plus_courte += 1

        # Ecart de la bonne reponse a la moyenne des distracteurs, en caracteres.
        ecarts.append((i + 1, q["t"], round(lc - sum(autres) / len(autres))))

    print(f"{total} questions\n")

    print("Repartition par theme")
    for t, n in par_theme.most_common():
        print(f"  {themes.get(t, t):32} {n:2}")

    print("\nRang de la bonne reponse")
    for r in range(4):
        n = rangs[r]
        pct = n / total
        drapeau = "  <-- desequilibre" if pct > SEUIL_RANG else ""
        print(f"  position {r + 1} : {n:2}  ({pct:5.1%}){drapeau}")
        if pct > SEUIL_RANG:
            problemes.append(f"Rang {r + 1} sur-represente : {pct:.1%}")

    print("\nLongueur de la bonne reponse")
    pct_longue = plus_longue / total
    print(f"  la plus longue des 4 : {plus_longue:2}  ({pct_longue:5.1%})")
    print(f"  la plus courte des 4 : {plus_courte:2}  ({plus_courte / total:5.1%})")
    if pct_longue > SEUIL_PLUS_LONGUE:
        problemes.append(f"Bonne reponse la plus longue dans {pct_longue:.1%} des cas")

    moyenne = sum(e[2] for e in ecarts) / len(ecarts)
    print(f"\n  ecart moyen a la moyenne des distracteurs : {moyenne:+.1f} caracteres")
    if abs(moyenne) > 15:
        problemes.append(f"Ecart moyen de longueur trop marque : {moyenne:+.1f}")

    pires = sorted(ecarts, key=lambda e: -e[2])[:5]
    print("  questions ou la bonne reponse depasse le plus les distracteurs :")
    for num, theme, ecart in pires:
        print(f"    Q{num:2} [{theme:10}] {ecart:+4} car.")

    print()
    if problemes:
        print("PROBLEMES")
        for p in problemes:
            print(f"  - {p}")
        return 1
    print("Aucun biais detecte au-dela des seuils.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
