# pyExamPrepper
A lightweight quiz program for user-created quizzes. Useful for reading up on exams or the family structure of the in-laws!

## Quiz syntax
- Lines starting with '?' are questions
- A question can span multiple lines, provided that each line is prepended with '?'
- Answers are 1 or more non-empty lines, and must be immediately after a question
- Answers end with the beginning of a new question, or with an empty line
- Categories are plain lines that are not part of an answer, i.e. free-standing. They may be followed directly by a question.
- Categories span only one line
- Empty categories are ignored.
- A category is empty if it is not followed by any questions before the next category or the end of the file.
- Lines are considered a comment and ignored if the first non-whitespace character is a percentage sign, %.
- Comment lines can be placed anywhere; in a question, in an answer, before or after a category. They are ignored regardless.
- Media files may be referred to in questions and answers, using square brackets around the file name at the beginning of a line. Only works in OSX so far, though.

### To be implemented
- The media folder may be specified in the first line of the quiz file as MEDIA:relative_path_from_quiz_file_parent_directory
    + E.g. MEDIA:quizmedia, or MEDIA:../../Documents/flags

### Feature demonstrating quiz
*If you are looking in the raw file, note that the actual quiz should not be indented. The quiz is also in the file examples/syntax_demo.ep*

    Basics
    ?My first question (start with question mark)
    And the first answer (immediately following the question)
    ?My second question
    % A sneaky comment between question and answer; it will be ignored
    And the second answer (it will be seen as immediately following the question, since the comment is ignored)
    % Another comment
    ?My third question
    My third answer

    Multiline options
    ?This question
    ?can span many
    ?lines
    And its answer
    can span many lines,
    as well (but doesn't have to)
    ?You want an empty line in your question?
    Just use whitespace! This could be a single space with the space bar, as here:
     
    The question continues here, as the preceding line is not empty.

    This line is ignored - it will not show up in the quiz, as it is neither a question nor a non-empty category.

        % indented comments
        % are also possible

    Future category (not implemented yet)
    ?[south_korea_flag.png]
    ?Which country has this flag?
    South Korea!
    ?What bird is this?
    ?[mockingbird.wav]
    The mockingbird
    ?Draw the schematics for a simple rectifier.
    [rectifier.jpg]
