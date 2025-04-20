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
            
        # Добавляем колонку payment_type в таблицу contract
        try:
            print("Добавляем колонку payment_type в таблицу contract...")
            db.session.execute(text("ALTER TABLE contract ADD COLUMN payment_type VARCHAR(20) DEFAULT 'hourly'"))
            db.session.commit()
            print("Колонка payment_type успешно добавлена")
        except Exception as e:
            if "already exists" in str(e):
                print("Колонка payment_type уже существует")
            else:
                print(f"Ошибка при добавлении колонки payment_type: {e}")
            db.session.rollback()
            
        # Делаем nullable колонку monthly_hours в таблице contract
        try:
            print("Изменяем колонку monthly_hours в таблице contract на nullable...")
            db.session.execute(text("ALTER TABLE contract ALTER COLUMN monthly_hours DROP NOT NULL"))
            db.session.commit()
            print("Колонка monthly_hours успешно изменена")
        except Exception as e:
            print(f"Ошибка при изменении колонки monthly_hours: {e}")
            db.session.rollback()
                
        print("Миграции успешно выполнены")

if __name__ == '__main__':
    run_migrations()
    sys.exit(0)