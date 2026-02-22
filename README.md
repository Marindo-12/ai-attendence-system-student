# Face Recognition Attendance System (Flask + SQLite)

Application de presence avec reconnaissance faciale et 2 dashboards:
- Dashboard Professeur: demarrer/arreter une seance, camera active, marquage presence.
- Dashboard Etudiant: voir son statut (`present` / `absent`).

## Fonctionnalites ajoutees
- Formulaire inscription: `nom`, `prenom`, `email`, `password`, `role`, `images (1 a 5 pour etudiant)`.
- Base de donnees reelle SQLite: `attendance.db`.
- Gestion des roles: `professor` et `student`.
- Seances:
  - Le professeur demarre la seance.
  - Le systeme camera envoie des captures au backend.
  - Si reconnu: statut `present` en base.
  - A la fin de seance: les etudiants non reconnus deviennent `absent`.

## Structure
- `app.py`: backend Flask + DB + API reconnaissance.
- `templates/`: pages login/register/prof/student.
- `static/style.css`: style dashboards.
- `Images/`: images de reference etudiants (utilisees par DeepFace).
- `attendance.db`: base SQLite creee au premier lancement.

## Installation
```bash
python -m venv venv
venv\Scripts\activate
pip install flask deepface opencv-python werkzeug
```

## Execution
```bash
python app.py
```
Puis ouvrir:
- `http://127.0.0.1:5000/register` pour creer les comptes.
- `http://127.0.0.1:5000/login` pour se connecter.

## Notes importantes
- En production, changer `SECRET_KEY` dans `app.py`.
- La reconnaissance depend de la qualite/luminosite des images de reference.
- Pour un etudiant, uploader entre 1 et 5 images au moment de l'inscription.
