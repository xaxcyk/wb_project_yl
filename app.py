import random
from flask import Flask, render_template, redirect, url_for, request, flash, session as flask_session, g, jsonify, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from data.word_rules import WordRule
from data.user_mistakes import UserMistake
from forms.user import RegisterForm, LoginForm
from flask_restful import Api
from data.word_resources import WordListResource, WordResource, CategoryListResource, UserMistakesResource

# Создание Flask-приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# Обработчики ошибок API (возвращают JSON вместо HTML)
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Ресурс не найден'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Неверный запрос'}), 400)

@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': 'Внутренняя ошибка сервера'}), 500)

@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({'error': 'Метод не разрешён'}), 405)

# Настройка авторизации
login_manager = LoginManager()
login_manager.init_app(app)

# Настройка REST API
api = Api(app)
login_manager.login_view = 'login'
api.add_resource(WordListResource, '/api/v2/words')
api.add_resource(WordResource, '/api/v2/words/<int:word_id>')
api.add_resource(CategoryListResource, '/api/v2/categories')
api.add_resource(UserMistakesResource, '/api/v2/mistakes')

# Инициализация базы данных
db_session.global_init("db/web_project.db")

# Создание сессии БД для каждого запроса (хранится в g)
@app.before_request
def before_request():
    g.sess = db_session.create_session()

# Закрытие сессии БД после запроса
@app.teardown_appcontext
def teardown_session(exception=None):
    sess = g.pop('sess', None)
    if sess:
        sess.close()

# Загрузка пользователя из БД по ID для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return g.sess.get(User, int(user_id))

# ------------------- Основные маршруты -------------------
@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html', title='Главная')

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if g.sess.query(User).filter(User.username == form.username.data).first():
            form.username.errors.append('Пользователь с таким логином уже существует')
            return render_template('register.html', form=form)
        if g.sess.query(User).filter(User.email == form.email.data).first():
            form.email.errors.append('Пользователь с такой почтой уже зарегистрирован')
            return render_template('register.html', form=form)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        g.sess.add(user)
        g.sess.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('register.html', title='Регистрация', form=form)

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = g.sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            form.email.errors.append('Неправильная почта или пароль')
    return render_template('login.html', title='Вход', form=form)

# Выход пользователя
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Страница категорий
@app.route('/categories')
def categories():
    return render_template('categories.html', title='Категории')

# Перенаправление на тренировку со всеми словами
@app.route('/words')
def words():
    return redirect(url_for('training', category='all'))

# Страница правил
@app.route('/rules')
def rules():
    return render_template('rules.html', title='Правила')

# Тренировка (основная логика)
@app.route('/training', methods=['GET', 'POST'])
def training():
    category = request.args.get('category', 'all')

    # Преобразование английских ключей в русские названия
    category_names = {
        'roots': 'Корни с чередованием',
        'prefixes': 'Приставки ПРЕ- и ПРИ-',
        'suffixes': 'Суффиксы',
        'verb_ends': 'Окончания глаголов и суффиксы причастий',
        'ne': 'Правописание НЕ с разными частями речи',
        'hyphen': 'Слитное, раздельное, дефисное написание',
        'soft_sign': 'Ь после шипящих',
        'ci': 'Ы/И после Ц',
        'participle_suf': 'Гласные в суффиксах причастий прошедшего времени',
        'raz_roz': 'Гласные в приставках раз-/роз-',
        'all': 'Все слова'
    }
    category_display = category_names.get(category, category)

    # Получение слов из БД
    if category == 'all':
        words = g.sess.query(WordRule).all()
    else:
        words = g.sess.query(WordRule).filter(WordRule.category == category).all()

    total = len(words)
    if total == 0:
        flash('В этой категории пока нет слов', 'warning')
        return redirect(url_for('categories'))

    # Управление порядком слов (случайный) через сессию
    order_key = f'order_{category}'
    index_key = f'index_{category}'

    if request.method == 'GET':
        if 'index' not in request.args:
            word_ids = [w.id for w in words]
            random.shuffle(word_ids)
            flask_session[order_key] = word_ids
            flask_session[index_key] = 0
            current_index = 0
        else:
            current_index = int(request.args.get('index'))
            if order_key not in flask_session:
                word_ids = [w.id for w in words]
                random.shuffle(word_ids)
                flask_session[order_key] = word_ids
            flask_session[index_key] = current_index
    else:
        current_index = flask_session.get(index_key, 0)

    if current_index >= total:
        flash('Поздравляем! Вы прошли все слова.', 'success')
        flask_session.pop(order_key, None)
        flask_session.pop(index_key, None)
        return redirect(url_for('index'))

    word_id = flask_session[order_key][current_index]
    current_word = g.sess.get(WordRule, word_id)

    # Обработка ответа пользователя
    if request.method == 'POST':
        user_letter = request.form.get('letter', '').strip().lower()
        if user_letter == current_word.correct_letter.lower():
            result = 'correct'
            flash('✅ Правильно!', 'success')
        else:
            result = 'incorrect'
            flash(f'❌ Неправильно! Правильная буква: {current_word.correct_letter.upper()}', 'danger')
            # Сохранение ошибки в БД
            if current_user.is_authenticated:
                existing = g.sess.query(UserMistake).filter(
                    UserMistake.user_id == current_user.id,
                    UserMistake.word_id == current_word.id
                ).first()
                if not existing:
                    mistake = UserMistake(
                        user_id=current_user.id,
                        word_id=current_word.id,
                        category=current_word.category
                    )
                    g.sess.add(mistake)
                    g.sess.commit()
        return render_template('training.html',
                               word=current_word,
                               category=category_display,
                               category_key=category,
                               index=current_index,
                               total=total,
                               result=result,
                               user_letter=user_letter,
                               title=f'Тренировка: {category_display}')

    return render_template('training.html',
                           word=current_word,
                           category=category_display,
                           category_key=category,
                           index=current_index,
                           total=total,
                           result=None,
                           user_letter='',
                           title=f'Тренировка: {category_display}')

