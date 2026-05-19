# WC 2026 Prediction Challenge (Python)

This is a Python/Flask conversion of your HTML prediction interface, with a shared SQLite backend so all colleagues see the same leaderboard.

## 1) Setup

```powershell
cd "c:\Users\ruiz pablo\OneDrive - The Boston Consulting Group, Inc\Documents\Miscellaneous\RedBull Wingfinder\wc2026_python_app"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Run locally

```powershell
python app.py
```

Open: `http://127.0.0.1:5000`

## 3) Run tests

```powershell
python -m unittest discover -s tests
```

## 4) Share with colleagues on your network

Run the app on all interfaces:

```powershell
python app.py
```

Then colleagues on same network can use:

`http://YOUR_LOCAL_IP:5000`

Find your IP in PowerShell:

```powershell
ipconfig
```

## 5) More stable serving (optional)

```powershell
waitress-serve --host 0.0.0.0 --port 5000 app:app
```

## 6) Deploy to Render

Render can deploy this app directly from the repo.

### Required environment variables

- `ADMIN_PASSWORD`: password for the `/admin` page
- `SECRET_KEY`: long random string for Flask session security
- `DB_PATH`: path to the SQLite file on a persistent Render disk, for example `/var/data/predictions.db`

### Important storage note

SQLite only works on Render if you attach a persistent disk. If you do not mount a disk, `predictions.db` can be lost on redeploy or restart.

Recommended Render disk mount path:

- Mount path: `/var/data`
- `DB_PATH=/var/data/predictions.db`

### Render setup steps

1. Push this project to GitHub.
2. In Render, create a new Web Service from that GitHub repo.
3. Set the build command to `pip install -r requirements.txt`.
4. Set the start command to `waitress-serve --host=0.0.0.0 --port=$PORT app:app`.
5. Add a persistent disk mounted at `/var/data`.
6. Add the environment variables above in Render.
7. Deploy.

If you use the included `render.yaml`, Render can prefill the service settings, env vars, health check, and persistent disk automatically.

### Optional post-deploy checks

- App home: `/`
- Admin page: `/admin`
- Health check: `/health`

## Notes

- Data is stored in `data/predictions.db`.
- Saving picks for the same email updates that player's latest prediction and score.
- Current score is based on completed picks (group + knockout picks), same as your original app logic.
- Admin access is available at `/admin`. Set `ADMIN_PASSWORD` before starting the app so only you can view all submissions.
- For deployment, also set `SECRET_KEY` to a long random value so admin sessions are protected.
