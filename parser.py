from quiz_handler import Category, QuestionAnswer
from itertools import groupby
import re

QUESTION_LINE_RE = re.compile('^\?.*')
MEDIA_CONTENT_RE = re.compile('^\??(?:\[([^\]]+)\])+')
COMMENT_LINE_RE = re.compile('^\s*%.*')


def extract_media(line):
    """Extracts text written in square brackets
    at the beginning of the line. More than one 
    may be found. Returns whatever remains of 'line',
    and a list of found media names
    """
    media = []
    while line.startswith('['):
        n = line.find(']')
        media.append(line[1:n])
        line = line[n+1:]
    return line, media

def extract_QuestionAnswer(lines):
    """Returns a QuestionAnswer.
    lines is a list of strings, and must be guaranteed to
    contain only a full, proper question and answer.
    """
    assert not any([COMMENT_LINE_RE.match(L) for L in lines]), "lines must not contain comments."
    assert not any([L == '' for L in lines]), "no empty lines are allowed in a question-answer."

    grouped = list(groupby(lines, lambda x: bool(QUESTION_LINE_RE.match(x[0]))))
    assert 1 == sum([k for k,g in grouped]), "A QA must contain at least one question line, and question must be consecutive across lines."
    assert len(grouped) == 2, "An error occured - more than one question or one answer is considered part of this qa."
    
    # question
    question_media = []
    question_text = []
    answer_media = []
    answer_text = []

    for i,line in enumerate(lines):
        if not QUESTION_LINE_RE.match(line):
            break
        line, media = extract_media(line[1:])
        question_media.extend(media)
        question_text.append(line)

    for line in lines[i:]:
        line, media = extract_media(line)
        answer_media.extend(media)
        answer_text.append(line)
    
    qa = QuestionAnswer(''.join(question_text), 
                        ''.join(answer_text), 
                        question_media, 
                        answer_media)

    return qa


class LineParser(object):
    def __init__(s):
        s.current_category = Category('Default')
        s.categories = []
        s.qa_buffer = []
        s.building_question = False
        s.building_answer = False
        s.discarded_text = []
        s.comments = []
        s.line_number = -1

    def clear(s):
        s.qa_buffer = []
        s.building_answer = False
        s.building_question = False

    def store_discarded_qa(s):
        if len(s.qa_buffer) > 0:
            i = s.line_number - len(s.qa_buffer)
            for L in s.qa_buffer:
                i += 1
                s.discarded_text.append((i,L))
        s.qa_buffer = []

    def store_discarded_category(s, category):
        if 'line_number' in category:
            i = category.line_number
        else:
            i = '<' + str(s.line_number)
        s.discarded_text.append((i,category.name))

    def flush_qa(s):
        """flush the buffer for the current question/answer
        into a QuestionAnswer, and put it in the current category.
        """
        if len(s.qa_buffer) == 0:
            return
        qa = extract_QuestionAnswer(s.qa_buffer)
        s.current_category.append(qa)
        s.clear()

    def flush_category(s, new_category_name=None):
        """flush the buffer for the current category
        putting it into the list of categories iff the
        category contains questions.
        """
        if len(s.current_category) != 0:
            s.categories.append(s.current_category)
        else:
            s.store_discarded_category(s.current_category)

        if new_category_name:
            s.current_category = Category(new_category_name)
        else:
            s.current_category = Category('Default')

    def parse_line(s, line):
        s.line_number += 1
        if COMMENT_LINE_RE.match(line):
            s.comments.append(line)
            return
        if line == '\n':
            if s.building_question:
                # Abandon question
                s.store_discarded_qa()
                s.clear()
            elif s.building_answer:
                # flush_qa QA
                s.flush_qa()
            return
        if QUESTION_LINE_RE.match(line):
            if not s.building_question:
                # flush_qa qa, begin
                s.flush_qa()
                s.building_question = True
            s.qa_buffer.append(line)
            return
            # else
        if s.building_question: # and line does not match the question line re:
            s.building_question = False
            s.building_answer = True
        if s.building_answer:
            s.qa_buffer.append(line)
            return
        s.flush_category(line)

    def close(s):
        s.flush_qa()
        s.flush_category()

    def get_parsed(s):
        return s.categories

    def get_discarded(s):
        return s.discarded_text


def parse(file_path):
    """Interprets a quiz file in the given path, and returns
    the parsed list of categories
    """

    p = LineParser()

    with open(file_path) as f:
        for i, line in enumerate(f):
            p.parse_line(line)
        p.close()

    # print "Discarded text from quiz file:"
    # for L,val in p.get_discarded():
        # print str(L).rjust(5), val

    return p.get_parsed()
