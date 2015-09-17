# encoding: utf-8
from __future__ import print_function

from base_interface import QuizInterfaceBase
import re

RE_WHITESPACE = re.compile("^\s*$")

class View(object):
    def __init__(self, terminal=None, input_gt=False, view=None):
        if view != None and type(view) == View:
            self.t = terminal or view.t
            self.contents = view.contents[:]
            self.section_names = view.section_names.copy()
            self.input_gt = view.input_gt
        else:
            self.t = terminal
            self.contents = []
            self.input_gt = input_gt
            self.section_names = dict()

    def clear(self):
        self.contents = []

    def push(self, content, section_name=None):
        self.set_section(section_name, length=1)
        self.contents.append(content)

    def push_if_new(self, content, section_name=None):
        self.set_section(section_name, length=1)
        if content not in self.contents:
            self.push(content)

    def set_section(self, section_name, length=1):
        if section_name == None:
            return
        i = len(self.contents)
        self.section_names[section_name] = (i, i+length)

    def pop_section(self, section_name):
        start, end = self.section_names.pop(section_name)
        ct = self.contents
        self.contents = ct[:start] + ct[end:]

    def revert_to_before_section(self, section_name):
        start, end = self.section_names.pop(section_name)
        ct = self.contents
        self.contents = ct[:start]

    def contains_section(self, section_name):
        return section_name in self.section_names

    def extend(self, content, section_name=None):
        self.set_section(section_name, length=len(content))
        self.contents.extend(content)

    def vpad(self, n=1):
        """returns n (default 1) newline, to be used when adding content
        """
        return '\n'*n

    def render_execute(self, execute):
        """execute is a method to be run while showing the contents
        whatever execute returns will be returned by render. No 
        arguments are passed to it.
        """
        with self.t.fullscreen():
            for v in self.contents:
                print(v)
            if self.input_gt:
                print('> ', end='')
            return execute()

def raw_input_prompt():
    return raw_input('> ')


