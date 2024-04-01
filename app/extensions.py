from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.secret_key = 'your_secret_key_here'  # Установите секретный ключ
db = SQLAlchemy(app)