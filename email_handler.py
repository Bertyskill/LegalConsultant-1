import os
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import logging
from datetime import datetime

from app import db
from models import User, ClientProfile, Consultation, Message, LegalTopic, LegalCategory

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Получение данных для подключения к почтовому серверу из переменных окружения
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
IMAP_HOST = os.environ.get('IMAP_HOST', 'imap.gmail.com')
IMAP_PORT = int(os.environ.get('IMAP_PORT', 993))

def send_notification_email(recipient_email, subject, body):
    """Отправляет email-уведомление."""
    try:
        # Создаем объект сообщения
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Добавляем тело сообщения
        msg.attach(MIMEText(body, 'html'))
        
        # Подключаемся к SMTP-серверу и отправляем сообщение
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Уведомление отправлено на {recipient_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")
        return False

def extract_client_email(email_text):
    """Извлекает email клиента из текста сообщения."""
    # Ищем email в формате user@domain.com
    email_pattern = r'[\w\.-]+@[\w\.-]+'
    matches = re.findall(email_pattern, email_text)
    if matches:
        return matches[0]
    return None

def extract_subject_info(subject):
    """Извлекает информацию из темы письма."""
    # Проверяем, содержит ли тема указание на существующую консультацию
    consultation_pattern = r'консультация[:\s]*#?(\d+)'
    match = re.search(consultation_pattern, subject, re.IGNORECASE)
    if match:
        consultation_id = int(match.group(1))
        return {'type': 'existing', 'consultation_id': consultation_id}
    
    # Если это новая консультация, пытаемся определить тему
    category_pattern = r'категория[:\s]*([\w\s]+)'
    match = re.search(category_pattern, subject, re.IGNORECASE)
    category_name = match.group(1).strip() if match else None
    
    topic_pattern = r'тема[:\s]*([\w\s]+)'
    match = re.search(topic_pattern, subject, re.IGNORECASE)
    topic_name = match.group(1).strip() if match else None
    
    return {
        'type': 'new',
        'category': category_name,
        'topic': topic_name
    }

def process_incoming_emails():
    """Обрабатывает входящие email-сообщения и создает из них консультации."""
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("Не заданы учетные данные для доступа к почте")
        return {'status': 'error', 'message': 'Email credentials not configured'}
    
    processed_count = 0
    
    try:
        # Подключаемся к IMAP-серверу
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select('inbox')
        
        # Ищем непрочитанные сообщения
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.error("Ошибка при поиске сообщений")
            return {'status': 'error', 'message': 'Failed to search messages'}
        
        # Обрабатываем каждое сообщение
        for mail_id in messages[0].split():
            status, msg_data = mail.fetch(mail_id, '(RFC822)')
            if status != 'OK':
                continue
                
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Получаем тему и отправителя
            subject = decode_header(email_message['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            sender = email_message['From']
            
            # Получаем тело сообщения
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition'))
                    
                    # Пропускаем вложения
                    if 'attachment' in content_disposition:
                        continue
                    
                    # Извлекаем текст
                    if content_type == 'text/plain' or content_type == 'text/html':
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset()
                        if charset:
                            body += payload.decode(charset, errors='replace')
                        else:
                            body += payload.decode(errors='replace')
            else:
                payload = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset()
                if charset:
                    body = payload.decode(charset, errors='replace')
                else:
                    body = payload.decode(errors='replace')
            
            # Извлекаем email клиента
            client_email = extract_client_email(sender)
            if not client_email:
                logger.warning(f"Не удалось определить email клиента: {sender}")
                continue
                
            # Ищем клиента в системе
            client_user = User.query.filter_by(email=client_email).first()
            if not client_user:
                logger.warning(f"Клиент с email {client_email} не найден в системе")
                continue
                
            client_profile = client_user.client_profile
            if not client_profile:
                logger.warning(f"Профиль клиента для {client_email} не найден")
                continue
                
            # Извлекаем информацию из темы
            subject_info = extract_subject_info(subject)
            
            if subject_info['type'] == 'existing':
                # Добавляем сообщение к существующей консультации
                consultation_id = subject_info['consultation_id']
                consultation = Consultation.query.get(consultation_id)
                
                if not consultation or consultation.client_id != client_profile.id:
                    logger.warning(f"Консультация #{consultation_id} не найдена или не принадлежит клиенту {client_email}")
                    continue
                    
                # Создаем новое сообщение
                message = Message(
                    consultation_id=consultation.id,
                    sender_id=client_user.id,
                    content=body
                )
                db.session.add(message)
                
                # Обновляем время последнего изменения консультации
                consultation.updated_at = datetime.now()
                
                db.session.commit()
                
                # Отправляем уведомление юристу, если он назначен
                if consultation.lawyer_id:
                    lawyer = consultation.lawyer
                    if lawyer and lawyer.user:
                        notification_subject = f"Новое сообщение в консультации #{consultation.id}"
                        notification_body = f"""
                        <p>Здравствуйте, {lawyer.user.first_name}!</p>
                        <p>Получено новое сообщение от клиента в консультации #{consultation.id}: "{consultation.title}".</p>
                        <p>Пожалуйста, ознакомьтесь с сообщением и ответьте клиенту.</p>
                        """
                        send_notification_email(lawyer.user.email, notification_subject, notification_body)
                
            else:
                # Создаем новую консультацию
                # Определяем категорию и тему
                category_name = subject_info.get('category')
                topic_name = subject_info.get('topic')
                
                category = None
                topic = None
                
                if category_name:
                    category = LegalCategory.query.filter(LegalCategory.name.ilike(f"%{category_name}%")).first()
                    
                if topic_name and category:
                    topic = LegalTopic.query.filter(
                        LegalTopic.name.ilike(f"%{topic_name}%"),
                        LegalTopic.category_id == category.id
                    ).first()
                elif topic_name:
                    topic = LegalTopic.query.filter(LegalTopic.name.ilike(f"%{topic_name}%")).first()
                
                # Если категория или тема не найдены, берем первые из базы
                if not category:
                    category = LegalCategory.query.first()
                    
                if not topic and category:
                    topic = LegalTopic.query.filter_by(category_id=category.id).first()
                elif not topic:
                    topic = LegalTopic.query.first()
                
                # Создаем новую консультацию
                consultation = Consultation(
                    client_id=client_profile.id,
                    topic_id=topic.id if topic else None,
                    title=subject,
                    request=body,
                    status='новая'
                )
                db.session.add(consultation)
                db.session.commit()
                
                # Отправляем уведомление менеджерам
                managers = User.query.filter_by(role='manager').all()
                for manager in managers:
                    notification_subject = "Новая консультация в системе"
                    notification_body = f"""
                    <p>Здравствуйте, {manager.first_name}!</p>
                    <p>В системе создана новая консультация от клиента {client_user.full_name}.</p>
                    <p>Тема: {consultation.title}</p>
                    <p>Пожалуйста, назначьте юриста для обработки этой консультации.</p>
                    """
                    send_notification_email(manager.email, notification_subject, notification_body)
            
            processed_count += 1
            
        mail.logout()
        
        return {'status': 'success', 'processed': processed_count}
    except Exception as e:
        logger.error(f"Ошибка при обработке писем: {str(e)}")
        return {'status': 'error', 'message': str(e)}
