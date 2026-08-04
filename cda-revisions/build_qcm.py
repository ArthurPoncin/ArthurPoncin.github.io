#!/usr/bin/env python3
"""Injecte _src/qcm.json dans qcm_template.html pour produire qcm.html.

La page resultante est autonome : aucune requete reseau, elle fonctionne
aussi bien sur GitHub Pages qu'ouverte en file:// depuis le disque.

Usage : python3 build_qcm.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
donnees = json.loads((ROOT / "_src" / "qcm.json").read_text(encoding="utf-8"))
gabarit = (ROOT / "qcm_template.html").read_text(encoding="utf-8")

# </script> a l'interieur du JSON fermerait la balise du navigateur.
charge = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")

sortie = gabarit.replace("/*__DONNEES__*/", charge)
if sortie == gabarit:
    raise SystemExit("Marqueur /*__DONNEES__*/ introuvable dans le gabarit.")

(ROOT / "qcm.html").write_text(sortie, encoding="utf-8")
print(f"qcm.html genere - {len(donnees['questions'])} questions, "
      f"{len(donnees['themes'])} themes")
