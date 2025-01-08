## 1. For run WEB need to create in root project dir the file .env with content (past your parameters)

\# Django Settings<br>
DATABASE_ENGINE=django.db.backends.mysql <br>
DATABASE_NAME=translit<br>
DATABASE_USER=user<br>
DATABASE_PASSWORD=password<br>
DATABASE_HOST=localhost<br>
DATABASE_PORT=3306<br>
SECRET_KEY='django-insecure-blablablabla'<br>
DEBUG=True<br>
ALLOWED_HOSTS=127.0.0.1,localhost<br>
CSRF_TRUSTED_ORIGINS=http://localhost<br>

\# Bot-specific settings<br>
BOT_TOKEN="token"

## 2. For build desktop app use command<br>

pyinstaller --onefile --windowed --collect-all django --name desktop_app desktop_app.py