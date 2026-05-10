# Méthodologie ML — Nexus-Diagnostix

## Modèles utilisés

### 1. Prédiction de non-conformité à 12 mois

- **Algorithme** : `RandomForestClassifier`
- **Hyperparamètres** : `n_estimators=300`, `max_depth=8`, `class_weight='balanced'`
- **Justification** : robuste sur petits datasets tabulaires hétérogènes (Breiman 2001)
- **Features** (24) : 20 réponses encodées + 4 méta (taille, secteur, score_fiscale, score_sociale)
- **Cible** : binaire (1 = redressement CNPS/DGI dans les 12 mois)
- **Seuils CI** : `ROC-AUC ≥ 0.82`, `F1 ≥ 0.75`

### 2. Prédiction du turnover

- **Algorithme** : `GradientBoostingRegressor`
- **Hyperparamètres** : `n_estimators=200`, `learning_rate=0.05`, `max_depth=4`
- **Justification** : éprouvé en analytics RH (IBM Watson, Saradhi & Palshikar 2011)
- **Sortie** : probabilité ∈ [0, 1]
- **Seuil CI** : `MAE ≤ 0.08`

### 3. Gap digital

- **Méthode** : distance euclidienne pondérée vs vecteur `IA-NATIVE` (toutes réponses = YES)
- **Pas de ML** — calcul déterministe, 100 % reproductible

## Garde-fous

- Confiance < 0.60 → "Donnée insuffisante"
- Hash du modèle stocké dans chaque rapport (traçabilité)
- Validation croisée 5-fold en CI

## Dataset d'entraînement

- **5 000 lignes synthétiques calibrées expert** par OpenLab Consulting
- Distributions paramétrées par secteur, taille d'entreprise
- Script : `backend/scripts/generate_training_data.py` (Sprint 4)
- Notebook d'entraînement : `backend/notebooks/train_models.ipynb`

Pour des raisons de protection des données clients, **aucune donnée réelle** n'est utilisée pour
l'entraînement initial. Au fil de la production, des données opt-in agrégées et anonymisées
pourront enrichir le réentraînement.
