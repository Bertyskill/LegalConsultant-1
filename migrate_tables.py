import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from models import db, BillingEntry

# Создаем приложение
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db.init_app(app)

def run_migrations():
    """Выполняем необходимые миграции для базы данных."""
    with app.app_context():
        try:
            # Проверяем наличие колонки service_name в таблице billing_entry
            db.session.execute(text("SELECT service_name FROM billing_entry LIMIT 1"))
            print("Колонка service_name уже существует в таблице billing_entry")
        except Exception as e:
            if "column billing_entry.service_name does not exist" in str(e):
                print("Добавляем колонку service_name в таблицу billing_entry...")
                db.session.execute(text("ALTER TABLE billing_entry ADD COLUMN service_name VARCHAR(200)"))
                db.session.commit()
                print("Колонка service_name успешно добавлена")
            else:
                print(f"Ошибка при проверке колонки service_name: {e}")
                
        try:
            # Проверяем наличие колонки is_clarification в таблице billing_entry
            db.session.execute(text("SELECT is_clarification FROM billing_entry LIMIT 1"))
            print("Колонка is_clarification уже существует в таблице billing_entry")
        except Exception as e:
            if "column billing_entry.is_clarification does not exist" in str(e):
                print("Добавляем колонку is_clarification в таблицу billing_entry...")
                db.session.execute(text("ALTER TABLE billing_entry ADD COLUMN is_clarification BOOLEAN DEFAULT FALSE"))
                db.session.commit()
                print("Колонка is_clarification успешно добавлена")
            else:
                print(f"Ошибка при проверке колонки is_clarification: {e}")
                
        print("Миграции успешно выполнены")

if __name__ == '__main__':
    run_migrations()
    sys.exit(0)