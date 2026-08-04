# Architecture et design patterns

*Fiche transversale 2/6 — les choix de structure, les patterns réellement implémentés, et comment les défendre.*
{: .meta }

## 0. Vocabulaire à connaître avant de lire

Design pattern
:   Solution **réutilisable** à un problème de conception récurrent. Ce n'est pas du code : c'est un schéma de collaboration entre classes. Les 23 patterns du « Gang of Four » se répartissent en créationnels (Factory, Singleton, Builder), structurels (Adapter, Facade, Decorator, Proxy) et comportementaux (Strategy, Observer, Template Method, Command).

Couplage / cohésion
:   **Couplage** = degré de dépendance entre modules (on le veut faible). **Cohésion** = degré de rapport entre les responsabilités d'un même module (on la veut forte). L'objectif permanent : couplage faible, cohésion forte. Tous les patterns servent à ça.

Monolithe / microservices
:   Un **monolithe** est une seule unité déployable. Des **microservices** sont des unités déployables indépendamment, chacune avec sa propre base et son cycle de vie. Entre les deux : le **monolithe modulaire** (un déploiement, des modules étanches) et le **monorepo** (un dépôt, plusieurs services déployés séparément) — deux notions qu'on confond souvent.

Monorepo
:   Un **dépôt Git unique** contenant plusieurs services. C'est une décision d'organisation du code, pas d'architecture d'exécution : un monorepo peut héberger des microservices, et un multi-repo peut héberger un monolithe.

Inversion de dépendance
:   Le « D » de SOLID. Les modules de haut niveau ne dépendent pas des modules de bas niveau : les deux dépendent d'**abstractions**. Concrètement, mon moteur de rendu dépend de `AbstractStrategy`, pas de `TableStrategy`.

Injection de dépendance
:   Technique de mise en œuvre de l'inversion : on **passe** à un objet ce dont il a besoin (par constructeur ou paramètre) au lieu qu'il l'instancie lui-même. Ça rend le remplacement en test trivial.

Fat models / thin views
:   Convention Django : la logique métier vit **au plus près des modèles**, les vues se limitent au routage HTTP et à la sérialisation. À l'opposé du « fat controller » qui concentre tout dans la vue.

REST / ressource / verbe
:   Style d'architecture où l'on manipule des **ressources** identifiées par une URL, avec les verbes HTTP standards (`GET` lire, `POST` créer, `PUT`/`PATCH` modifier, `DELETE` supprimer) et des codes de statut normalisés. Sans état côté serveur entre deux requêtes.

BFF (Backend For Frontend)
:   Un backend dédié à un client donné, qui porte la session et parle aux services en aval. Chez moi, l'API Django joue ce rôle vis-à-vis du SSO : elle détient la session, les tokens du fournisseur d'identité ne descendent jamais au navigateur.

Feature-based architecture
:   Découpage du code **par domaine métier** (`features/editor/`, `features/photo-appendix/`) plutôt que par type technique (`components/`, `hooks/`, `api/`). Chaque feature porte sa propre pile complète.

Idempotence
:   Une opération est idempotente si l'exécuter n fois produit le même résultat qu'une fois. `GET`, `PUT` et `DELETE` sont idempotents en REST ; `POST` ne l'est pas.

---

## 1. TL;DR

Trois décisions structurantes portent l'ensemble de mon travail :

1. **Une architecture orientée services dans un monorepo.** L'authentification a été sortie de Django dès le départ, mais tout est resté dans un seul dépôt. Compromis assumé : cloisonnement logique sans le coût opérationnel de vrais microservices.
2. **Un refactoring de fond après la V1.** Un `views.py` de 586 lignes et un moteur de rendu de ~500 lignes ont été redécoupés en applications Django distinctes, et la cascade de `if type == ...` remplacée par un **Strategy Pattern** avec factory.
3. **Une architecture feature-based côté front.** Chaque domaine métier isolé sous `features/`, sans import croisé hors point d'entrée explicite (ADR-005).

!!! jury "La phrase à retenir"
    Aucun de ces choix n'a été fait au démarrage « parce que c'est la bonne pratique ». Chacun répond à une **douleur mesurée** : un fichier trop long, un bug difficile à localiser, une feature impossible à ajouter sans risque. C'est ça que le jury veut entendre.

---

## 2. Le Strategy Pattern : le cas d'école du dossier

### 2.1 Le problème d'origine

Le moteur de génération Word tenait dans **un seul fichier de près de 500 lignes**, avec une fonction de dispatch centrale `_render_brick` construite comme une cascade de conditions :

