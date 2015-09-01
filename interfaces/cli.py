# encoding: utf-8


from base_interface import QuizInterfaceBase

import subprocess # For use in commandline
import re
import os # used in clear()

class CLI(QuizInterfaceBase):
    """Command line interface for quizzing
    Currently only supporting OSX Terminal (due use of 'open' command).

    Run by building the object, calling setup, and then calling 
    """

    def __init__(s):
        s.PART_DELIMITER = '----------'
    
    def select_categories(s, categories): # Override super
        CLI.clear()     
        print "Select the categories you want."
        print "Select any number of categories by entering their index numbers"
        print "separated by spaces and/or commas."
        print "Select all categories by entering a blank line."
        print "Select all categories except some by writing category numbers with",
        print "a minus sign in front of each."
        print "The categories are..."
        print

        # Print small progress bars indicating relative category sizes
        # Also, print number of questions per category, and category names.
        largest_cat_len = float(max([len(x) for x in categories]))
        for i, cat in enumerate(categories):
            frac_qas = len(cat) / largest_cat_len
            print format(i, ' 3'),
            print CLI.generate_progress_bar(8, frac_qas),
            print cat
        print


        # Interpret input
        # TODO Allow slice operators
        selected_categories = [] 
        inp = raw_input()
        if inp == '':
            return categories
        inp = [x for x in re.split('[ ,]+', inp) if not x == '']

        if all([x.startswith('-') for x in inp]): # All are negations
            catidx = list(range(len(categories)))
            for val in inp:
                catidx.remove(int(val[1:]))
            inp = catidx

        for val in inp:
            print val
            selected_categories.append(categories[int(val)])

        return selected_categories

    def select_ordering(s, order_options): # Override super
        # CLI.clear()
        for i, op in enumerate(order_options):
            print "Press {} for: {}".format(i+1, op.__doc__)

        while True:
            try:
                inp = int(raw_input())
            except ValueError as ve:
                pass
            else:
                if 1 <= inp <= len(order_options):
                    print inp
                    return order_options[inp-1]
            print "Sorry, not understood. Enter a number from 1 to {}.".format(len(order_options))

    def select_repetition_lag(s): # Override super
        CLI.clear() 
        print "How many questions must pass before you get a wrongly answered question again?"
        print "Enter a blank line if you don't care"

        try:
            repetition_lag = int(raw_input())
        except ValueError as e:
            repetition_lag = -1
        return repetition_lag

    def show_question(s, qa): # Override super
        print "Q:", qa.question
        # if qa.image_path:
            # subprocess.call(['open', s.image_folder + '/' + qa.image_path]) # TODO use OS indifferent method
        print s.PART_DELIMITER

    def show_answer(s, qa): # Override super
        print "A:"
        print qa.answer

    def show_current_info(s, quiz_conductor): # Override super
        qc = quiz_conductor
        CLI.clear()
        
        print qc.get_current_category_name()
        print "|" + CLI.generate_progress_bar(20, qc.get_progress_within_category()) + "|",
        print str(qc.get_completed_questions_in_category_count()) + "/" + \
              str(qc.get_total_questions_in_category_count()), "in this category."

        print "|" + CLI.generate_progress_bar(20, qc.get_total_progress()) + "|",
        print str(qc.get_total_questions_done_count()) + "/" + \
              str(qc.get_total_question_count()), "in total."
        print

    def get_response(s): # Override super
        print "Your answer (end with an empty line):"
        current_answer = ''
        while True:
            answer_fragment = raw_input()
            if answer_fragment == '':
                print s.PART_DELIMITER
                return current_answer.strip()
            current_answer += answer_fragment

    def get_evaluation(s): # Override super
        print "Was your answer ok? y/n"
        while True:
            inp = raw_input()
            if inp.lower() == 'y':
                return True
            elif inp.lower() == 'n':
                return False
            print "Sorry, not understood. y or n, please"

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
