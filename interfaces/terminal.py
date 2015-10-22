# encoding: utf-8
from __future__ import print_function

from base_interface import QuizInterfaceBase
import re
import platform
import readline
from textwrap import TextWrapper

RE_WHITESPACE = re.compile("^\s*$")

class View(object):
    def __init__(self, terminal=None, input_gt=False, view=None):
        self.t = terminal
        self.contents = []
        self.input_gt = input_gt
        self.section_names = dict()
        self.textwrapper = TextWrapper(width=self.t.width, replace_whitespace=False)

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

    def hcenter(self, text):
        """text is a string
        returns text padded with whitespace to center it
        """
        return text.center(self.t.width)

    def render_execute(self, execute, word_wrap=True):
        """execute is a method to be run while showing the contents
        whatever execute returns will be returned by render. No 
        arguments are passed to it.
        """
        with self.t.fullscreen():
            for v in self.contents:
                if word_wrap:
                    print(self.textwrapper.fill(v))
                else:
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
        try:
            from blessed import Terminal as BlessedTerminal
        except ImportError, ie:
            from poor_mans_blessed import Terminal as BlessedTerminal

        s.t = BlessedTerminal()
        s.view = View(s.t)
        
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

    def select_index_from_list(self, length, view, shift=0, select_multiple=False, accept_empty=False):
        # Aaay, this could sure need some clean-up for readability!
        
        error_message = ''.join([view.vpad(),
                                  "Sorry, not understood. Enter ",
                                  "one or more numbers" if select_multiple else "a number",
                                  " from {} to {}.".format(shift, length+shift-1)])
        while True:
            inp = view.render_execute(raw_input_prompt)
            if accept_empty and RE_WHITESPACE.match(inp):
                return []
            if select_multiple:
                idx = map(lambda x: x-1, self.parse_uint_list(inp))
                if len(idx) > 0:
                    return idx
            else:
                try:
                    inp = int(inp)
                except ValueError as ve:
                    pass
                else:
                    if 1 <= inp <= length:
                        index = inp-shift
                        return index
            view.push_if_new(error_message)


    def select_categories(self, categories):
        """Allow the user to pick categories.
        Returns a list of selected categories.
        """
        view = View(self.t)
        view.extend(["Please select the categories you want to be quizzed in by entering their numbers.", 
                     "You can quickly select a range by using e.g. 3:7, instead of saying 3,4,5,6,7.",
                     "You may select all categories by just pressing Enter." + view.vpad()],
                     section_name='instructions')
        
        cats = []
        for i,cat in enumerate(categories):
            cats.append('{index}: ({length}) {name}'.format(index=str(i+1).rjust(3), 
                                                            length=str(len(cat)), 
                                                            name=cat.name))
        view.extend(cats, section_name='categories')
        view.push('')

        idx = self.select_index_from_list(len(categories), view, shift=1, 
                                    select_multiple=True, accept_empty=True)
        if len(idx) == 0:
            idx = range(len(categories))

        return [categories[i] for i in idx]

    def select_ordering(self, order_options):
        """order_options is a list of methods, each defining a type of ordering.
        Each method has an instructive docstring, which can be used to explain it
        to a user. 
        Allow user to pick an ordering of the questions and categories.

        Returns one of the methods in order_options
        """
        view = View(self.t)
        view.push("Please select an ordering that suits your needs by entering its corresponding number." + view.vpad())

        for i, option in enumerate(order_options):
            view.push("Press {} for: {}".format(i+1, option.__doc__).replace('\n', ''))
        view.push('')

        index = self.select_index_from_list(len(order_options), view, shift=1)
        return order_options[index]


    def select_repetition_lag(self):
        """Allow user to select how many questions should pass before 
        a previously failed question is asked again.
        Returns an integer or a two-tuple of integers.
        In the future, this might change to a range, allowing for some randomness.
        Put the decision in s.repetition_lag, and set it to a negative value 
        to just put the failed question at the end of the queue.
        """
        view = View(self.t)
        view.push("How many questions must pass before you get a wrongly answered question again?")
        view.push("Enter a blank line if you don't care" + view.vpad())

        while True:
            inp = view.render_execute(raw_input_prompt)
            if inp == '':
                return 5 # Chosen by fair dice roll. No, really, I found it to be a decent choice.
            try:
                inp = int(inp)
            except ValueError as ve:
                pass
            else:
                return inp
            view.push_if_new("Sorry, not understood. Please enter either nothing or a natural number.")

    def show_current_info(self, quiz_conductor):
        """Display whatever info you think the user would like to see.
        quiz_conductor is the object in charge of the quiz, and
        can give a lot of different information about it.
        Called before display_question.
        """ 

        qc = quiz_conductor
        v = self.view
        v.clear()
        v.push(qc.get_current_category_name())
        
        # Progress bar 1: Progress within category
        pbtext = str(qc.get_completed_questions_in_category_count()) + "/" \
               + str(qc.get_total_questions_in_category_count()) + " in this category."
        pbwidth = min(self.t.width/2, self.t.width-len(pbtext)-1)
        pb = [self.make_progress_bar(pbwidth, qc.get_progress_within_category(), "|", '=', '>', ' ')]
        pb.append(pbtext)
        pb = ' '.join(pb)
        v.push(pb)

        # Progress bar 2: Progress overall
        pbtext = str(qc.get_total_questions_done_count()) + "/" \
               + str(qc.get_total_question_count()) + " in total."
        pb = [self.make_progress_bar(pbwidth, qc.get_total_progress(), "|", '=', '>', ' ')]
        pb.append(pbtext)
        pb = ' '.join(pb)
        v.push(pb)

    def show_question(self, qa):
        """Present the given question to the user.
        """
        if self.view.contains_section('question'):
            self.view.revert_to_before_section('question')
        q = ["Question:", qa.question, '-'*(self.t.width/2)]
        self.show_media(qa.question_media)
        self.view.extend(q, section_name='question')

    def show_answer(self, qa):
        """Show the reference answer to the user.
        """
        a = ["True answer:", qa.answer, '-'*(self.t.width/2)]
        self.show_media(qa.answer_media)
        self.view.extend(a, section_name='answer')
    
    def get_response(self):
        """Returns the user's response to the current question
        """
        self.view.push('Your answer (end with an empty line):', section_name='response_prompt')
        def handler():
            out = []
            while True:
                inp = raw_input_prompt()
                out.append(inp)
                if inp == '':
                    return out
        response = self.view.render_execute(handler)
        response = ['> ' + r for r in response]
        self.view.extend(response + ['-'*(self.t.width/2)], section_name='response')
        return response

    def get_evaluation(self):
        """Returns the user's evaluation of their own current response.
        True for a correct response, False for incorrect.
        """
        self.view.push("Was your answer ok? y/n", section_name='eval_prompt')
        while True:
            inp = self.view.render_execute(raw_input_prompt)
            self.view.push('> ' + inp)
            if inp.lower() == 'y':
                return True
            elif inp.lower() == 'n':
                return False
            else:
                self.view.push("Sorry, not understood. y or n, please", section_name='error_msg')


    def end_of_quiz(self, quiz_conductor, end_options):
        """Tell the user that the quiz is over
        end_options is a list of strings describing what options 
        the user may take now for restarting the quiz.
        Returns a list of indices of the end_options list.
        """
        view = View(self.t)
        self.show_current_info(quiz_conductor)
        view.push(view.vpad())
        view.push(view.hcenter('This is the end of the quiz! Good job!'))
        view.push(view.vpad())
        view.push('Now, select one of the following options:')

        opt = []
        for i,option in enumerate(end_options):
            opt.append('{index}: {description}'.format(index=str(i+1).rjust(3), 
                                                       description=option))
        view.extend(opt + [view.vpad()], section_name='options')

        res = self.select_index_from_list(len(end_options), view, shift=1, select_multiple=False, accept_empty=False)
        return res

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
            nchars -= 2 # Remove end characters from the count
        p = int(round(nchars * progress))

        pb.append(end_char)
        pb.extend(covered_char * p)
        if progress < 1.0: # Don't show current progress char if completed progress
            pb.append(current_pos_char)
        pb.extend(uncovered_char * (nchars - p - 1)) # -1 to make room for the current_pos_char
        pb.append(end_char)
        
        return ''.join(pb)

    def show_media(self, media_list):
        if media_list == None or len(media_list) == 0:
            return
        if platform.system() == 'Darwin': # OSX
            from subprocess import call
            from os.path import join, isfile
            from tempfile import TemporaryFile
            for f in media_list:
                path = join(self.media_folder,f)
                if not isfile(path):
                    self.view.push("There is no file in {}.".format(path))
                    continue
                with TemporaryFile() as f:
                    res = call(['open', path], stderr=f)
                    f.seek(0) # reset file reader
                    msg = f.read() # get potential error message from the 'open' process
                if res != 0:
                    self.view.push(msg)



# End of class Terminal