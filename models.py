from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Определяем типы пользователей
class UserRole:
    CLIENT = 'client'
    LAWYER = 'lawyer'
    MANAGER = 'manager'

# Таблица связи между консультациями и документами
consultation_documents = db.Table('consultation_documents',
    db.Column('consultation_id', db.Integer, db.ForeignKey('consultation.id')),
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'))
)

# Модель пользователя (базовая для всех ролей)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_active = db.Column(db.DateTime, default=datetime.now)
    
    # Профиль клиента (отношение один-к-одному)
    client_profile = db.relationship('ClientProfile', backref='user', uselist=False)
    
    # Профиль юриста (отношение один-к-одному)
    lawyer_profile = db.relationship('LawyerProfile', backref='user', uselist=False)
    
    # Назначенные задачи (для юристов)
    assigned_tasks = db.relationship('Task', backref='assigned_to', foreign_keys='Task.assigned_to_id')
    
    # Созданные задачи (для менеджеров)
    created_tasks = db.relationship('Task', backref='created_by', foreign_keys='Task.created_by_id')
    
    # Полное имя пользователя
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    # Установка пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # Проверка пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Является ли клиентом
    @property
    def is_client(self):
        return self.role == UserRole.CLIENT
    
    # Является ли юристом
    @property
    def is_lawyer(self):
        return self.role == UserRole.LAWYER
    
    # Является ли менеджером
    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER

# Профиль клиента
class ClientProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    company_name = db.Column(db.String(200))
    contract_number = db.Column(db.String(50))
    contract_date = db.Column(db.Date)
    hourly_rate = db.Column(db.Float)  # Стоимость часа работы
    monthly_hours = db.Column(db.Float)  # Количество часов в абонементе
    
    # Связь с консультациями
    consultations = db.relationship('Consultation', backref='client')
    
    # Связь с договорами
    contracts = db.relationship('Contract', backref='client')
    
    # Связь с биллингом
    billing_entries = db.relationship('BillingEntry', backref='client')

# Профиль юриста
class LawyerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    biography = db.Column(db.Text)
    
    # Связь с консультациями
    consultations = db.relationship('Consultation', backref='lawyer')

# Отрасли права
class LegalCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Консультации по отрасли права
    consultations = db.relationship('Consultation', backref='category')

# Консультации
class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profile.id'))
    lawyer_id = db.Column(db.Integer, db.ForeignKey('lawyer_profile.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('legal_category.id'))
    topic = db.Column(db.String(200), nullable=False)
    request = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    status = db.Column(db.String(50), default='открыта')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    time_spent = db.Column(db.Float, default=0)  # Затраченное время в часах
    assigned_at = db.Column(db.DateTime)  # Время взятия в работу
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Кто взял в работу (юрист)
    
    # Связь с документами (многие-ко-многим)
    documents = db.relationship('Document', secondary=consultation_documents, backref='consultations')
    
    # Связь с сообщениями
    messages = db.relationship('Message', backref='consultation')
    
    # Связь с биллингом
    billing_entries = db.relationship('BillingEntry', backref='consultation')

# Сообщения в консультации
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Связь с отправителем
    sender = db.relationship('User')

# Документы
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # Размер в байтах
    upload_date = db.Column(db.DateTime, default=datetime.now)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    
    # Связь с пользователем, загрузившим документ
    uploaded_by = db.relationship('User')

# Задачи для юристов
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client_profile.id'))
    status = db.Column(db.String(50), default='новая')
    priority = db.Column(db.String(20), default='средний')
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Связь с клиентом
    client = db.relationship('ClientProfile', backref='tasks')

# Договоры клиентов
class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profile.id'))
    contract_number = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    payment_type = db.Column(db.String(20), default='hourly')  # 'hourly' или 'subscription'
    hourly_rate = db.Column(db.Float, nullable=False)
    monthly_hours = db.Column(db.Float)  # Необязательно для почасовой оплаты
    terms = db.Column(db.Text)
    status = db.Column(db.String(50), default='активный')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Связь с документами
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    document = db.relationship('Document')

# Биллинг
class BillingEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profile.id'))
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'))
    lawyer_id = db.Column(db.Integer, db.ForeignKey('lawyer_profile.id'))
    hours = db.Column(db.Float, nullable=False)  # Затраченное время в часах
    rate = db.Column(db.Float, nullable=False)  # Стоимость часа
    service_name = db.Column(db.String(200))  # Наименование услуги
    description = db.Column(db.Text)
    date = db.Column(db.Date, default=datetime.now().date)
    billed = db.Column(db.Boolean, default=False)
    paid = db.Column(db.Boolean, default=False)
    is_clarification = db.Column(db.Boolean, default=False)  # Является ли уточнением
    
    # Связь с юристом
    lawyer = db.relationship('LawyerProfile', backref='billing_entries')
    
    # Расчет стоимости услуги
    @property
    def amount(self):
        return self.hours * self.rate

# Мероприятия календаря
class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Связь с создателем
    created_by = db.relationship('User', backref='created_events')
    
    # Связь с участниками (многие-ко-многим)
    participants = db.relationship('User', secondary='event_participants')

# Таблица связи между мероприятиями и участниками
event_participants = db.Table('event_participants',
    db.Column('event_id', db.Integer, db.ForeignKey('calendar_event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

# Email рассылка
class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now)
    sent_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Связь с отправителем
    sent_by = db.relationship('User')
    
    # Связь с получателями (многие-ко-многим)
    recipients = db.relationship('User', secondary='newsletter_recipients')

# Таблица связи между рассылками и получателями
newsletter_recipients = db.Table('newsletter_recipients',
    db.Column('newsletter_id', db.Integer, db.ForeignKey('newsletter.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)
