from datetime import datetime, date, timedelta
from models import BillingEntry, Consultation, ClientProfile, LawyerProfile, Contract
from app import db
import calendar

def get_month_dates(year, month):
    """Возвращает начальную и конечную даты месяца."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return first_day, last_day

def calculate_monthly_billing(client_id, year=None, month=None):
    """
    Рассчитывает биллинг клиента за указанный месяц.
    Если месяц и год не указаны, используется текущий месяц.
    """
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month
        
    start_date, end_date = get_month_dates(year, month)
    
    # Получаем все записи биллинга за указанный период
    billing_entries = BillingEntry.query.filter(
        BillingEntry.client_id == client_id,
        BillingEntry.date >= start_date,
        BillingEntry.date <= end_date
    ).all()
    
    # Рассчитываем общую сумму и часы
    total_hours = sum(entry.hours for entry in billing_entries)
    total_amount = sum(entry.amount for entry in billing_entries)
    
    # Получаем активный договор клиента
    active_contract = Contract.query.filter_by(
        client_id=client_id, 
        status='активный',
        start_date__lte=end_date
    ).order_by(Contract.start_date.desc()).first()
    
    monthly_hours = active_contract.monthly_hours if active_contract else 0
    hourly_rate = active_contract.hourly_rate if active_contract else 0
    
    # Рассчитываем остаток часов
    remaining_hours = monthly_hours - total_hours if monthly_hours > total_hours else 0
    
    # Рассчитываем превышение абонемента
    excess_hours = total_hours - monthly_hours if total_hours > monthly_hours else 0
    excess_amount = excess_hours * hourly_rate
    
    return {
        'total_hours': total_hours,
        'total_amount': total_amount,
        'monthly_hours': monthly_hours,
        'remaining_hours': remaining_hours,
        'excess_hours': excess_hours,
        'excess_amount': excess_amount,
        'entries': billing_entries
    }

def get_client_statistics(client_id):
    """Возвращает статистику по клиенту."""
    # Количество консультаций
    consultations = Consultation.query.filter_by(client_id=client_id).all()
    total_consultations = len(consultations)
    active_consultations = len([c for c in consultations if c.status in ['открыта', 'активная', 'новая']])
    
    # Статистика по времени
    total_time_spent = sum(c.time_spent for c in consultations)
    
    # Статистика по категориям
    category_stats = {}
    for consultation in consultations:
        if consultation.topic and consultation.topic.category:
            category_name = consultation.topic.category.name
            if category_name not in category_stats:
                category_stats[category_name] = 0
            category_stats[category_name] += 1
    
    # Статистика по биллингу
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    
    billing_entries = BillingEntry.query.filter(
        BillingEntry.client_id == client_id,
        BillingEntry.date >= start_of_year
    ).all()
    
    monthly_billing = {}
    for entry in billing_entries:
        month_key = entry.date.strftime('%Y-%m')
        if month_key not in monthly_billing:
            monthly_billing[month_key] = {
                'hours': 0,
                'amount': 0,
                'month_name': entry.date.strftime('%B %Y')
            }
        monthly_billing[month_key]['hours'] += entry.hours
        monthly_billing[month_key]['amount'] += entry.amount
    
    return {
        'total_consultations': total_consultations,
        'active_consultations': active_consultations,
        'total_time_spent': total_time_spent,
        'category_stats': category_stats,
        'monthly_billing': monthly_billing
    }

def get_lawyer_statistics(lawyer_id):
    """Возвращает статистику по юристу."""
    # Получаем все консультации юриста
    consultations = Consultation.query.filter_by(lawyer_id=lawyer_id).all()
    total_consultations = len(consultations)
    active_consultations = len([c for c in consultations if c.status in ['открыта', 'активная']])
    
    # Статистика по биллингу
    billing_entries = BillingEntry.query.filter_by(lawyer_id=lawyer_id).all()
    total_hours = sum(entry.hours for entry in billing_entries)
    total_amount = sum(entry.amount for entry in billing_entries)
    
    # Статистика по месяцам
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    
    monthly_stats = {}
    for entry in billing_entries:
        if entry.date < start_of_year:
            continue
            
        month_key = entry.date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'hours': 0,
                'amount': 0,
                'month_name': entry.date.strftime('%B %Y')
            }
        monthly_stats[month_key]['hours'] += entry.hours
        monthly_stats[month_key]['amount'] += entry.amount
    
    # Статистика по клиентам
    client_ids = set(c.client_id for c in consultations)
    clients_count = len(client_ids)
    
    # Статистика по категориям
    category_stats = {}
    for consultation in consultations:
        if consultation.topic and consultation.topic.category:
            category_name = consultation.topic.category.name
            if category_name not in category_stats:
                category_stats[category_name] = 0
            category_stats[category_name] += 1
    
    return {
        'total_consultations': total_consultations,
        'active_consultations': active_consultations,
        'total_hours': total_hours,
        'total_amount': total_amount,
        'monthly_stats': monthly_stats,
        'clients_count': clients_count,
        'category_stats': category_stats
    }

def get_top_lawyers(count=5):
    """Возвращает топ юристов по количеству часов за текущий месяц."""
    today = date.today()
    first_day = date(today.year, today.month, 1)
    
    # Получаем всех юристов
    lawyers = LawyerProfile.query.all()
    
    # Считаем часы для каждого юриста
    lawyer_stats = []
    for lawyer in lawyers:
        billing_entries = BillingEntry.query.filter(
            BillingEntry.lawyer_id == lawyer.id,
            BillingEntry.date >= first_day
        ).all()
        
        total_hours = sum(entry.hours for entry in billing_entries)
        total_amount = sum(entry.amount for entry in billing_entries)
        
        lawyer_stats.append({
            'lawyer': lawyer,
            'hours': total_hours,
            'amount': total_amount
        })
    
    # Сортируем по убыванию часов
    lawyer_stats.sort(key=lambda x: x['hours'], reverse=True)
    
    return lawyer_stats[:count]

def get_overdue_tasks():
    """Возвращает просроченные задачи."""
    from models import Task
    today = date.today()
    
    overdue_tasks = Task.query.filter(
        Task.due_date < today,
        Task.status != 'завершена'
    ).all()
    
    return overdue_tasks

def get_pending_contracts():
    """Возвращает договоры, которые скоро истекают."""
    today = date.today()
    thirty_days_later = today + timedelta(days=30)
    
    pending_contracts = Contract.query.filter(
        Contract.end_date <= thirty_days_later,
        Contract.end_date >= today,
        Contract.status == 'активный'
    ).all()
    
    return pending_contracts
