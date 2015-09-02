# pyExamPrepper
A lightweight quiz program for user-created quizzes. Useful for reading up on exams or the family structure of the in-laws!

## Upcoming, revised quiz syntax
- Use ? to show that the line is a question
- Questions can span multiple lines, provided that each line is prepended with ?
Answers always immediately follow questions. If there is a blank line after - the question, it is ignored.
- Answers may span multiple nonempty lines
Categories are non-question that are not part of an answer, i.e. lines that - come after an empty line or another category.
- Categories can only span one line.
Categories are ignored if they are empty, i.e. are not followed by any - questions before the end of file, or next category.
- Media files may be referred to in questions and answers, using square brackets around the file name at the beginning of a line.

### example
    ?What does the French flag look like?
    [french_flag.png]
    ?What is the meaning of this figure?
    ?[somefigure.jpg]
    Yadda yadda answer here