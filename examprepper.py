# encoding: utf-8

import subprocess # For use in commandline
import re
import numpy as np
from datetime import datetime
import os


QUESTION_START_SYMBOL = '?'
ANSWER_START_SYMBOL = '#'
IMAGE_START_SYMBOL = '['
IMAGE_END_SYMBOL = ']'
LINE_COMMENT_SYMBOL = '%'


def ORDER_RANDOM(categories):
    questions = []
    for category in categories:
        questions.extend(list(category))
    np.random.shuffle(questions)
    return [Category('random', questions)]

def ORDER_NO_RANDOM(categories):
    return categories

def ORDER_RANDOM_WITHIN_CATEGORY(categories, inplace=False):
    if not inplace:
        categories = [category.copy() for category in categories]
    for category in categories:
        np.random.shuffle(category)
    return categories

def ORDER_RANDOM_BETWEEN_CATEGORY(categories, inplace=False):
    if not inplace:
        categories = categories[:]
    np.random.shuffle(categories)
    return categories

def ORDER_CATEGORIES_RANDOM_AND_RANDOM_WITHIN_CATEGORY(categories):
    return ORDER_RANDOM_WITHIN_CATEGORY(ORDER_RANDOM_BETWEEN_CATEGORY(categories), inplace=True)



def parse_ep(filepath):
    """Interprets a quiz file in the given path, and returns
    the parsed list of categories
    """

    current_category = Category('unnamed')
    categories = []

    with open(filepath) as f:
        building_question = False
        building_answer = False
        current_question = None
        current_answer = None
        last_line = ''

        for line in f:
            if line[0] == LINE_COMMENT_SYMBOL:
                continue
            if line[0] == QUESTION_START_SYMBOL:
                if building_answer:
                    building_answer = False
                    # Flush question and answer. QuestionAnswer handles parsing image.
                    qa = QuestionAnswer(current_question, current_answer)
                    current_category.append(qa)
                building_question = True
                current_question = line[1:]
            elif line[0] == ANSWER_START_SYMBOL:
                building_question = False
                building_answer = True
                current_answer = line[1:]
            elif building_question:
                current_question += line
            elif building_answer:
                if line != '\n':
                    current_answer += line
                else:
                    building_answer = False
                    # Flush question and answer. QuestionAnswer handles parsing image.
                    qa = QuestionAnswer(current_question, current_answer)
                    current_category.append(qa)
            elif line != '\n':
                if len(current_category) > 0:
                    categories.append(current_category)
                current_category = Category(line)

    # End of file. Wrap up:
    if building_answer:
            # Flush question and answer. QuestionAnswer handles parsing image.
            qa = QuestionAnswer(current_question, current_answer)
            current_category.append(qa)
    if len(current_category) > 0:
        categories.append(current_category)

    return categories




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

    def __init__(s, question_str, answer_str):
        s.image_path = None
        s.extract_question(question_str)
        s.answer = answer_str.strip()

    def extract_question(s, question_str):
        imagefile = None
        question_str = question_str.strip()
        if question_str.startswith(IMAGE_START_SYMBOL):
            endsym = question_str.find(IMAGE_END_SYMBOL)
            if endsym > 0:
                s.image_path = question_str[1:endsym]
                question_str = question_str[endsym+1:].strip()
        s.question = question_str

    def __repr__(s):
        return ''.join([QUESTION_START_SYMBOL, s.question, '\n', 
                        ANSWER_START_SYMBOL, s.answer])

    def __hash__(s):
        return hash(hash(s.question) + 
                    hash(s.answer) +
                    (hash(s.image_path) if s.image_path else 0))