```python
# État initial (avant refactoring) — schéma reconstitué
def _render_brick(subdoc, brick, resolver):
    if brick["type"] == "heading":
        ...25 lignes...
    elif brick["type"] == "paragraph":
        ...18 lignes...
    elif brick["type"] == "list":
        ...30 lignes...
    elif brick["type"] == "table":
        ...80 lignes...
    elif brick["type"] == "image":
        ...
```

Trois défauts concrets :

- Ajouter un type de bloc **modifie une fonction que tous les autres types traversent** — violation du principe ouvert/fermé.
- Localiser un bug de rendu de tableau oblige à descendre 200 lignes de conditions.
- Tester un seul type de bloc impose de passer par la fonction entière.

### 2.2 La solution implémentée

Chaque type de bloc devient une **classe** avec sa propre méthode de rendu, derrière une interface commune.

```python
# generator/brick_strategies/base.py
from abc import ABC, abstractmethod
from typing import Any

from .styles import StyleResolver


class AbstractStrategy(ABC):
    """Classe de base pour toutes les stratégies de rendu de briques."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    @abstractmethod
    def execute(self, subdoc, resolver: StyleResolver) -> None:
        """Insère le contenu de la brique dans le sous-document Word."""
```

Une **factory** fait la correspondance type → classe. C'est un simple dictionnaire, ce qui suffit :

```python
# generator/brick_strategies/factory.py
class BrickFactory:
    """Factory qui instancie la bonne stratégie selon le type de brique."""

    _strategies: dict[str, type[AbstractStrategy]] = {
        "text": ParagraphStrategy,
        "paragraph": ParagraphStrategy,
        "heading": HeadingStrategy,
        "list": ListStrategy,
        "callout": CalloutStrategy,
        "page_break": PageBreakStrategy,
        "image": ImageStrategy,
        "table": TableStrategy,
    }

    @classmethod
    def create(cls, data: dict[str, Any]) -> AbstractStrategy | None:
        strategy_class = cls._strategies.get(data.get("type"))
        return strategy_class(data) if strategy_class else None
```

Et le **runner** ne connaît plus aucun type de bloc :

```python
# generator/brick_strategies/runner.py
def render_bricks(tpl, bricks: Sequence[dict[str, Any]]):
    """Crée un sous-document, itère sur les briques, délègue aux stratégies."""
    sd = tpl.new_subdoc()
    resolver = StyleResolver(sd.part.document)

    for brick_data in bricks:
        strategy = BrickFactory.create(brick_data)
        if strategy:
            strategy.execute(sd, resolver)

    return sd
```

!!! jury "Ce que ça change, concrètement"
    Ajouter un type de bloc = créer une classe + une ligne dans le dictionnaire. **Aucun code existant n'est modifié.** C'est la définition du principe ouvert/fermé : ouvert à l'extension, fermé à la modification. Et chaque stratégie se teste isolément, sans monter un document complet.

### 2.3 Strategy ou Factory ? Les deux

Question de jury quasi certaine. Il y a **deux patterns** dans ce code :

- **Strategy** (comportemental) : la famille d'algorithmes interchangeables derrière `AbstractStrategy`.
- **Factory** (créationnel) : `BrickFactory`, qui décide **quelle** stratégie instancier à partir de la donnée.

Ils sont complémentaires : Strategy résout « comment rendre », Factory résout « qui doit rendre ». Sans la factory, le choix de la stratégie serait revenu dans le runner sous forme de conditions — on aurait juste déplacé le problème.

!!! note "Le StyleResolver, un Adapter"
    Troisième pattern présent, souvent oublié à l'oral. Le `StyleResolver` fait le lien entre les noms de styles **attendus par l'application** et ceux réellement **présents dans le template Word**, via une table d'alias. C'est un **Adapter** : il permet de supporter plusieurs templates, nommant leurs styles différemment, sans toucher au code de génération.

---

## 3. Architecture feature-based côté front (ADR-005)

### 3.1 Avant / après

| Avant (par type technique) | Après (par domaine) |
|---|---|
| `components/` — 40+ fichiers à plat | `features/editor/` |
| `hooks/` | `features/editor-v2/` |
| `api/` — un client de 400 lignes | `features/photo-appendix/` |
| `types/` | `features/reports/`, `auth/`, `admin/`, `analytics/`, `onboarding/` |

Chaque feature porte **sa pile complète** :

```
features/photo-appendix/
├── api/          # queries et mutations TanStack Query
├── components/   # composants React du domaine
├── hooks/        # logique réutilisable du domaine
├── types/        # types TypeScript du domaine
├── utils/
└── index.ts      # point d'entrée public — la seule surface exposée
```

