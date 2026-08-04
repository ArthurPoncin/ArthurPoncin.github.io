# cda-revisions — fiches et QCM de révision, Titre CDA 2026

En ligne : <https://arthurponcin.me/cda-revisions/>

11 fiches de révision (6 transversales, 5 par dépôt) et un QCM interactif de
78 questions, pour la soutenance du Titre Professionnel Concepteur Développeur
d'Applications (RNCP 37873).

## Contenu

| Fichier | Rôle |
|---|---|
| `index.html` | Page d'accueil, écrite à la main |
| `_src/*.md` | **Sources** des fiches — c'est ici qu'on édite |
| `NN-*.html` | Fiches générées, ne pas éditer directement |
| `_src/qcm.json` | **Source** du QCM : thèmes, questions, réponses, explications |
| `qcm_template.html` | Gabarit du QCM (structure + logique) |
| `qcm.html` | QCM généré, données injectées, ne pas éditer directement |
| `style.css` | Feuille de style commune aux fiches, à l'index et au QCM |
| `template.html` | Gabarit des fiches |
| `build.py` | Markdown → fiches HTML |
| `build_qcm.py` | `qcm.json` + gabarit → `qcm.html` |
| `audit_qcm.py` | Détecte les biais qui rendraient une bonne réponse devinable |

## Régénérer

Dépendances Python : `markdown` et `pygments`.

```bash
python3 -m venv venv
./venv/bin/pip install markdown pygments

# Fiches (lit _src/*.md)
./venv/bin/python build.py

# QCM (lit _src/qcm.json)
python3 build_qcm.py

# Contrôle qualité du QCM — sort en code 1 si un biais dépasse les seuils
python3 audit_qcm.py
```

`build_qcm.py` et `audit_qcm.py` n'utilisent que la bibliothèque standard : le
venv n'est nécessaire que pour les fiches.

## Éditer une fiche

Modifier le `.md` correspondant dans `_src/`, puis relancer `build.py`.

Extensions Markdown disponibles : tableaux, listes de définitions, blocs de code
avec coloration, notes de bas de page, et les encadrés (`admonition`) :

```markdown
!!! jury "Titre de l'encadré"
    Le contenu, indenté de quatre espaces.
```

Types d'encadrés : `jury` (bleu, angle d'attaque probable), `piege` (jaune,
confusion courante), `attention` (rouge, limite assumée du projet), `note`
(gris, précision secondaire).

Les diagrammes Mermaid s'écrivent dans un bloc ` ```mermaid `. Ils sont extraits
du flux Markdown avant conversion (sinon la coloration syntaxique les
intercepterait) et rendus par le navigateur.

## Éditer le QCM

Une question dans `_src/qcm.json` :

```json
{
  "t": "securite",              // clé de thème, doit exister dans "themes"
  "q": "L'énoncé, HTML autorisé",
  "a": ["Proposition 1", "Proposition 2", "Proposition 3", "Proposition 4"],
  "c": 2,                        // index (0-3) de la bonne réponse
  "e": "L'explication affichée après la réponse, HTML autorisé"
}
```

Après toute modification, relancer `build_qcm.py` **puis** `audit_qcm.py`.

### Ce que l'audit vérifie, et pourquoi

Les QCM générés automatiquement présentent deux biais récurrents qui permettent
de trouver la bonne réponse sans connaître le sujet :

1. **la bonne réponse est la plus longue** — l'auteur y glisse une justification
   que les distracteurs n'ont pas ;
2. **la bonne réponse est toujours au même rang**, typiquement la 2ᵉ ou la 3ᵉ.

`audit_qcm.py` mesure les deux et échoue si un seuil est dépassé. État actuel :

| Indicateur | Valeur | Attendu au hasard |
|---|---|---|
| Bonne réponse la plus longue | 24,4 % | 25 % |
| Bonne réponse la plus courte | 21,8 % | 25 % |
| Écart moyen aux distracteurs | +0,8 caractère | 0 |
| Rangs 1 / 2 / 3 / 4 | 26,9 / 24,4 / 24,4 / 24,4 % | 25 % chacun |

### Deux contraintes à respecter en éditant

- **Ne pas mélanger l'ordre des propositions**, ni dans le code ni à la main :
  quelques explications s'y réfèrent (« la 1ʳᵉ proposition décrit le `state` »).
  Le QCM ne mélange que l'ordre des questions. Si une proposition doit être
  déplacée, vérifier l'explication de la question concernée.
- **Ne pas rallonger une bonne réponse** pour la clarifier : la justification va
  dans le champ `e`, jamais dans la réponse. C'est exactement le biais que
  l'audit traque.

## Publication

Le dépôt est servi par GitHub Pages sur `arthurponcin.me`. Un push sur `main`
met le site en ligne, il n'y a pas d'étape de build côté serveur : les `.html`
générés sont versionnés.