class QuizInterfaceBase(object):
    """This is the base interface for an ExamPrepper quiz.
    Extend and implement it in subclasses, catering to different views.

    Might very well be too rigidly built; a GUI might not want to 
    separate pick_categories and pick_ordering. This is a TODO.
    """

    def __init__(s, base_path, source_file, image_folder):
        s.ordering = ORDER_RANDOM

        s.file_path = base_path + '/' + source_file # TODO Use something platform independent.
        s.image_folder = base_path + '/' + image_folder

        # Load quiz from file
        s.categories = parse_ep(s.file_path)

        s.selected_categories = []
        s.unanswered = []

    def setup(s, callback_per_step=None):
        """Allows the user to pick categories, 
        pick an ordering of questions and categories,
        and select a lag for the number of questions
        between failing to answer a question and getting it again.

        callback_per_step is a method that takes a string. It is 
        called after every call made by this method, with the name 
        of the called method as argument.
        """
        s.pick_categories()
        s.pick_ordering()
        s.select_repetition_lag()

    def pick_categories(s):
        """Allow the user to pick categories.
        Set the chosen categories directly in s.selected_categories
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def pick_ordering(s):
        """Allow user to pick an ordering of the questions and categories.
        Draw inspiration from the existing ORDER_ methods, or make a new one yourself!
        Set the ordering in s.order.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def select_repetition_lag(s):
        """Allow user to select how many questions should pass before 
        a previously failed question is asked again.
        In the future, this might change to a range, allowing for some randomness.
        Put the decision in s.repetition_lag, and set it to a negative value 
        to just put the failed question at the end of the queue.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def display_question(s, qa):
        """Present the given question to the user.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def display_answer(s, qa):
        """Present the given answer to the user.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def display_current_info(s):
        """Display whatever misc. info you think the user would like to see
        Called before display_question.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def get_user_answer(s):
        """Retrieve the user's answer
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def evaluate_answer(s):
        """Have the user evaluate whether their own answer was good enough.

        Returns True or False.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def ask(s, qa):
        """Ask the user a question, get their response, and get their evaluation.
        """
        raise NotImplementedError('Abstract method - implement it yourself!')

    def elapsed_time(s):
        return datetime.now() - s.start_time

    def run(s):
        """Take the user through the quiz!
        """
        s.question_counter = 0
        s.start_time = datetime.now()
        s.quiz_conductor = QuizConductor(s, s.selected_categories, s.order, s.repetition_lag)

        def category_change_callback(category):
            s.current_category = category
            s.question_counter = 0

        for qa in s.quiz_conductor:
            s.question_counter += 1
            s.display_current_info()
            s.ask(qa)


# End of class QuizInterfaceBase




