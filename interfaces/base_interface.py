# encoding: utf-8


class QuizInterfaceBase(object):
    """This is the base user interface for an ExamPrepper quiz.
    Extend and implement it in subclasses, catering to different views.
    """

    def set_media_folder(s, path):
        s.media_folder = path

    def select_categories(s, categories):
        """Allow the user to pick categories.
        Returns a list of selected categories.
        """
        raise NotImplementedError('select_categories is an abstract method - implement it yourself!')

    def select_ordering(s, order_options):
        """order_options is a list of methods, each defining a type of ordering.
        Each method has an instructive docstring, which can be used to explain it
        to a user. 
        Allow user to pick an ordering of the questions and categories.

        Returns one of the methods in order_options
        """
        raise NotImplementedError('select_ordering is an abstract method - implement it yourself!')

    def select_repetition_lag(s):
        """Allow user to select how many questions should pass before 
        a previously failed question is asked again.
        Returns an integer or a two-tuple of integers.
        In the future, this might change to a range, allowing for some randomness.
        Put the decision in s.repetition_lag, and set it to a negative value 
        to just put the failed question at the end of the queue.
        """
        raise NotImplementedError('select_repetition_lag is an abstract method - implement it yourself!')

    def show_current_info(s, quiz_conductor):
        """Display whatever info you think the user would like to see.
        quiz_conductor is the object in charge of the quiz, and
        can give a lot of different information about it.
        Called before display_question.
        """
        raise NotImplementedError('show_current_info is an abstract method - implement it yourself!')

    def show_question(s, qa):
        """Present the given question to the user.
        """
        raise NotImplementedError('show_question is an abstract method - implement it yourself!')

    def show_answer(s, qa):
        """Show the reference answer to the user.
        """
        raise NotImplementedError('show_answer is an abstract method - implement it yourself!')
    
    def get_response(s):
        """Returns the user's response to the current question
        """
        raise NotImplementedError('get_response is an abstract method - implement it yourself!')

    def get_evaluation(s):
        """Returns the user's evaluation of their own current response.
        True for a correct response, False for incorrect.
        """
        raise NotImplementedError('get_evaluation is an abstract method - implement it yourself!')

# End of class QuizInterfaceBase