from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
from typing import Any, Dict

repo_dir = Path(__file__).resolve().parent

def _build_db_uri() -> str:
    if os.environ.get('FLASK_ENV') == 'testing':
        return 'sqlite:///:memory:'

    if os.environ.get('USE_SQLITE', 'false').lower() == 'true':
        return f"sqlite:///{(repo_dir / 'flowershop.db').as_posix()}"

    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'rootpassword')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'flowershop')

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

vars: Dict[str, Any] = {
    'APP_HOSTNAME': os.environ.get('APP_HOSTNAME', 'http://localhost'),
    'APP_PORT': int(os.environ.get('APP_PORT', 5000)),
    'FLASK_ENV': os.environ.get('FLASK_ENV'),
    'USE_SQLITE': os.environ.get('USE_SQLITE', 'False').lower(),
    'DB_USER': os.environ.get('DB_USER', 'root'),
    'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'rootpassword'),
    'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
    'DB_PORT': os.environ.get('DB_PORT', '3306'),
    'DB_NAME': os.environ.get('DB_NAME', 'flowershop'),
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'super-secret-flower-key'),
    'BANK_API_URL': os.environ.get(
        'BANK_API_URL',
        'http://localhost:5001/api'
    ),
    'SQLALCHEMY_DATABASE_URI': _build_db_uri(),
}