from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import json

from app import db
from models import (User, UserRole, ClientProfile, LawyerProfile, 
                   LegalCategory, Consultation, Document, 
                   Task, Contract, BillingEntry, CalendarEvent, Message,
                   Newsletter)
from forms import (LoginForm, RegisterForm, ClientProfileForm, LawyerProfileForm, 
                  ConsultationForm, DocumentForm, TaskForm, ContractForm, 
                  BillingEntryForm, CalendarEventForm, MessageForm, NewsletterForm,
                  ClientRegistrationForm, SearchForm)
from email_handler import send_notification_email, process_incoming_emails
from utils import calculate_monthly_billing, get_client_statistics, get_lawyer_statistics

def register_routes(app):
    # Главная страница
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_client:
                return redirect(url_for('client_dashboard'))
            elif current_user.is_lawyer:
                return redirect(url_for('lawyer_dashboard'))
            elif current_user.is_manager:
                return redirect(url_for('manager_dashboard'))
        return render_template('index.html')

    # Аутентификация и регистрация
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Неверный email или пароль', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegisterForm()
        if form.validate_on_submit():
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                role=UserRole.CLIENT  # Регистрация доступна только для клиентов
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Создание профиля клиента
            client_profile = ClientProfile(
                user_id=user.id,
                company_name=form.company_name.data
            )
            db.session.add(client_profile)
            db.session.commit()
            
            flash('Вы успешно зарегистрировались. Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    # Маршруты для клиентов
    @app.route('/client/dashboard')
    @login_required
    def client_dashboard():
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        # Получаем активный договор
        active_contract = Contract.query.filter_by(
            client_id=client.id, 
            status='активный'
        ).order_by(Contract.created_at.desc()).first()
        
        # Получаем текущий биллинг за месяц
        current_month = date.today().replace(day=1)
        month_billing = BillingEntry.query.filter(
            BillingEntry.client_id == client.id,
            BillingEntry.date >= current_month
        ).all()
        
        # Рассчитываем общее количество использованных часов и стоимость
        used_hours = sum(entry.hours for entry in month_billing)
        total_cost = sum(entry.amount for entry in month_billing)
        
        # Получаем последние консультации
        recent_consultations = Consultation.query.filter_by(
            client_id=client.id
        ).order_by(Consultation.updated_at.desc()).limit(5).all()
        
        return render_template(
            'client/dashboard.html',
            client=client,
            active_contract=active_contract,
            used_hours=used_hours,
            total_cost=total_cost,
            monthly_hours=active_contract.monthly_hours if active_contract else 0,
            remaining_hours=active_contract.monthly_hours - used_hours if active_contract else 0,
            recent_consultations=recent_consultations
        )

    @app.route('/client/billing')
    @login_required
    def client_billing():
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        # Получаем все биллинговые записи клиента, сгруппированные по месяцам
        billing_entries = BillingEntry.query.filter_by(client_id=client.id).order_by(BillingEntry.date.desc()).all()
        
        # Группируем записи по месяцам
        months = {}
        for entry in billing_entries:
            month_key = entry.date.strftime('%Y-%m')
            if month_key not in months:
                months[month_key] = {
                    'entries': [],
                    'total_hours': 0,
                    'total_amount': 0,
                    'month_name': entry.date.strftime('%B %Y')
                }
            months[month_key]['entries'].append(entry)
            months[month_key]['total_hours'] += entry.hours
            months[month_key]['total_amount'] += entry.amount
        
        return render_template(
            'client/billing.html',
            client=client,
            months=months
        )

    @app.route('/client/documents')
    @login_required
    def client_documents():
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        # Получаем все договоры клиента
        contracts = Contract.query.filter_by(client_id=client.id).order_by(Contract.start_date.desc()).all()
        
        # Получаем все документы из консультаций клиента
        consultations = Consultation.query.filter_by(client_id=client.id).all()
        documents = []
        for consultation in consultations:
            for doc in consultation.documents:
                if doc not in documents:
                    documents.append(doc)
        
        return render_template(
            'client/documents.html',
            client=client,
            contracts=contracts,
            documents=documents
        )

    @app.route('/client/consultations')
    @login_required
    def client_consultations():
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        # Получаем категории права и темы
        categories = LegalCategory.query.all()
        
        # Фильтрация по категории (если указана)
        category_id = request.args.get('category_id', type=int)
        topic = request.args.get('topic')
        
        # Формируем запрос
        query = Consultation.query.filter_by(client_id=client.id)
        
        if topic:
            query = query.filter(Consultation.topic == topic)
        elif category_id:
            query = query.filter_by(category_id=category_id)
        
        consultations = query.order_by(Consultation.updated_at.desc()).all()
        
        return render_template(
            'client/consultations.html',
            client=client,
            consultations=consultations,
            categories=categories,
            selected_category=category_id,
            selected_topic=topic
        )

    @app.route('/client/consultations/<int:id>')
    @login_required
    def client_consultation_detail(id):
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        consultation = Consultation.query.get_or_404(id)
        
        # Проверка, что консультация принадлежит текущему клиенту
        if consultation.client_id != client.id:
            abort(403)
            
        # Получаем все сообщения консультации
        messages = Message.query.filter_by(consultation_id=consultation.id).order_by(Message.created_at).all()
        
        # Форма для добавления сообщения
        form = MessageForm()
        
        return render_template(
            'client/consultation_detail.html',
            client=client,
            consultation=consultation,
            messages=messages,
            form=form
        )

    @app.route('/client/consultations/new', methods=['GET', 'POST'])
    @login_required
    def client_new_consultation():
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        form = ConsultationForm()
        
        # Заполняем выпадающие списки отраслей права
        categories = LegalCategory.query.all()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        
        # Получаем все уникальные темы из существующих консультаций
        existing_topics = db.session.query(Consultation.topic).filter_by(category_id=form.category_id.data).distinct().all() if form.category_id.data else []
        existing_topics = [topic[0] for topic in existing_topics if topic[0]]
        
        if form.validate_on_submit():
            consultation = Consultation(
                client_id=client.id,
                category_id=form.category_id.data,
                topic=form.topic.data,
                title=form.title.data,
                request=form.request.data,
                status='новая'
            )
            db.session.add(consultation)
            db.session.commit()
            
            flash('Консультация успешно создана', 'success')
            return redirect(url_for('client_consultations'))
            
        return render_template(
            'client/new_consultation.html',
            client=client,
            form=form,
            existing_topics=existing_topics
        )

    @app.route('/get_topics/<int:category_id>')
    def get_topics(category_id):
        # Получаем все уникальные темы из существующих консультаций по выбранной категории
        topics = db.session.query(Consultation.topic).filter_by(category_id=category_id).distinct().all()
        topic_list = [{'id': i, 'name': t[0]} for i, t in enumerate(topics, 1) if t[0]]
        return jsonify(topic_list)

    @app.route('/client/message/add', methods=['POST'])
    @login_required
    def client_add_message():
        if not current_user.is_client:
            abort(403)
            
        client = current_user.client_profile
        if not client:
            flash('Профиль клиента не найден', 'warning')
            return redirect(url_for('index'))
            
        form = MessageForm()
        if form.validate_on_submit():
            consultation_id = form.consultation_id.data
            consultation = Consultation.query.get_or_404(consultation_id)
            
            # Проверка, что консультация принадлежит текущему клиенту
            if consultation.client_id != client.id:
                abort(403)
                
            message = Message(
                consultation_id=consultation_id,
                sender_id=current_user.id,
                content=form.content.data
            )
            db.session.add(message)
            
            # Обновляем время изменения консультации
            consultation.updated_at = datetime.now()
            
            db.session.commit()
            
            flash('Сообщение отправлено', 'success')
            
        return redirect(url_for('client_consultation_detail', id=consultation_id))

    # Маршруты для юристов
    @app.route('/lawyer/dashboard')
    @login_required
    def lawyer_dashboard():
        if not current_user.is_lawyer:
            abort(403)
            
        lawyer = current_user.lawyer_profile
        if not lawyer:
            flash('Профиль юриста не найден', 'warning')
            return redirect(url_for('index'))
            
        # Получаем активные задачи
        active_tasks = Task.query.filter_by(
            assigned_to_id=current_user.id,
            status='активная'
        ).order_by(Task.due_date).all()
        
        # Получаем активные консультации
        active_consultations = Consultation.query.filter_by(
            lawyer_id=lawyer.id,
            status='активная'
        ).order_by(Consultation.updated_at.desc()).all()
        
        # Получаем ближайшие события календаря
        today = datetime.now()
        upcoming_events = CalendarEvent.query.filter(
            CalendarEvent.participants.any(id=current_user.id),
            CalendarEvent.start_time >= today
        ).order_by(CalendarEvent.start_time).limit(5).all()
        
        # Статистика за текущий месяц
        current_month = date.today().replace(day=1)
        month_billing = BillingEntry.query.filter(
            BillingEntry.lawyer_id == lawyer.id,
            BillingEntry.date >= current_month
        ).all()
        
        total_hours = sum(entry.hours for entry in month_billing)
        total_clients = len(set(entry.client_id for entry in month_billing))
        
        return render_template(
            'lawyer/dashboard.html',
            lawyer=lawyer,
            active_tasks=active_tasks,
            active_consultations=active_consultations,
            upcoming_events=upcoming_events,
            total_hours=total_hours,
            total_clients=total_clients
        )

    @app.route('/lawyer/tasks')
    @login_required
    def lawyer_tasks():
        if not current_user.is_lawyer:
            abort(403)
            
        # Получаем задачи с фильтрацией по статусу
        status = request.args.get('status', 'all')
        
        if status == 'all':
            tasks = Task.query.filter_by(assigned_to_id=current_user.id).order_by(Task.due_date).all()
        else:
            tasks = Task.query.filter_by(assigned_to_id=current_user.id, status=status).order_by(Task.due_date).all()
            
        return render_template(
            'lawyer/tasks.html',
            tasks=tasks,
            status=status
        )

    @app.route('/lawyer/task/update/<int:id>', methods=['POST'])
    @login_required
    def lawyer_update_task(id):
        if not current_user.is_lawyer:
            abort(403)
            
        task = Task.query.get_or_404(id)
        
        # Проверка, что задача назначена текущему юристу
        if task.assigned_to_id != current_user.id:
            abort(403)
            
        status = request.form.get('status')
        if status:
            task.status = status
            task.updated_at = datetime.now()
            db.session.commit()
            flash('Статус задачи обновлен', 'success')
            
        return redirect(url_for('lawyer_tasks'))

    @app.route('/lawyer/consultations')
    @login_required
    def lawyer_consultations():
        if not current_user.is_lawyer:
            abort(403)
            
        lawyer = current_user.lawyer_profile
        if not lawyer:
            flash('Профиль юриста не найден', 'warning')
            return redirect(url_for('index'))
            
        # Фильтрация по статусу
        status = request.args.get('status', 'all')
        
        # Формируем запрос
        query = Consultation.query.filter_by(lawyer_id=lawyer.id)
        
        if status != 'all':
            query = query.filter_by(status=status)
            
        consultations = query.order_by(Consultation.updated_at.desc()).all()
        
        return render_template(
            'lawyer/consultations.html',
            lawyer=lawyer,
            consultations=consultations,
            status=status
        )

    @app.route('/lawyer/consultations/<int:id>')
    @login_required
    def lawyer_consultation_detail(id):
        if not current_user.is_lawyer:
            abort(403)
            
        lawyer = current_user.lawyer_profile
        if not lawyer:
            flash('Профиль юриста не найден', 'warning')
            return redirect(url_for('index'))
            
        consultation = Consultation.query.get_or_404(id)
        
        # Проверка, назначена ли консультация текущему юристу
        if consultation.lawyer_id != lawyer.id:
            # Если консультация никому не назначена, назначаем ее текущему юристу
            if consultation.lawyer_id is None:
                consultation.lawyer_id = lawyer.id
                db.session.commit()
                flash('Консультация назначена вам', 'success')
            else:
                abort(403)
        
        # Получаем все сообщения консультации
        messages = Message.query.filter_by(consultation_id=consultation.id).order_by(Message.created_at).all()
        
        # Форма для добавления сообщения
        message_form = MessageForm()
        
        # Форма для добавления биллинга
        billing_form = BillingEntryForm()
        
        return render_template(
            'lawyer/consultation_detail.html',
            lawyer=lawyer,
            consultation=consultation,
            messages=messages,
            message_form=message_form,
            billing_form=billing_form
        )

    @app.route('/lawyer/message/add', methods=['POST'])
    @login_required
    def lawyer_add_message():
        if not current_user.is_lawyer:
            abort(403)
            
        lawyer = current_user.lawyer_profile
        if not lawyer:
            flash('Профиль юриста не найден', 'warning')
            return redirect(url_for('index'))
            
        form = MessageForm()
        if form.validate_on_submit():
            consultation_id = form.consultation_id.data
            consultation = Consultation.query.get_or_404(consultation_id)
            
            # Проверка, назначена ли консультация текущему юристу
            if consultation.lawyer_id != lawyer.id:
                abort(403)
                
            message = Message(
                consultation_id=consultation_id,
                sender_id=current_user.id,
                content=form.content.data
            )
            db.session.add(message)
            
            # Обновляем время изменения консультации
            consultation.updated_at = datetime.now()
            
            db.session.commit()
            
            flash('Сообщение отправлено', 'success')
            
        return redirect(url_for('lawyer_consultation_detail', id=consultation_id))

    @app.route('/lawyer/billing/add', methods=['POST'])
    @login_required
    def lawyer_add_billing():
        if not current_user.is_lawyer:
            abort(403)
            
        lawyer = current_user.lawyer_profile
        if not lawyer:
            flash('Профиль юриста не найден', 'warning')
            return redirect(url_for('index'))
            
        form = BillingEntryForm()
        if form.validate_on_submit():
            consultation_id = form.consultation_id.data
            consultation = Consultation.query.get_or_404(consultation_id)
            
            # Проверка, назначена ли консультация текущему юристу
            if consultation.lawyer_id != lawyer.id:
                abort(403)
                
            # Получаем активный договор клиента для определения стоимости часа
            client = consultation.client
            active_contract = Contract.query.filter_by(
                client_id=client.id, 
                status='активный'
            ).first()
            
            if not active_contract:
                flash('У клиента нет активного договора', 'warning')
                return redirect(url_for('lawyer_consultation_detail', id=consultation_id))
                
            billing_entry = BillingEntry(
                client_id=client.id,
                consultation_id=consultation_id,
                lawyer_id=lawyer.id,
                hours=form.hours.data,
                rate=active_contract.hourly_rate,
                description=form.description.data,
                date=datetime.now().date()
            )
            db.session.add(billing_entry)
            
            # Обновляем затраченное время в консультации
            consultation.time_spent += form.hours.data
            
            db.session.commit()
            
            flash(f'Учтено {form.hours.data} часов работы', 'success')
            
        return redirect(url_for('lawyer_consultation_detail', id=consultation_id))

    @app.route('/lawyer/calendar')
    @login_required
    def lawyer_calendar():
        if not current_user.is_lawyer:
            abort(403)
            
        # Получаем все события текущего юриста
        events = CalendarEvent.query.filter(
            CalendarEvent.participants.any(id=current_user.id)
        ).all()
        
        # Форматируем события для календаря
        calendar_events = []
        for event in events:
            calendar_events.append({
                'id': event.id,
                'title': event.title,
                'start': event.start_time.isoformat(),
                'end': event.end_time.isoformat(),
                'description': event.description,
                'location': event.location
            })
            
        return render_template(
            'lawyer/calendar.html',
            events=json.dumps(calendar_events)
        )

    @app.route('/lawyer/client_base')
    @login_required
    def lawyer_client_base():
        if not current_user.is_lawyer:
            abort(403)
            
        lawyer = current_user.lawyer_profile
        if not lawyer:
            flash('Профиль юриста не найден', 'warning')
            return redirect(url_for('index'))
            
        # Получаем всех клиентов, с которыми работал юрист
        consultations = Consultation.query.filter_by(lawyer_id=lawyer.id).all()
        client_ids = set(c.client_id for c in consultations)
        clients = [db.session.get(ClientProfile, id) for id in client_ids]
        clients = [c for c in clients if c is not None]
        
        # Форма поиска
        search_form = SearchForm()
        
        return render_template(
            'lawyer/client_base.html',
            lawyer=lawyer,
            clients=clients,
            search_form=search_form
        )

    @app.route('/lawyer/search', methods=['POST'])
    @login_required
    def lawyer_search():
        if not current_user.is_lawyer:
            abort(403)
            
        form = SearchForm()
        if form.validate_on_submit():
            query = form.query.data
            
            # Поиск по клиентам
            clients = ClientProfile.query.join(User).filter(
                (User.email.ilike(f'%{query}%')) |
                (User.first_name.ilike(f'%{query}%')) |
                (User.last_name.ilike(f'%{query}%')) |
                (ClientProfile.company_name.ilike(f'%{query}%'))
            ).all()
            
            # Поиск по консультациям
            consultations = Consultation.query.filter(
                (Consultation.title.ilike(f'%{query}%')) |
                (Consultation.request.ilike(f'%{query}%')) |
                (Consultation.response.ilike(f'%{query}%'))
            ).all()
            
            # Поиск по документам
            documents = Document.query.filter(
                (Document.filename.ilike(f'%{query}%')) |
                (Document.description.ilike(f'%{query}%'))
            ).all()
            
            return render_template(
                'lawyer/search_results.html',
                query=query,
                clients=clients,
                consultations=consultations,
                documents=documents
            )
            
        return redirect(url_for('lawyer_client_base'))

    # Маршруты для менеджеров
    @app.route('/manager/dashboard')
    @login_required
    def manager_dashboard():
        if not current_user.is_manager:
            abort(403)
            
        # Получаем статистику по клиентам
        client_count = ClientProfile.query.count()
        
        # Получаем статистику по юристам
        lawyer_count = LawyerProfile.query.count()
        
        # Получаем статистику по консультациям
        active_consultations = Consultation.query.filter_by(status='активная').count()
        new_consultations = Consultation.query.filter_by(status='новая').count()
        
        # Получаем статистику по задачам
        active_tasks = Task.query.filter_by(status='активная').count()
        new_tasks = Task.query.filter_by(status='новая').count()
        
        # Получаем статистику по биллингу за текущий месяц
        current_month = date.today().replace(day=1)
        month_billing = BillingEntry.query.filter(
            BillingEntry.date >= current_month
        ).all()
        
        total_hours = sum(entry.hours for entry in month_billing)
        total_amount = sum(entry.amount for entry in month_billing)
        
        return render_template(
            'manager/dashboard.html',
            client_count=client_count,
            lawyer_count=lawyer_count,
            active_consultations=active_consultations,
            new_consultations=new_consultations,
            active_tasks=active_tasks,
            new_tasks=new_tasks,
            total_hours=total_hours,
            total_amount=total_amount
        )

    @app.route('/manager/clients')
    @login_required
    def manager_clients():
        if not current_user.is_manager:
            abort(403)
            
        # Получаем всех клиентов
        clients = ClientProfile.query.join(User).order_by(User.last_name).all()
        
        return render_template(
            'manager/clients.html',
            clients=clients
        )

    @app.route('/manager/client/<int:id>')
    @login_required
    def manager_client_detail(id):
        if not current_user.is_manager:
            abort(403)
            
        client = ClientProfile.query.get_or_404(id)
        
        # Получаем активный договор
        active_contract = Contract.query.filter_by(
            client_id=client.id, 
            status='активный'
        ).first()
        
        # Получаем все консультации клиента
        consultations = Consultation.query.filter_by(client_id=client.id).order_by(Consultation.updated_at.desc()).all()
        
        # Получаем биллинг клиента
        billing_entries = BillingEntry.query.filter_by(client_id=client.id).order_by(BillingEntry.date.desc()).all()
        
        # Рассчитываем общую сумму и часы
        total_hours = sum(entry.hours for entry in billing_entries)
        total_amount = sum(entry.amount for entry in billing_entries)
        
        return render_template(
            'manager/client_detail.html',
            client=client,
            active_contract=active_contract,
            consultations=consultations,
            billing_entries=billing_entries,
            total_hours=total_hours,
            total_amount=total_amount
        )

    @app.route('/manager/create_client', methods=['GET', 'POST'])
    @login_required
    def manager_create_client():
        if not current_user.is_manager:
            abort(403)
            
        form = ClientRegistrationForm()
        
        if form.validate_on_submit():
            # Создаем пользователя
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                role=UserRole.CLIENT
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Создаем профиль клиента
            client = ClientProfile(
                user_id=user.id,
                company_name=form.company_name.data
            )
            db.session.add(client)
            db.session.commit()
            
            # Создаем договор, если указаны данные
            if form.contract_number.data:
                contract = Contract(
                    client_id=client.id,
                    contract_number=form.contract_number.data,
                    start_date=form.contract_start_date.data,
                    end_date=form.contract_end_date.data,
                    hourly_rate=form.hourly_rate.data,
                    monthly_hours=form.monthly_hours.data,
                    status='активный'
                )
                db.session.add(contract)
                db.session.commit()
            
            flash('Клиент успешно создан', 'success')
            return redirect(url_for('manager_clients'))
            
        return render_template(
            'manager/create_client.html',
            form=form
        )

    @app.route('/manager/client/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def manager_edit_client(id):
        if not current_user.is_manager:
            abort(403)
            
        client = ClientProfile.query.get_or_404(id)
        user = User.query.get(client.user_id)
        
        form = ClientProfileForm()
        
        if request.method == 'GET':
            form.email.data = user.email
            form.first_name.data = user.first_name
            form.last_name.data = user.last_name
            form.phone.data = user.phone
            form.company_name.data = client.company_name
            
        if form.validate_on_submit():
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.phone = form.phone.data
            
            client.company_name = form.company_name.data
            
            db.session.commit()
            
            flash('Данные клиента обновлены', 'success')
            return redirect(url_for('manager_client_detail', id=client.id))
            
        return render_template(
            'manager/edit_client.html',
            form=form,
            client=client
        )

    @app.route('/manager/contract/create/<int:client_id>', methods=['GET', 'POST'])
    @login_required
    def manager_create_contract(client_id):
        if not current_user.is_manager:
            abort(403)
            
        client = ClientProfile.query.get_or_404(client_id)
        
        form = ContractForm()
        
        if form.validate_on_submit():
            # Деактивируем предыдущие активные договоры
            active_contracts = Contract.query.filter_by(
                client_id=client.id, 
                status='активный'
            ).all()
            
            for contract in active_contracts:
                contract.status = 'закрыт'
                contract.end_date = date.today()
            
            # Создаем новый договор
            new_contract = Contract(
                client_id=client.id,
                contract_number=form.contract_number.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                hourly_rate=form.hourly_rate.data,
                monthly_hours=form.monthly_hours.data,
                terms=form.terms.data,
                status='активный'
            )
            db.session.add(new_contract)
            db.session.commit()
            
            flash('Договор успешно создан', 'success')
            return redirect(url_for('manager_client_detail', id=client.id))
            
        return render_template(
            'manager/create_contract.html',
            form=form,
            client=client
        )

    @app.route('/manager/lawyers')
    @login_required
    def manager_lawyers():
        if not current_user.is_manager:
            abort(403)
            
        # Получаем всех юристов
        lawyers = LawyerProfile.query.join(User).order_by(User.last_name).all()
        
        return render_template(
            'manager/lawyers.html',
            lawyers=lawyers
        )

    @app.route('/manager/lawyer/<int:id>')
    @login_required
    def manager_lawyer_detail(id):
        if not current_user.is_manager:
            abort(403)
            
        lawyer = LawyerProfile.query.get_or_404(id)
        
        # Получаем все активные задачи юриста
        active_tasks = Task.query.filter_by(
            assigned_to_id=lawyer.user_id,
            status='активная'
        ).all()
        
        # Получаем все активные консультации юриста
        active_consultations = Consultation.query.filter_by(
            lawyer_id=lawyer.id,
            status='активная'
        ).all()
        
        # Получаем статистику по биллингу
        billing_entries = BillingEntry.query.filter_by(lawyer_id=lawyer.id).all()
        
        # Рассчитываем общую сумму и часы
        total_hours = sum(entry.hours for entry in billing_entries)
        total_amount = sum(entry.amount for entry in billing_entries)
        
        return render_template(
            'manager/lawyer_detail.html',
            lawyer=lawyer,
            active_tasks=active_tasks,
            active_consultations=active_consultations,
            total_hours=total_hours,
            total_amount=total_amount
        )

    @app.route('/manager/create_lawyer', methods=['GET', 'POST'])
    @login_required
    def manager_create_lawyer():
        if not current_user.is_manager:
            abort(403)
            
        form = LawyerProfileForm()
        
        if form.validate_on_submit():
            # Создаем пользователя
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                role=UserRole.LAWYER
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Создаем профиль юриста
            lawyer = LawyerProfile(
                user_id=user.id,
                specialization=form.specialization.data,
                experience_years=form.experience_years.data,
                biography=form.biography.data
            )
            db.session.add(lawyer)
            db.session.commit()
            
            flash('Юрист успешно создан', 'success')
            return redirect(url_for('manager_lawyers'))
            
        return render_template(
            'manager/create_lawyer.html',
            form=form
        )

    @app.route('/manager/assign_task', methods=['GET', 'POST'])
    @login_required
    def manager_assign_task():
        if not current_user.is_manager:
            abort(403)
            
        form = TaskForm()
        
        # Заполняем выпадающие списки юристов и клиентов
        lawyers = User.query.filter_by(role=UserRole.LAWYER).all()
        form.assigned_to_id.choices = [(l.id, l.full_name) for l in lawyers]
        
        clients = ClientProfile.query.join(User).all()
        form.client_id.choices = [(c.id, c.user.full_name) for c in clients]
        
        if form.validate_on_submit():
            task = Task(
                title=form.title.data,
                description=form.description.data,
                created_by_id=current_user.id,
                assigned_to_id=form.assigned_to_id.data,
                client_id=form.client_id.data,
                status='новая',
                priority=form.priority.data,
                due_date=form.due_date.data
            )
            db.session.add(task)
            db.session.commit()
            
            flash('Задача успешно создана', 'success')
            return redirect(url_for('manager_tasks'))
            
        return render_template(
            'manager/assign_task.html',
            form=form
        )

    @app.route('/manager/tasks')
    @login_required
    def manager_tasks():
        if not current_user.is_manager:
            abort(403)
            
        # Фильтрация по статусу и юристу
        status = request.args.get('status', 'all')
        lawyer_id = request.args.get('lawyer_id', type=int)
        
        # Формируем запрос
        query = Task.query
        
        if status != 'all':
            query = query.filter_by(status=status)
            
        if lawyer_id:
            query = query.filter_by(assigned_to_id=lawyer_id)
            
        tasks = query.order_by(Task.due_date).all()
        
        # Получаем список юристов для фильтра
        lawyers = User.query.filter_by(role=UserRole.LAWYER).all()
        
        return render_template(
            'manager/tasks.html',
            tasks=tasks,
            status=status,
            selected_lawyer=lawyer_id,
            lawyers=lawyers
        )

    @app.route('/manager/calendar')
    @login_required
    def manager_calendar():
        if not current_user.is_manager:
            abort(403)
            
        # Получаем всех юристов для фильтра
        lawyers = User.query.filter_by(role=UserRole.LAWYER).all()
        
        # Получаем выбранного юриста (если указан)
        lawyer_id = request.args.get('lawyer_id', type=int)
        
        # Получаем все события
        if lawyer_id:
            events = CalendarEvent.query.filter(
                CalendarEvent.participants.any(id=lawyer_id)
            ).all()
        else:
            events = CalendarEvent.query.all()
        
        # Форматируем события для календаря
        calendar_events = []
        for event in events:
            calendar_events.append({
                'id': event.id,
                'title': event.title,
                'start': event.start_time.isoformat(),
                'end': event.end_time.isoformat(),
                'description': event.description,
                'location': event.location
            })
            
        return render_template(
            'manager/calendar.html',
            events=json.dumps(calendar_events),
            lawyers=lawyers,
            selected_lawyer=lawyer_id
        )

    @app.route('/manager/create_event', methods=['GET', 'POST'])
    @login_required
    def manager_create_event():
        if not current_user.is_manager:
            abort(403)
            
        form = CalendarEventForm()
        
        # Заполняем выпадающий список участников
        users = User.query.all()
        form.participants.choices = [(u.id, u.full_name) for u in users]
        
        if form.validate_on_submit():
            event = CalendarEvent(
                title=form.title.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                location=form.location.data,
                created_by_id=current_user.id
            )
            db.session.add(event)
            db.session.commit()
            
            # Добавляем участников
            for participant_id in form.participants.data:
                user = User.query.get(participant_id)
                if user:
                    event.participants.append(user)
            
            db.session.commit()
            
            flash('Мероприятие успешно создано', 'success')
            return redirect(url_for('manager_calendar'))
            
        return render_template(
            'manager/create_event.html',
            form=form
        )

    @app.route('/manager/reports')
    @login_required
    def manager_reports():
        if not current_user.is_manager:
            abort(403)
            
        # Получаем данные по биллингу за текущий месяц
        current_month = date.today().replace(day=1)
        month_billing = BillingEntry.query.filter(
            BillingEntry.date >= current_month
        ).all()
        
        # Группируем данные по клиентам
        client_data = {}
        for entry in month_billing:
            client_id = entry.client_id
            if client_id not in client_data:
                client = ClientProfile.query.get(client_id)
                client_data[client_id] = {
                    'client': client,
                    'hours': 0,
                    'amount': 0
                }
            client_data[client_id]['hours'] += entry.hours
            client_data[client_id]['amount'] += entry.amount
        
        # Группируем данные по юристам
        lawyer_data = {}
        for entry in month_billing:
            lawyer_id = entry.lawyer_id
            if lawyer_id not in lawyer_data:
                lawyer = LawyerProfile.query.get(lawyer_id)
                lawyer_data[lawyer_id] = {
                    'lawyer': lawyer,
                    'hours': 0,
                    'amount': 0
                }
            lawyer_data[lawyer_id]['hours'] += entry.hours
            lawyer_data[lawyer_id]['amount'] += entry.amount
        
        # Рассчитываем общие суммы
        total_hours = sum(data['hours'] for data in client_data.values())
        total_amount = sum(data['amount'] for data in client_data.values())
        
        return render_template(
            'manager/reports.html',
            client_data=client_data,
            lawyer_data=lawyer_data,
            total_hours=total_hours,
            total_amount=total_amount,
            month_name=current_month.strftime('%B %Y')
        )

    @app.route('/manager/newsletter', methods=['GET', 'POST'])
    @login_required
    def manager_newsletter():
        if not current_user.is_manager:
            abort(403)
            
        form = NewsletterForm()
        
        # Получаем всех клиентов для выбора получателей
        clients = User.query.filter_by(role=UserRole.CLIENT).all()
        form.recipients.choices = [(c.id, c.full_name) for c in clients]
        
        if form.validate_on_submit():
            newsletter = Newsletter(
                subject=form.subject.data,
                content=form.content.data,
                sent_by_id=current_user.id
            )
            db.session.add(newsletter)
            db.session.commit()
            
            # Добавляем получателей
            if form.all_clients.data:
                # Отправляем всем клиентам
                for client in clients:
                    newsletter.recipients.append(client)
            else:
                # Отправляем выбранным клиентам
                for recipient_id in form.recipients.data:
                    user = User.query.get(recipient_id)
                    if user:
                        newsletter.recipients.append(user)
            
            db.session.commit()
            
            # Отправляем письма
            for recipient in newsletter.recipients:
                send_notification_email(
                    recipient.email,
                    newsletter.subject,
                    newsletter.content
                )
            
            flash('Рассылка успешно отправлена', 'success')
            return redirect(url_for('manager_dashboard'))
            
        return render_template(
            'manager/newsletter.html',
            form=form
        )

    # Общие маршруты
    @app.route('/document/upload', methods=['POST'])
    @login_required
    def upload_document():
        form = DocumentForm()
        if form.validate_on_submit():
            if 'file' not in request.files:
                flash('Файл не выбран', 'danger')
                return redirect(request.referrer)
                
            file = request.files['file']
            if file.filename == '':
                flash('Файл не выбран', 'danger')
                return redirect(request.referrer)
                
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            
            # Создаем директорию, если не существует
            os.makedirs('uploads', exist_ok=True)
            
            file.save(file_path)
            
            document = Document(
                filename=filename,
                file_path=file_path,
                file_type=file.content_type,
                file_size=os.path.getsize(file_path),
                uploaded_by_id=current_user.id,
                description=form.description.data
            )
            db.session.add(document)
            
            # Если указана консультация, связываем документ с ней
            if form.consultation_id.data:
                consultation = Consultation.query.get(form.consultation_id.data)
                if consultation:
                    consultation.documents.append(document)
            
            db.session.commit()
            
            flash('Документ успешно загружен', 'success')
            
        return redirect(request.referrer)

    @app.route('/document/download/<int:id>')
    @login_required
    def download_document(id):
        document = Document.query.get_or_404(id)
        
        # Проверяем права доступа
        can_access = False
        
        if current_user.is_manager:
            can_access = True
        elif current_user.is_lawyer:
            # Проверяем, связан ли документ с консультациями юриста
            lawyer = current_user.lawyer_profile
            if lawyer:
                for consultation in document.consultations:
                    if consultation.lawyer_id == lawyer.id:
                        can_access = True
                        break
        elif current_user.is_client:
            # Проверяем, связан ли документ с консультациями клиента
            client = current_user.client_profile
            if client:
                for consultation in document.consultations:
                    if consultation.client_id == client.id:
                        can_access = True
                        break
        
        if not can_access:
            abort(403)
            
        return send_file(document.file_path, download_name=document.filename, as_attachment=True)

    # Периодические задачи (запускаются отдельно)
    @app.route('/tasks/process_emails', methods=['POST'])
    def task_process_emails():
        # Проверяем секретный ключ для запуска задачи
        secret_key = request.args.get('key')
        if not secret_key or secret_key != app.config.get('TASK_SECRET_KEY'):
            abort(403)
            
        # Обрабатываем входящие письма
        result = process_incoming_emails()
        
        return jsonify({'status': 'success', 'processed': result})