### 3.2 La règle qui fait tenir l'ensemble

> Les composants d'une feature n'importent pas ceux d'une autre, **sauf à travers un point d'entrée explicite** (`index.ts`).

C'est ce qui distingue une vraie architecture modulaire d'un simple rangement de dossiers. Le reste vit dans :

- `components/ui/` — primitives partagées (shadcn/ui, sans logique métier) ;
- `lib/` — utilitaires transverses (client axios, helpers) ;
- `app/` — providers et configuration globale.

Le canvas de l'éditeur, qui rendait tous les types de blocs dans un seul composant, a été **éclaté : une brique = un fichier**. Le client API monolithique de 400 lignes a été découpé en queries et mutations rattachées à leur feature.

!!! jury "Le lien avec le SRP"
    C'est le principe de responsabilité unique appliqué à l'échelle du module : **chaque module a une seule raison de changer**. Un changement dans les annexes photo ne touche aucun fichier de l'éditeur. Bénéfice mesurable : les annexes photo, développées *après* le refactoring, ont été livrées nettement plus vite que ce qu'aurait permis l'ancienne organisation.

---

## 4. SOLID, avec des exemples issus du code

| Principe | Énoncé | Où c'est appliqué |
|---|---|---|
| **S** — Responsabilité unique | Une classe/module a une seule raison de changer | Découpage en 5 apps Django ; une feature front = un domaine ; une stratégie = un type de bloc |
| **O** — Ouvert/fermé | Ouvert à l'extension, fermé à la modification | `BrickFactory` : nouveau bloc = nouvelle classe, zéro modification |
| **L** — Substitution de Liskov | Toute sous-classe doit pouvoir remplacer sa classe de base | Toutes les stratégies respectent la signature `execute(subdoc, resolver)` : le runner ne fait aucun cas particulier |
| **I** — Ségrégation des interfaces | Mieux vaut plusieurs interfaces spécifiques qu'une seule générale | `AbstractStrategy` n'expose **qu'une** méthode. Rien à implémenter inutilement |
| **D** — Inversion de dépendance | Dépendre d'abstractions, pas d'implémentations | `render_bricks` dépend de `AbstractStrategy`, jamais de `TableStrategy` |

!!! piege "Ne pas réciter SOLID à vide"
    Le jury repère immédiatement la récitation. La bonne réponse contient toujours *« dans mon code, à tel endroit, ça donne ça »*. Si on ne peut pas donner l'exemple, mieux vaut ne pas citer le principe.

---

## 5. Monorepo, services, microservices

### 5.1 Le choix de départ sur Boost-Report

L'authentification a été sortie de Django dans un **service séparé** (Bun + Hono + Better-Auth + Drizzle) alors que Django embarque une auth complète. Pourquoi ?

- Isoler l'authentification du reste et garder les couches métier indépendantes.
- Préparer la montée en charge : chaque service évolue de son côté.
- Front **et** API s'adressent tous deux à ce service ; l'API valide les jetons via un **secret partagé**.

Mais tout est resté dans un **monorepo** : un seul dépôt, un seul `docker-compose` pour tout lancer, des services cloisonnés. C'est le compromis qui évite de s'enfermer dans un monolithe sans payer le coût opérationnel de vrais microservices (déploiements indépendants, versionnement d'API, observabilité distribuée).

### 5.2 Ce que le passage au hub a changé

Quand SXE-Hub est devenu le **fournisseur d'identité** de toute la suite, l'auth-service propre à Boost-Report a été **retiré**. L'architecture s'est simplifiée : de quatre images construites (base, auth, API, front) à **deux** (API Django, front), la base ayant migré vers PostgreSQL managé.

!!! jury "Savoir dire qu'on a supprimé du code"
    C'est le point fort de cette histoire. Le service d'auth était un bon choix au moment où il a été fait — il isolait une responsabilité sensible et permettait d'avancer. Quand le contexte a changé (un IdP centralisé à l'échelle de la suite), le maintenir serait devenu de la duplication. Retirer un composant qu'on a écrit soi-même est une décision d'architecture au même titre que l'ajouter.

### 5.3 Monolithe vs microservices — le tableau à connaître

| | Monolithe | Microservices |
|---|---|---|
| Déploiement | Une unité, simple | n unités, orchestration nécessaire |
| Scalabilité | Globale (on duplique tout) | Ciblée (on scale le service saturé) |
| Couplage | Fort par défaut, à discipliner | Faible par contrat, fort si mal découpé |
| Transactions | ACID natives | Distribuées (saga, compensation) — difficile |
| Observabilité | Logs locaux | Tracing distribué obligatoire |
| Coût d'entrée | Faible | Élevé (CI/CD, réseau, monitoring, versionnement) |
| Adapté à | Petite équipe, domaine peu stabilisé | Grande équipe, domaines matures et indépendants |