class CLI(QuizInterfaceBase):
    """Command line interface for quizzing
    Currently only supporting OSX Terminal (due use of 'open' command).

    Run by building the object, calling setup, and then calling 
    """

    def __init__(s, base_path, source_file, image_folder):
        super(CLI, s).__init__(base_path, source_file, image_folder)
        s.stats = AnswerStats('answer_stats.csv')
        s.PART_DELIMITER = '--------------'
    
    def setup(s, callback_per_step=None):
        CLI.clear()
        super(CLI, s).setup()

    def pick_categories(s): # Override super
        CLI.clear()     
        print "Pick the categories you want."
        print "Select any number of categories by entering their index numbers"
        print "separated by spaces and/or commas."
        print "Select all categories by entering a blank line."
        print "Select all categories except some by writing category numbers with",
        print "a minus sign in front of each."
        print "The categories are..."
        print

        # Print small progress bars indicating relative category sizes
        # Also, print number of questions per category, and category names.
        largest_cat_len = float(max([len(x) for x in s.categories]))
        for i, cat in enumerate(s.categories):
            frac_qas = len(cat) / largest_cat_len
            print format(i, ' 3'),
            print CLI.generate_progress_bar(8, frac_qas),
            print cat
        print


        # Interpret input
        # TODO Allow slice operators
        s.selected_categories = [] 
        inp = raw_input()
        if inp == '':
            s.selected_categories = s.categories
            return
        inp = [x for x in re.split('[ ,]+', inp) if not x == '']

        if all([x.startswith('-') for x in inp]): # All are negations
            catidx = list(range(len(s.categories)))
            for val in inp:
                catidx.remove(int(val[1:]))
            inp = catidx

        for val in inp:
            print val
            s.selected_categories.append(s.categories[int(val)])

    def pick_ordering(s): # Override super
        CLI.clear()
        print "Press 1 to use random ordering, mixing all the chosen categories."
        print "Press 2 to use the ordering defined in your quiz document."
        print "Press 3 to use the category order from your document, but shuffle the questions within each category."
        print "Press 4 to shuffle the category order, but keep the question order defined in your quiz document."
        print "Press 5 to shuffle both category order and question-within-category order."

        while True:
            inp = raw_input().strip()

            if inp == "1":
                s.order = ORDER_RANDOM
                break
            elif inp == "2":
                s.order = ORDER_NO_RANDOM
                break
            elif inp == "3":
                s.order = ORDER_RANDOM_WITHIN_CATEGORY
                break
            elif inp == "4":
                s.order = ORDER_RANDOM_BETWEEN_CATEGORY
                break
            elif inp == "5":
                s.order = ORDER_CATEGORIES_RANDOM_AND_RANDOM_WITHIN_CATEGORY
                break
            else:
                print "Sorry, not understood. Pick a number from 1 to 5."

    def select_repetition_lag(s): # Override super
        CLI.clear() 
        print "How many questions must pass before you get a wrongly answered question again?"
        print "Enter a blank line if you don't care"

        try:
            s.repetition_lag = int(raw_input())
        except ValueError as e:
            s.repetition_lag = -1

    def display_question(s, qa): # Override super
        s.stats.answer_starts()
        print "Q:", qa.question
        if qa.image_path:
            subprocess.call(['open', s.image_folder + '/' + qa.image_path]) # TODO use OS indifferent method

    def display_answer(s, qa): # Override super
        print "A:"
        print qa.answer

    def display_current_info(s): # Override super
        qc = s.quiz_conductor
        CLI.clear()
        
        print qc.get_current_category_name()
        print "|" + CLI.generate_progress_bar(20, qc.get_progress_within_category()) + "|",
        print str(qc.get_completed_questions_in_category_count()) + "/" + \
              str(qc.get_total_questions_in_category_count()), "in this category."

        print "|" + CLI.generate_progress_bar(20, qc.get_total_progress()) + "|",
        print str(qc.get_total_questions_done_count()) + "/" + \
              str(qc.get_total_question_count()), "in total."
        print

    def get_user_answer(s): # Override super
        print "Your answer (end with an empty line):"
        current_answer = ''
        while True:
            answer_fragment = raw_input()
            if answer_fragment == '':
                return current_answer.strip()
            current_answer += answer_fragment

    def evaluate_answer(s): # Override super
        print "Was your answer ok? y/n"
        while True:
            inp = raw_input()
            if inp.lower() == 'y':
                return True
            elif inp.lower() == 'n':
                return False
            print "Sorry, not understood. y or n, please"

    def ask(s, qa): # Override super
        s.display_question(qa)
        print s.PART_DELIMITER
        user_answer = s.get_user_answer()
        print s.PART_DELIMITER
        s.display_answer(qa)
        print s.PART_DELIMITER
        if not s.evaluate_answer():
            s.quiz_conductor.repeat()

    def run(s): # Override super
        super(CLI, s).run()

        print 
        print "Well done! It took you", s.elapsed_time()
        print

    @staticmethod
    def clear():
        """Clear the command line window
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def generate_progress_bar(length, progress, orientation='l', on_sym='+', off_sym=' '):
        """Returns a string resembling a progress bar

        length is an integer indicating how many characters it should span
        progress is a float  0 <= progress <= 1 indicating how far the bar should indicate we've progressed
        orientation is either 'l' or 'r', which entails starting the filling-out from the left or 
        the right, respectively.
        on_sym is the string symbol used to fill out the progress part. Should be 1 char.
        off_sym is the string symbol used to fill out the part we haven't reached yet with our progress. Should 
        be 1 char.
        """
        on_part = on_sym * int(progress * length)
        remaining_length = length - len(on_part)

        if orientation == 'l':
            return on_part + off_sym*remaining_length
        elif orientation == 'r':
            return off_sym*remaining_length + on_part


# End of class CLI


def run_cli_quiz(path, quiz, images='images'):
    """path is the path to a folder
    quiz is the file name of the quiz file, presumed to be in the folder "path"
    images is the folder name of the folder containing images pertaining to 
    the quiz. It too is expected to be in the path folder.
    """
    cli = CLI(path, quiz, 'images')
    cli.setup()
    cli.run()

    print "Write anything followed by enter to reload quiz file."
    while raw_input() != '':
        cli.load_quiz()
        print "Try a new configuration? y for yes, anything else to exit."
        if raw_input() == 'y':
            cli.setup()
            cli.run()
        else:
            break
        print "Write anything followed by enter to reload quiz file."



class QuizConductor(object):
    """Responsible for ordering questions, handling 
    question repetitions, and delivering progress feedback.
    """

    def __init__(s, quiz_interface, categories, order=None, repetition_lag=None):
        """categories is a list of Category
        order is a function for ordering
        """
        s.quiz_interface = quiz_interface
        s.categories = order(categories)
        s.repetition_lag = repetition_lag
        s.reset_indices()
        s.update()


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

    def repeat(s):
        """Repeat last question in accordance with s.repetition_lag
        """
        s.reinsert(s.current_question)

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

# End of class QuizConductor


class AnswerStats(object):
    """Collects stats/features for question answering
    """

    def __init__(s, output_file):
        s.output_file = output_file
        s.skip_user_answers = ['test', 't', 'ignore', 'skip']

        if not os.path.isfile(output_file):
            s.writeline('eval,ttas,question,answer,user_answer', 'w')

    def writeargs(s,args):
        s.writeline(','.join(args))

    def writeline(s, line, mode='a'):
        with open(s.output_file, 'a') as f:
            f.write(line + '\n')

    def answer_starts(s):
        s.start_time = datetime.now()

    def normalize_string(s, text):
        return re.sub('\W', '', text)

    def answer_ends(s, evaluation, qa, user_answer):
        t = datetime.now() - s.start_time
        t = t.total_seconds()
        ua = s.normalize_string(user_answer)
        if ua in s.skip_user_answers:
            return
        s.writeargs(["1" if evaluation else "0",
                     str(t),
                     s.normalize_string(qa.question),
                     s.normalize_string(qa.answer),
                     s.normalize_string(user_answer)
                    ])
        
    # Feature suggestions:
    # No of characters entered per time unit
    # No of characters in question (will affect response time)
    

