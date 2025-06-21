# Organisation CSS Segmentée

Ce projet utilise une architecture CSS modulaire avec des fichiers séparés par thématique pour une meilleure maintenabilité.

## Structure des fichiers CSS

### 📱 Fichiers principaux (ordre d'import)

1. **`variables.css`** - Variables CSS, thèmes et couleurs Material Design 3
2. **`base.css`** - Styles de base (reset, typography, éléments globaux)
3. **`layout.css`** - Structure de mise en page (grid, layout principal)
4. **`chat.css`** - Styles spécifiques au chat et messages
5. **`sidebar.css`** - Panneau latéral et upload de fichiers
6. **`qcm.css`** - Interface QCM (modals, questions, résultats)
7. **`dashboard.css`** - Page dashboard et statistiques
8. **`effects.css`** - Effets visuels (ripple, animations)
9. **`utilities.css`** - Classes utilitaires (spacing, colors, etc.)

## 🎨 Contenu de chaque fichier

### `variables.css`
- Variables CSS pour Material Design 3
- Thème clair et sombre
- Couleurs, élévations, bordures
- Variables dynamiques (`--current-*`)

### `base.css`
- Reset CSS minimal
- Typographie de base
- Styles globaux pour body, boutons, liens
- Classes Material Icons

### `layout.css`
- Structure principale de l'application
- Grid layout pour desktop/mobile
- App bar et navigation
- Layouts flex et responsive

### `chat.css`
- Interface de chat
- Messages utilisateur/bot
- Zone de saisie
- Boutons TTS et reply
- Styles Markdown dans les messages

### `sidebar.css`
- Panneau latéral droit
- Upload de fichiers
- Liste des fichiers ingérés
- Sections QCM et révision

### `qcm.css`
- Interface QCM complète
- Modals QCM et résultats
- Questions et options
- Navigation et progression
- Styles responsive

### `dashboard.css`
- Page dashboard
- Graphiques et statistiques
- Cards et métriques
- Layout dashboard

### `effects.css`
- Effet ripple Material Design
- Animations et transitions
- Effets visuels interactifs

### `utilities.css`
- Classes utilitaires Tailwind-like
- Spacing (margin, padding)
- Typographie, couleurs
- Flexbox, display
- Responsive utilities

## 🔧 Utilisation

Les fichiers sont importés dans l'ordre dans `templates/head.html` :

```html
<link rel="stylesheet" href="/static/css/variables.css" />
<link rel="stylesheet" href="/static/css/base.css" />
<!-- ... autres fichiers ... -->
```

## 💡 Avantages

- **Maintenabilité** : Chaque fichier a une responsabilité claire
- **Performance** : Possibilité de lazy-loading par section
- **Collaboration** : Plusieurs développeurs peuvent travailler sans conflit
- **Debugging** : Plus facile de localiser les problèmes CSS
- **Réutilisabilité** : Components CSS modulaires

## 🚀 Migration depuis style.css

L'ancien fichier `style.css` monolithique a été segmenté. Pour basculer :

1. ✅ Remplacer l'import de `style.css` par les imports segmentés
2. ✅ Vérifier que tous les styles sont correctement répartis
3. ✅ Tester l'application sur tous les écrans
4. 🔄 Nettoyer l'ancien `style.css` (optionnel)

## 📋 TODO

- [ ] Ajouter des CSS custom properties pour les animations
- [ ] Optimiser les imports CSS avec des bundles
- [ ] Ajouter un mode de développement avec source maps
- [ ] Documentation des composants CSS