Pour un développeur seul dans une agence, le monolithe modulaire est le bon choix par défaut. Le seul service que j'ai réellement isolé est celui dont la responsabilité était la plus **clairement délimitée et la plus sensible** : l'authentification.

---

## 6. L'API REST

### 6.1 Les principes appliqués

- **Ressources nommées au pluriel** : `/api/reports/`, `/api/photo-appendices/`, `/api/agencies/`.
- **Verbes HTTP porteurs de sens** : la sémantique est dans la méthode, pas dans l'URL (jamais `/api/deleteReport`).
- **Sans état** : chaque requête porte de quoi être authentifiée (cookie de session first-party) ; le serveur ne garde pas de contexte de conversation.
- **Codes de statut normalisés** : 200/201 succès, 400 requête invalide, 401 non authentifié, 403 authentifié mais non autorisé, 404 introuvable, 429 throttlé.

!!! piege "401 contre 403"
    **401 Unauthorized** = « je ne sais pas qui tu es » (pas de session valide) → le front redirige vers le login OIDC. **403 Forbidden** = « je sais qui tu es, tu n'as pas le droit » → on affiche une erreur. Dans mon code, `OIDCSessionAuthentication` surcharge `authenticate_header` **exactement pour ça** : sans ce header, DRF répondrait 403 aux requêtes anonymes et le SPA ne saurait pas qu'il faut relancer le login.

### 6.2 REST vs GraphQL vs RPC

| | REST | GraphQL | RPC / gRPC |
|---|---|---|---|
| Unité | Ressource | Requête typée sur un schéma | Appel de procédure |
| Sur/sous-fetching | Fréquent | Résolu par construction | Selon le contrat |
| Cache HTTP | Natif | Difficile (tout en POST) | Non |
| Complexité serveur | Faible | Élevée (resolvers, N+1, profondeur) | Moyenne |

REST était le bon choix : le domaine est simple (CRUD + génération), Django REST Framework fournit sérialisation, permissions, pagination et throttling en standard, et le cache HTTP fonctionne sans effort.

---

## 7. Les autres patterns présents dans le code

| Pattern | Où | Rôle |
|---|---|---|
| **Strategy** | `brick_strategies/` | Un algorithme de rendu par type de bloc |
| **Factory** | `BrickFactory` | Instancie la bonne stratégie depuis la donnée |
| **Adapter** | `StyleResolver`, `weasyprint_adapter.py` | Réconcilie deux vocabulaires (styles applicatifs ↔ styles du template Word) |
| **Facade** | `ReportPdfService`, `photo_appendix_service.py` | Une entrée simple devant une chaîne complexe (cache → génération → conversion) |
| **Policy object** | `ReportPermissionPolicy` | Centralise les règles d'autorisation hors des vues |
| **Mixin** | `VisibilityFilterMixin` | Compose le filtrage de visibilité dans plusieurs ViewSets |
| **Repository (via ORM)** | Managers Django | Encapsule l'accès aux données ; aucun SQL manuel |
| **Template Method** | `AbstractStrategy` | Le squelette est fixé par la base, le détail par les sous-classes |

!!! note "Le pattern le plus utile à citer après Strategy"
    Le **policy object**. `ReportPermissionPolicy.can_edit(user, report)` sort la règle métier « qui a le droit d'éditer » de la vue **et** du modèle. Résultat : la règle est testable en isolation, et surtout elle est écrite **une fois** — les permissions DRF, le filtrage de queryset et l'accès aux fichiers média consomment tous la même source de vérité. Une règle d'autorisation dupliquée finit toujours par diverger, et c'est comme ça qu'on crée une faille.

---

## 8. Questions probables du jury

### Q1. Pourquoi le Strategy Pattern plutôt qu'un simple dictionnaire de fonctions ?

Un dictionnaire `type → fonction` aurait résolu le dispatch, c'est vrai. Mais les stratégies portent un **état** (`self.data`) et partagent une interface qui permet d'ajouter du comportement commun : validation, gestion d'erreur, hooks avant/après rendu. Avec des fonctions nues, il aurait fallu passer les données en paramètre à chaque appel et dupliquer toute logique transverse. Cela dit, si le besoin s'était limité à « un type, une fonction sans état », le dictionnaire de fonctions aurait été le bon choix — un pattern n'est justifié que par la complexité qu'il absorbe.

