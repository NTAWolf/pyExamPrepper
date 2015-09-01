# encoding: utf-8

"""
This module handles parsing of quiz files (.ep format), quiz ordering, 
question issuance and question reinsertion.
"""

import numpy as np
from datetime import datetime


def ORDER_RANDOM(categories):
    """Jumble all questions, regardless of categories.
    """
    questions = []
    for category in categories:
        questions.extend(list(category))
    np.random.shuffle(questions)
    return [Category('random', questions)]

def ORDER_NO_RANDOM(categories):
    """No randomness; keep the order defined in the quiz file.
    """
    return categories

def ORDER_RANDOM_WITHIN_CATEGORY(categories, inplace=False):
    """Keep the order of the categories, but jumble the questions within each category.
    """
    if not inplace:
        categories = [category.copy() for category in categories]
    for category in categories:
        np.random.shuffle(category)
    return categories

def ORDER_RANDOM_BETWEEN_CATEGORY(categories, inplace=False):
    """Shuffle the order of the categories, but keep their internal structure.
    """
    if not inplace:
        categories = categories[:]
    np.random.shuffle(categories)
    return categories

def ORDER_CATEGORIES_RANDOM_AND_RANDOM_WITHIN_CATEGORY(categories):
    """Shuffle category order, and shuffle question order within each category.
    """
    return ORDER_RANDOM_WITHIN_CATEGORY(ORDER_RANDOM_BETWEEN_CATEGORY(categories), inplace=True)

ORDER_OPTIONS = [ORDER_RANDOM, ORDER_NO_RANDOM, 
                ORDER_RANDOM_WITHIN_CATEGORY, 
                ORDER_RANDOM_BETWEEN_CATEGORY, 
                ORDER_CATEGORIES_RANDOM_AND_RANDOM_WITHIN_CATEGORY]


class Category(list):
    """A class for categorizing a set of questions.
    """
    def __init__(s, name, qas=None):
        s.name = name.strip()

        if qas:
            for qa in qas:
                if not 'category' in dir(qa):
                    qa.category = s # Hack to circumvent ORDER_RANDOM where everything is put in a Category('random')
            s.extend(qas)

    def __repr__(s):
        return s.name + ': ' + str(len(s))

    def copy(s):
        return Category(s.name[:], qas=s[:])

class QuestionAnswer(object):
    """Class holding the strings and relevant image paths for
    a quiz question-and-answer pair.
    """

    def __init__(s, question_str, answer_str, question_media=None, answer_media=None):
        s.answer = answer_str.strip()
        s.answer_media = answer_media
        s.question = question_str.strip()
        s.question_media = question_media

    def __repr__(s):
        return ''.join([QUESTION_START_SYMBOL, s.question, '\n', 
                        ANSWER_START_SYMBOL, s.answer])

    def __hash__(s):
        return hash(hash(s.question) + 
                    hash(s.answer) +
                    (hash(s.image_path) if s.image_path else 0))

class QuizConductor(object):
    """Responsible for ordering questions, handling 
    question repetitions, and delivering progress feedback.
    """

    def __init__(s, categories):
        """categories is a list of Category
        order is a function for ordering
        """
        s.base_categories = categories
        s.reset_indices()
        # s.update()

    def reinsert(s, qa):
        if s.repetition_lag == 'random':
            pos = np.random.random() * s.get_unseen_questions_in_category_count() + s._current_question_index
            pos = int(pos)
            s.current_category.insert(pos, qa)
        elif s.repetition_lag >= 0:
            s.current_category.insert(s._current_question_index + s.repetition_lag + 1, qa)
        else:
            s.current_category.append(qa)

    def update(s):
        """Updates the pointers to current category and question
        """
        s.current_category = s.categories[s._current_category_index]
        if s._current_question_index >= 0:
            s.current_question = s.current_category[s._current_question_index]

    def reset_indices(s):
        """Start over, but do not remove duplicate questions
        inserted due to repetition
        """
        s._current_category_index = 0
        s._current_question_index = -1

    def __iter__(s):
        return s

    def next(s):
        s._current_question_index += 1
        if s._current_question_index >= len(s.current_category):
            s._current_category_index += 1
            s._current_question_index = 0
            if s._current_category_index >= len(s.categories):
                raise StopIteration
        s.update()
        return s.current_question

    def get_total_progress(s):
        return float(s.get_total_questions_done_count())/s.get_total_question_count()
        
    def get_total_questions_done_count(s):
        count = 0
        for cat in s.categories[:s._current_category_index]:
            count += len(cat)
        count += s._current_question_index
        return count

    def get_total_question_count(s):
        return sum((len(cat) for cat in s.categories))

    def get_total_questions_left_count(s):
        return s.get_total_question_count() - s.get_total_questions_done_count()

    def get_progress_within_category(s):
        return float(s._current_question_index)/len(s.current_category)

    def get_unseen_questions_in_category_count(s):
        return len(s.current_category) - (s._current_question_index + 1)

    def get_completed_questions_in_category_count(s):
        return s._current_question_index

    def get_total_questions_in_category_count(s):
        return len(s.current_category)

    def get_categories_progress(s):
        return float(s._current_category_index)/len(s.categories)

    def set_repetition_lag(s, repetition_lag):
        s.repetition_lag = repetition_lag

    def get_current_category(s):
        return s.current_category

    def get_current_question(s):
        return s.current_category[s._current_question_index]

    def get_current_category_name(s):
        n = s.current_category.name
        if n == 'random': # TODO Hack to circumvent displaying 'random'. Not working ATM tho.
            return s.current_question.category.name
        return n

    def elapsed_time(s):
        return datetime.now() - s.start_time

    def setup(s, ui):
        """ui is a user interface, implementing QuizInterfaceBase
        """
        s.categories = ui.select_categories(s.base_categories)
        order = ui.select_ordering(ORDER_OPTIONS)
        s.categories = order(s.categories)
        s.repetition_lag = ui.select_repetition_lag()

    def handle_question(s, ui, qa):
        ui.show_question(qa)
        response = ui.get_response()
        ui.show_answer(qa)
        answer_ok = ui.get_evaluation()
        if not answer_ok:
            s.reinsert(s.current_question)

    def run(self, ui):
        self.setup(ui)
        self.update()
        self.n_questions_seen = 0
        self.start_time = datetime.now()

        for qa in self:
            self.n_questions_seen += 1
            ui.show_current_info(self)
            self.handle_question(ui,qa)

# End of class QuizConductor