class Terminal(QuizInterfaceBase):
    """This is the base user interface for an ExamPrepper quiz.
    Extend and implement it in subclasses, catering to different views.
    """

    def __init__(s):
        from blessed import Terminal as BlessedTerminal
        s.t = BlessedTerminal()
        s.qa_view = View(s.t)
        s.init_view = View(s.t)
        
    def set_media_folder(s, path):
        s.media_folder = path

    def parse_uint_list(s, line, unique=False):
        """Takes a string comprising one line
        and returns a list of nonnegative integers.
        Understands spaces, commas, and semicolons.
        Interprets colon as an INCLUSIVE range operator.
        Understands step operator in a range.

        If unique is set to True, it will return only the first
        encountered instance of each value.
        """
        elems = re.compile('(\d+)(?::(?P<end>\d+))?(?::(?P<step>\d+))?')
        op = []
        parts = elems.findall(line)

        for val in parts:
            v0 = int(val[0])
            if len(val[1]) > 0:
                v1 = int(val[1]) + 1
                if len(val[2]) > 0:
                    v2 = int(val[2])
                    op.extend(range(v0,v1,v2))
                    continue
                op.extend(range(v0,v1))
                continue
            op.append(v0)

        if unique:
            for i in range(len(op)):
                for k in range(len(op)-1,i, -1):
                    if op[i] == op[k]:
                        op.pop(k)
        return op

    def select_categories(s, categories):
        """Allow the user to pick categories.
        Returns a list of selected categories.
        """
        view = View(s.t)
        view.extend(["Please select the categories you want to be quizzed in by entering their numbers.", 
                     "You can quickly select a range by using e.g. 3:7, instead of saying 3,4,5,6,7.",
                     "You may select all categories by just pressing Enter."],
                     section_name='instructions')
        
        cats = []
        for i,cat in enumerate(categories):
            cats.append('{index}: ({length}) {name}'.format(index=str(i+1).rjust(3), 
                                                            length=str(len(cat)), 
                                                            name=cat.name))
        view.extend(cats + [view.vpad()], section_name='categories')

        idx = None
        while True:
            # res = s.render(op, raw_input)
            res = view.render_execute(raw_input_prompt)
            if RE_WHITESPACE.match(res): # Empty line
                idx = range(len(categories))
                break
            idx = map(lambda x: x-1, s.parse_uint_list(res))
            if len(idx) > 0:
                break
            view.push_if_new("Something is wrong with your input. Read the rules and try again.", section_name='error_msg')

        return [categories[i] for i in idx]

    def select_ordering(s, order_options):
        """order_options is a list of methods, each defining a type of ordering.
        Each method has an instructive docstring, which can be used to explain it
        to a user. 
        Allow user to pick an ordering of the questions and categories.

        Returns one of the methods in order_options
        """
        view = View(s.t)
        view.extend(["Please select an ordering that suits your needs by entering its corresponding number.", view.vpad()])

        for i, option in enumerate(order_options):
            view.push("Press {} for: {}".format(i+1, option.__doc__).replace('\n', ''))

        while True:
            try:
                inp = int(view.render_execute(raw_input_prompt))
            except ValueError as ve:
                pass
            else:
                if 1 <= inp <= len(order_options):
                    index = inp-1
                    return order_options[index]
            view.push_if_new("Sorry, not understood. Enter a number from 1 to {}.".format(len(order_options)))


    def select_repetition_lag(self):
        """Allow user to select how many questions should pass before 
        a previously failed question is asked again.
        Returns an integer or a two-tuple of integers.
        In the future, this might change to a range, allowing for some randomness.
        Put the decision in s.repetition_lag, and set it to a negative value 
        to just put the failed question at the end of the queue.
        """
        return 1 # TODO
        # raise NotImplementedError('Abstract method - implement it yourself!')

    def show_current_info(self, quiz_conductor):
        """Display whatever info you think the user would like to see.
        quiz_conductor is the object in charge of the quiz, and
        can give a lot of different information about it.
        Called before display_question.
        """ 
        pass # TODO
        # raise NotImplementedError('Abstract method - implement it yourself!')

    def show_question(self, qa):
        """Present the given question to the user.
        """
        if self.qa_view.contains_section('question'):
            self.qa_view.revert_to_before_section('question')
        q = ["Question:", qa.question, '-'*(self.t.width/2)]
        self.qa_view.extend(q, section_name='question')

    def show_answer(self, qa):
        """Show the reference answer to the user.
        """
        a = ["True answer:", qa.answer, '-'*(self.t.width/2)]
        self.qa_view.extend(a, section_name='answer')
    
    def get_response(self):
        """Returns the user's response to the current question
        """
        self.qa_view.push('Your answer (end with an empty line):', section_name='response_prompt')
        def handler():
            out = []
            while True:
                inp = raw_input_prompt()
                if inp == '':
                    return out
                out.append(inp)
        response = self.qa_view.render_execute(handler)
        response = ['> ' + r for r in response]
        self.qa_view.extend(response + ['-'*(self.t.width/2)], section_name='response')
        return response

    def get_evaluation(self):
        """Returns the user's evaluation of their own current response.
        True for a correct response, False for incorrect.
        """
        self.qa_view.push("Was your answer ok? y/n", section_name='eval_prompt')
        while True:
            inp = self.qa_view.render_execute(raw_input_prompt)
            if inp.lower() == 'y':
                self.qa_view.push('> ' + inp)
                return True
            elif inp.lower() == 'n':
                self.qa_view.push('> ' + inp)
                return False
            else:
                self.qa_view.push_if_new("Sorry, not understood. y or n, please", section_name='error_msg')

    def make_progress_bar(s, nchars, progress,
        end_char='|', covered_char='=', current_pos_char='>', uncovered_char=' '):
        """Returns a string of length nchars
        progress 
            A float between 0 and 1
        end_char 
            A symbol used to delimit the progress bar. Can be set to None.
        covered_char 
            The symbol used for the already covered progress.
        current_pos_char 
            The symbol used to indicate the current progress position.
        uncovered_char 
            The symbol used for what part remains to be covered by the progress.
            Defaults to space.

        Example:
        make_progress_bar(14, 0.75)
        >> |========>   |
        """
        pb = []
        if end_char == None or len(end_char) == 0: 
            end_char = ''
        else:
            nchars -= 2
        p = int(round(nchars * progress))

        pb.append(end_char)
        pb.extend(covered_char*(p-1))
        pb.append(current_pos_char)
        pb.extend(uncovered_char*(nchars-p))
        pb.append(end_char)
        
        return ''.join(pb)

# End of class Terminal