### Q2. Votre architecture microservices n'en est pas vraiment une, si ?

Non, et je ne la présente pas comme telle. C'était une **architecture orientée services dans un monorepo** : deux services au sens exécution (l'auth et l'API), un seul dépôt, un seul `docker-compose`. Ça m'a donné le cloisonnement — l'API ne connaît de l'auth que son contrat — sans le coût des vrais microservices : déploiements indépendants, versionnement d'API, tracing distribué. Pour un développeur seul, payer ce coût aurait été de la sur-ingénierie. Et l'histoire l'a confirmé : quand le hub est devenu l'IdP de la suite, j'ai pu retirer le service d'auth sans rien casser ailleurs, précisément parce que le contrat était propre.

### Q3. Le refactoring, ce n'est pas du temps perdu pour le client ?

C'est un investissement qui s'est payé sur le sprint suivant. Concrètement : le `views.py` faisait 586 lignes, le moteur de rendu ~500, le client API front 400. Ajouter une fonctionnalité imposait de toucher des fichiers qui géraient déjà trop de choses, et localiser un bug demandait de remonter des chaînes de conditions. La fonctionnalité d'annexes photo a été développée **après** le refactoring, dans son propre espace côté front comme côté back, sans interférer avec l'éditeur existant. Elle a été livrée nettement plus vite que ce qu'aurait permis l'ancienne base. Le vrai risque n'est pas le refactoring, c'est de le faire trop tard.

### Q4. Comment savez-vous qu'un fichier est « trop long » ?

Le nombre de lignes est un symptôme, pas le critère. Le vrai critère est le **nombre de raisons de changer**. Mon `views.py` mélangeait routage HTTP, logique métier et génération de documents : trois raisons de changer indépendantes, donc trois modules. À l'inverse `models.py` fait 900 lignes et je ne l'ai pas découpé, parce qu'il n'a qu'une raison de changer — l'évolution du domaine — et que le découper disperserait des entités qui se référencent mutuellement.

### Q5. Pourquoi feature-based et pas une architecture hexagonale ou Clean Architecture ?

L'hexagonale a un intérêt réel quand on veut pouvoir remplacer les adaptateurs d'infrastructure : changer de SGBD, exposer le même domaine en REST et en CLI, tester le métier sans aucune I/O. Aucun de ces besoins ne se posait ici : un seul SGBD, une seule interface, un domaine qui n'a pas de règles complexes indépendantes de la persistance. Le coût — ports, adaptateurs, DTO, mapping dans les deux sens — aurait été payé sans contrepartie. Le feature-based traitait ma douleur réelle, qui était le couplage entre domaines fonctionnels, pas entre domaine et infrastructure.

### Q6. Un `if/elif` sur huit cas, ce n'est pas si grave. Vous n'avez pas sur-conçu ?

C'est la bonne question à se poser et je me la suis posée. Le déclencheur n'est pas le nombre de cas, c'est que chaque branche faisait **20 à 80 lignes** — la fonction dépassait 400 lignes à elle seule et grossissait à chaque type ajouté. Si les branches avaient fait trois lignes chacune, j'aurais laissé le `if/elif` : c'est plus lisible qu'un système de classes. Le seuil, pour moi, c'est le moment où on ne voit plus la structure de la fonction sur un écran.

### Q7. Comment garantissez-vous que la règle « pas d'import entre features » est respectée ?

Aujourd'hui par convention et par revue de code, ce qui est une **limite réelle** que j'assume. La règle est écrite dans l'ADR-005 et chaque feature expose un `index.ts`, mais rien n'empêche techniquement un import direct en profondeur. Le durcissement existe et est identifié : une règle ESLint `no-restricted-imports` interdisant les chemins `features/*/` autres que `index.ts`, ce qui ferait échouer la CI. C'est le genre de garde-fou que j'aurais dû ajouter en même temps que l'ADR — une règle qui n'est pas outillée finit toujours par se relâcher.

### Q8. Vous citez beaucoup de patterns. Lequel regrettez-vous ?

Aucun de ceux qui sont là, mais il en manque un : je n'ai **pas** de machine à états explicite pour le workflow de rédaction (brouillon → relecture → validé). Les règles de transition sont réparties entre les permissions, les vues et le modèle, ce qui les rend difficiles à vérifier d'un coup d'œil. Un objet `ReportWorkflow` centralisant les transitions autorisées serait le prochain refactoring à faire — c'est exactement le même raisonnement que pour `ReportPermissionPolicy`, appliqué à un domaine que je n'ai pas encore traité.
