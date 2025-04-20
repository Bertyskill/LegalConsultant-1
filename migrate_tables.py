import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Создаем приложение и БД
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

def run_migrations():
    """Выполняем необходимые миграции для базы данных."""
    with app.app_context():
        # Добавляем колонку service_name напрямую
        try:
            print("Добавляем колонку service_name в таблицу billing_entry...")
            db.session.execute(text("ALTER TABLE billing_entry ADD COLUMN service_name VARCHAR(200)"))
            db.session.commit()
            print("Колонка service_name успешно добавлена")
        except Exception as e:
            if "already exists" in str(e):
                print("Колонка service_name уже существует")
            else:
                print(f"Ошибка при добавлении колонки service_name: {e}")
            db.session.rollback()
                
        # Добавляем колонку is_clarification напрямую
        try:
            print("Добавляем колонку is_clarification в таблицу billing_entry...")
            db.session.execute(text("ALTER TABLE billing_entry ADD COLUMN is_clarification BOOLEAN DEFAULT FALSE"))
            db.session.commit()
            print("Колонка is_clarification успешно добавлена")
        except Exception as e:
            if "already exists" in str(e):
                print("Колонка is_clarification уже существует")
            else:
                print(f"Ошибка при добавлении колонки is_clarification: {e}")
            db.session.rollback()
                
        print("Миграции успешно выполнены")

if __name__ == '__main__':
    run_migrations()
    sys.exit(0)