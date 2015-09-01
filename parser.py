from quiz_handler import Category, QuestionAnswer

QUESTION_START_SYMBOL = '?'
ANSWER_START_SYMBOL = '#'
MEDIA_START_SYMBOL = '['
MEDIA_END_SYMBOL = ']'
LINE_COMMENT_SYMBOL = '%'

def extract_media_filenames(line):
    """Returns a tuple: First is line without media filenames,
    second is a tuple of media filenames
    """

    media_filenames = []
    while line.startswith(MEDIA_START_SYMBOL): # Take all media filenames: [image.png][sound.wav]Question proceeds here
        endsym = line.find(MEDIA_END_SYMBOL)
        if endsym > 0:
            media_filenames.append(line[1:endsym])
            line = line[endsym+1:]

    return line, tuple(media_filenames)


def parse(file_path):
    """Interprets a quiz file in the given path, and returns
    the parsed list of categories
    """

    current_category = Category('unnamed')
    categories = []

    def flush():
        qa = QuestionAnswer(current_question, current_answer, question_media_filenames, answer_media_filenames)
        current_category.append(qa)

    with open(file_path) as f:
        building_question = False
        building_answer = False
        current_question = None
        current_answer = None
        question_media_filenames = None
        answer_media_filenames = None
        last_line = ''

        for line in f:
            if line[0] == LINE_COMMENT_SYMBOL:
                continue
            if line[0] == QUESTION_START_SYMBOL:
                if building_answer:
                    building_answer = False
                    # Flush question and answer.
                    flush()
                building_question = True
                current_question, question_media_filenames = extract_media_filenames(line[1:])
                
            elif line[0] == ANSWER_START_SYMBOL:
                building_question = False
                building_answer = True
                current_answer, answer_media_filenames = extract_media_filenames(line[1:])
            elif building_question:
                current_question += line
            elif building_answer:
                if line != '\n':
                    current_answer += line
                else:
                    building_answer = False
                    # Flush question and answer.
                    flush()
            elif line != '\n':
                if len(current_category) > 0:
                    categories.append(current_category)
                current_category = Category(line)

    # End of file. Wrap up:
    if building_answer:
            # Flush question and answer.
            flush()
    if len(current_category) > 0:
        categories.append(current_category)

    return categories
