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
- Le gestionnaire écrit *Fo*.

Conséquences pratiques:

- Il n'est pas possible durant l'édition de modifier *Ce*, par exemple rajouter un nouveau type de label avec sa
  couleur.
- Le gestionnaire peut se réduire à un simple gestionnaire de fichiers. On peut le couper pendant l'édition sans gêner.

## Contraintes techniques

- L'éditeur ne sera utilisé que sur des PC de bureau. On peut donc se réduire aux résolutions d'écran >= 1024x768 (XGA).
  On peut également supposer la présence d'une souris standard, par exemple pour faire des actions sur click long ou
  bouton droit.

# Formats de fichiers

# Configuration

La configuration est une donnée au format JSON.

# Fiche

La fiche est au format HTML5. La correspondance entre les différentes parties de la fiche est résumée ci-dessous:

| Bloc     | Document             | Obligatoire |
|----------|----------------------|-------------|
| Metadata | data-* dans `<body>` | Oui         |
|          |                      |             |
|          |                      |             |
|          |                      |             |
|          |                      |             |
|          |                      |             |
|          |                      |             |
|          |                      |             |
