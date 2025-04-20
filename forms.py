from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, \
    DateField, FloatField, IntegerField, FileField, HiddenField, SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from datetime import datetime, date

# Форма входа
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')

# Форма регистрации
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')]
    )
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[Optional()])
    company_name = StringField('Название компании', validators=[Optional()])

# Форма профиля клиента
class ClientProfileForm(FlaskForm):
    phone = StringField('Телефон', validators=[Optional()])
    current_password = PasswordField('Текущий пароль', validators=[Optional()])
    new_password = PasswordField('Новый пароль', validators=[
        Optional(),
        Length(min=6, message='Пароль должен содержать не менее 6 символов')
    ])
    confirm_password = PasswordField('Повторите новый пароль', validators=[
        Optional(),
        EqualTo('new_password', message='Пароли должны совпадать')
    ])

# Форма профиля юриста
class LawyerProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=6, message='Пароль должен содержать не менее 6 символов')
    ])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')]
    )
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[Optional()])
    specialization = StringField('Специализация', validators=[DataRequired()])
    experience_years = IntegerField('Опыт работы (лет)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Укажите корректное количество лет')
    ])
    biography = TextAreaField('Биография')

# Форма создания/редактирования консультации
class ConsultationForm(FlaskForm):
    category_id = SelectField('Отрасль права', coerce=int, validators=[DataRequired()])
    topic = StringField('Тема', validators=[DataRequired()])
    title = StringField('Заголовок', validators=[DataRequired()])
    request = TextAreaField('Запрос', validators=[DataRequired()])

# Форма загрузки документа
class DocumentForm(FlaskForm):
    file = FileField('Файл', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    consultation_id = HiddenField('ID консультации')

# Форма добавления сообщения
class MessageForm(FlaskForm):
    content = TextAreaField('Сообщение', validators=[DataRequired()])
    consultation_id = HiddenField('ID консультации', validators=[DataRequired()])

# Форма создания задачи
class TaskForm(FlaskForm):
    title = StringField('Название задачи', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    assigned_to_id = SelectField('Назначить юристу', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Клиент', coerce=int, validators=[DataRequired()])
    priority = SelectField('Приоритет', choices=[
        ('низкий', 'Низкий'),
        ('средний', 'Средний'),
        ('высокий', 'Высокий'),
        ('критический', 'Критический')
    ], validators=[DataRequired()])
    due_date = DateField('Срок выполнения', validators=[DataRequired()])

# Форма создания договора
class ContractForm(FlaskForm):
    contract_number = StringField('Номер договора', validators=[DataRequired()])
    start_date = DateField('Дата начала', validators=[DataRequired()])
    end_date = DateField('Дата окончания', validators=[Optional()])
    hourly_rate = FloatField('Стоимость часа (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Стоимость не может быть отрицательной')
    ])
    monthly_hours = FloatField('Количество часов в месяц', validators=[
        DataRequired(),
        NumberRange(min=0, message='Количество часов не может быть отрицательным')
    ])
    terms = TextAreaField('Условия договора', validators=[Optional()])
    document = FileField('Скан договора', validators=[Optional()])

# Форма регистрации биллинга
class BillingEntryForm(FlaskForm):
    hours = FloatField('Затраченное время (часов)', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Минимальное время - 0.1 часа')
    ])
    description = TextAreaField('Описание работы', validators=[DataRequired()])
    consultation_id = HiddenField('ID консультации', validators=[DataRequired()])

# Форма создания мероприятия календаря
class CalendarEventForm(FlaskForm):
    title = StringField('Название мероприятия', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    start_time = DateTimeField('Дата и время начала', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('Дата и время окончания', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    location = StringField('Место проведения', validators=[Optional()])
    participants = SelectMultipleField('Участники', coerce=int, validators=[DataRequired()])

# Форма для рассылки
class NewsletterForm(FlaskForm):
    subject = StringField('Тема письма', validators=[DataRequired()])
    content = TextAreaField('Содержание письма', validators=[DataRequired()])
    all_clients = BooleanField('Отправить всем клиентам')
    recipients = SelectMultipleField('Получатели', coerce=int)

# Форма регистрации клиента (для менеджера)
class ClientRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[Optional()])
    company_name = StringField('Название компании', validators=[Optional()])
    
    # Данные договора
    contract_number = StringField('Номер договора', validators=[Optional()])
    contract_start_date = DateField('Дата начала договора', validators=[Optional()])
    contract_end_date = DateField('Дата окончания договора', validators=[Optional()])
    hourly_rate = FloatField('Стоимость часа (руб.)', validators=[Optional()])
    monthly_hours = FloatField('Количество часов в месяц', validators=[Optional()])

# Форма поиска
class SearchForm(FlaskForm):
    query = StringField('Поисковый запрос', validators=[DataRequired()])
