## Architecture attendue

L'application se compose à minima:

- D'un **gestionnaire** de fiches (côté serveur). Le gestionnaire s'occupe de la partie administrative (liste des
  fiches, utilisateurs, rôles, actions...).
- D'un **éditeur** de fiche (côté navigateur). L'éditeur est ce que l'utilisateur voit pendant la modification d'une
  fiche.

Dans une version simplifiée mais fonctionnelle, le gestionnaire peut simplement envoyer et recevoir des fichiers
ordinaires. Les fichiers de configuration:

- seraient présents sur un serveur de fichiers.
- suivraient un schéma de nommage donné.
- seraient créés et modifiés manuellement.

Exemple: `31190_Zooscan.json` contiendrait la configuration pour la fiche taxo _Cyttarocylis_ du Zooscan.

## Scenario

### Lors de l'édition/création:

- Le gestionnaire va chercher une fiche existante, ou génère une fiche vide (*Fi*).
- Le gestionnaire détermine la configuration d'édition (*Ce*). Par exemple, la liste des labels possibles et leur
  couleur fait partie de la configuration.
- L'éditeur reçoit (ou va chercher) *Fi* + *Ce*, en contrôle la validité et affiche *Fi*.
- L'utilisateur peut alors modifier *Fi*, en étant forcé de respecter la configuration. Pendant cette phase, **aucun
  dialogue avec le gestionnaire n'est nécessaire**.
- Lors de la sauvegarde, l'éditeur génère *Fo* et l'envoie au gestionnaire.
- Le gestionnaire valide et écrit *Fo*.

Conséquences pratiques:

- Il n'est pas possible durant l'édition de modifier *Ce*, par exemple rajouter un nouveau type de label avec sa
  couleur.
- Le gestionnaire peut se réduire à un simple gestionnaire de fichiers. On peut le couper pendant l'édition sans gêner.

## Contraintes techniques

- L'éditeur ne sera utilisé que sur des PC de bureau. On peut donc se réduire aux résolutions d'écran >= 1024x768 (XGA).
  On peut également supposer la présence d'une souris standard, par exemple pour faire des actions sur click long ou
  bouton droit.
- On peut supposer que les dernières versions des navigateurs courants sont utilisés pour l'édition.
- Les blocs SVG sont minimalistes. Par exemple, alors qu'il est possible de faire tourner une flêche avec
  un `transform=(rotate...` , l'éditeur devra plutôt en modifier les extrémités.

# Formats de fichiers

# Configuration

La configuration est une donnée contenant:

{  
"taxoid": _identifiant de l'espèce_  
"instrumentid": _identifiant de l'instrument_  
"labels": _liste associative nom de label->couleur HTML_  
"segments": _liste d'étiquettes de segments_  
}

Pour l'exemple illustré dans le répertoire "static", la configuration permettant la génération aurait été, en JSON:

`{ "taxoid":74144,  
"instrumentid":"Zooscan",  
"labels":{
"protoconch":"blue",
"queue":"red",
"foot":"orchid",
"apex":"darkgray"
},
"segments":[
"body",
"head",
"tail"
]
}`

# Fiche

La fiche est au format HTML5. La correspondance entre les différentes parties de la fiche est résumée ci-dessous:

| Bloc                                  | Document                            |
|---------------------------------------|-------------------------------------|
| Metadata                              | data-* dans `<body>`                |
| Morphological identification criteria | `<article class="morpho-criteria">` |
| Descriptive schemas                   | `<div class="descriptive-schemas">` |
| More examples                         | `<div class="more-examples">`       |
| Photos and Figures                    | `<div class="photos-and-figures">`  |
| Possible Confusions                   | `<div class="possible-confusions">`   |

Les schémas sont au format SVG à l'intérieur des fiches, les primitives utilisés sont:

| Element             | Type SVG                          | 
|---------------------|-----------------------------------|
| Image de base       | `<image>`                         |
| Flêches             | `<line>`                          |
| Forme ronde         | `<circle>`                        |
| Forme 'spline'      | `<path>` restreint                |
| More examples       | `<div class="more-examples">`     |
| Possible Confusions | `<div class="possible-confusions">` |

# Survol du code

On trouvera dans le présent répertoire un code python (`verify.py`) dont le but est de valider
l'exemple `ok_example.html` et d'afficher de nombreuses erreurs sur l'exemple `ko_example.html`.

Le code est incomplet (i.e. il n'affichera aucune erreur sur certains documents invalides) mais constitue une base pour
être intégré (ou ré-implémenté).

Le principe de conception de l'application est que tout document doit être validé avant d'être stocké, i.e. que le
module gestionnaire ne doit pas "faire confiance" au module éditeur de fiche.  
