import flask
from flask_restful import Resource, reqparse, abort
from flask_login import login_required, current_user
from . import db_session
from .word_rules import WordRule
from .user_mistakes import UserMistake

# Парсер для POST и PUT запросов
parser = reqparse.RequestParser()
parser.add_argument('word', required=True, help='Слово обязательно для заполнения')
parser.add_argument('correct_letter', required=True, help='Правильная буква обязательна')
parser.add_argument('rule', required=True, help='Правило обязательно')
parser.add_argument('category', required=False, help='Категория (необязательно)')


def abort_if_word_not_found(word_id):
    session = db_session.create_session()
    word = session.get(WordRule, word_id)
    if not word:
        abort(404, message=f"Слово с id {word_id} не найдено")
    session.close()


class WordListResource(Resource):

    def get(self):
        session = db_session.create_session()
        words = session.query(WordRule).all()
        session.close()
        return {
            'words': [{
                'id': w.id,
                'word': w.word,
                'correct_letter': w.correct_letter,
                'rule': w.rule,
                'category': w.category
            } for w in words]
        }

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()

        existing = session.query(WordRule).filter(WordRule.word == args['word']).first()
        if existing:
            abort(400, message=f"Слово '{args['word']}' уже существует")

        word = WordRule(
            word=args['word'],
            correct_letter=args['correct_letter'],
            rule=args['rule'],
            category=args.get('category')
        )
        session.add(word)
        session.commit()
        word_id = word.id
        session.close()
        return {'id': word_id, 'message': 'Слово успешно добавлено'}, 201


class WordResource(Resource):

    def get(self, word_id):
        abort_if_word_not_found(word_id)
        session = db_session.create_session()
        word = session.get(WordRule, word_id)
        session.close()
        return {
            'id': word.id,
            'word': word.word,
            'correct_letter': word.correct_letter,
            'rule': word.rule,
            'category': word.category
        }

    def put(self, word_id):
        abort_if_word_not_found(word_id)
        args = parser.parse_args()
        session = db_session.create_session()
        word = session.get(WordRule, word_id)
        word.word = args['word']
        word.correct_letter = args['correct_letter']
        word.rule = args['rule']
        word.category = args.get('category')
        session.commit()
        session.close()
        return {'message': 'Слово успешно обновлено'}

    def delete(self, word_id):
        abort_if_word_not_found(word_id)
        session = db_session.create_session()
        word = session.get(WordRule, word_id)
        session.delete(word)
        session.commit()
        session.close()
        return {'message': 'Слово успешно удалено'}


class CategoryListResource(Resource):

    def get(self):
        session = db_session.create_session()
        categories = session.query(WordRule.category).distinct().all()
        session.close()
        return {'categories': [c[0] for c in categories if c[0]]}


class UserMistakesResource(Resource):

    @login_required
    def get(self):
        session = db_session.create_session()
        mistakes = session.query(UserMistake).filter(
            UserMistake.user_id == current_user.id
        ).all()
        session.close()
        return {
            'mistakes': [{
                'id': m.id,
                'word_id': m.word_id,
                'category': m.category
            } for m in mistakes]
        }