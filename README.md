# ShareMeal — Python Flask Project

This project combines the Flask/SQLite backend with the supplied ShareMeal/FoodShare pages and static assets.

## Features
- Register and log in (passwords are hashed)
- Add food donations
- Browse live available donations on the home page
- Submit pickup requests for donations
- Admin dashboard to review users, donations and pickup requests
- Food records page and additional informational/demo pages
- SQLite database created automatically on first run

## Run in VS Code (Windows)
1. Extract this ZIP.
2. Open the `ShareMeal_Python_Project` folder in VS Code.
3. Open Terminal in that folder.
4. Create a virtual environment (recommended):
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Start the app:
   ```powershell
   python app.py
   ```
7. Open the local address printed in the terminal (normally http://127.0.0.1:5000).

## Admin demo login
- Email: `admin@sharemeal.com`
- Password: `Admin@123`

Change the demo admin password and Flask secret key before deploying publicly. This is a local college-project setup, not production-hardened.

## Notes
- The original React dashboard files are included in `source_references/shraddha/` for reference. The app runs as Flask/Python; React source is not required to start it.