# Личный кабинет со статистикой
@app.route('/profile')
@login_required
def profile():
    from sqlalchemy import func

    category_names = {
        'roots': 'Корни с чередованием',
        'prefixes': 'Приставки ПРЕ- и ПРИ-',
        'suffixes': 'Суффиксы',
        'verb_ends': 'Окончания глаголов и суффиксы причастий',
        'ne': 'Правописание НЕ с разными частями речи',
        'hyphen': 'Слитное, раздельное, дефисное написание',
        'soft_sign': 'Ь после шипящих',
        'ci': 'Ы/И после Ц',
        'participle_suf': 'Гласные в суффиксах причастий прошедшего времени',
        'raz_roz': 'Гласные в приставках раз-/роз-',
        'all': 'Все слова'
    }

    mistakes = g.sess.query(UserMistake).filter(UserMistake.user_id == current_user.id).all()

    grouped_mistakes = {}
    for m in mistakes:
        cat_key = m.category or 'Без категории'
        cat_name = category_names.get(cat_key, cat_key)
        grouped_mistakes.setdefault(cat_name, []).append(m)

    word_counts = {}
    counts = g.sess.query(WordRule.category, func.count(WordRule.id)).group_by(WordRule.category).all()
    for cat_key, count in counts:
        cat_name = category_names.get(cat_key, cat_key or 'Без категории')
        word_counts[cat_name] = count

    category_stats = {}
    for category_name, words_count in word_counts.items():
        mistakes_count = len(grouped_mistakes.get(category_name, []))
        correct_count = words_count - mistakes_count
        percent = int((correct_count / words_count) * 100) if words_count > 0 else 0
        category_stats[category_name] = {
            'total': words_count,
            'correct': correct_count,
            'mistakes': mistakes_count,
            'percent': percent
        }

    total_words = sum(word_counts.values())
    total_mistakes = len(mistakes)
    total_correct = total_words - total_mistakes
    overall_percent = int((total_correct / total_words) * 100) if total_words > 0 else 0

    return render_template('profile.html',
                           title='Личный кабинет',
                           grouped=grouped_mistakes,
                           category_stats=category_stats,
                           overall_percent=overall_percent,
                           total_words=total_words,
                           total_mistakes=total_mistakes,
                           total_correct=total_correct)

# Страница экзамена (заглушка)
@app.route('/exam')
def exam():
    return render_template('exam.html', title='Экзамен')

# Исправление ошибки (тренировка на 10 слов из той же категории)
@app.route('/fix_mistake/<int:mistake_id>', methods=['GET', 'POST'])
@login_required
def fix_mistake(mistake_id):
    mistake = g.sess.query(UserMistake).filter(
        UserMistake.id == mistake_id,
        UserMistake.user_id == current_user.id
    ).first()
    if not mistake:
        flash('Ошибка не найдена', 'danger')
        return redirect(url_for('profile'))

    category = mistake.category
    words = g.sess.query(WordRule).filter(WordRule.category == category).all()

    if len(words) < 10:
        flash(f'В категории "{category}" недостаточно слов для тренировки', 'warning')
        return redirect(url_for('profile'))

    random.shuffle(words)
    words = words[:10]

    flask_session['fix_order'] = [w.id for w in words]
    flask_session['fix_index'] = 0
    flask_session['fix_mistake_id'] = mistake_id

    return redirect(url_for('fix_training'))

# Процесс исправления ошибки
@app.route('/fix_training', methods=['GET', 'POST'])
@login_required
def fix_training():
    word_ids = flask_session.get('fix_order', [])
    current_index = flask_session.get('fix_index', 0)
    mistake_id = flask_session.get('fix_mistake_id')

    if not word_ids or current_index >= len(word_ids):
        if mistake_id:
            mistake = g.sess.query(UserMistake).filter(
                UserMistake.id == mistake_id,
                UserMistake.user_id == current_user.id
            ).first()
            if mistake:
                g.sess.delete(mistake)
                g.sess.commit()
                flash('Вы успешно исправили ошибку! Слово удалено из вашего списка.', 'success')
            else:
                flash('Ошибка уже была исправлена', 'info')
        flask_session.pop('fix_order', None)
        flask_session.pop('fix_index', None)
        flask_session.pop('fix_mistake_id', None)
        return redirect(url_for('profile'))

    word_id = word_ids[current_index]
    current_word = g.sess.get(WordRule, word_id)

    if request.method == 'POST':
        user_letter = request.form.get('letter', '').strip().lower()
        if user_letter == current_word.correct_letter.lower():
            flash('✅ Верно!', 'success')
            flask_session['fix_index'] = current_index + 1
            return redirect(url_for('fix_training'))
        else:
            flash(f'❌ Неправильно! Правильная буква: {current_word.correct_letter.upper()}', 'danger')
            return render_template('fix_training.html',
                                   word=current_word,
                                   index=current_index,
                                   total=len(word_ids),
                                   user_letter=user_letter)

    return render_template('fix_training.html',
                           word=current_word,
                           index=current_index,
                           total=len(word_ids),
                           user_letter='')

# Запуск приложения (доступно извне на порту 5000)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)