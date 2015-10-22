from __future__ import print_function
import os

print("You should get the blessed package. Try 'pip install blessed'.")

class Term(object):
    """A dummy object for a poor simulation of blessed's fullscreen
    """
    def __enter__(s):
        os.system('cls' if os.name == 'nt' else 'clear')

    def __exit__(s, exc_type, exc_val, exc_tb):
        pass

class Terminal(object):
    """A simple BlessedTerminal emulator hack, for people
    who don't have blessed, or cannot get it to work.
    """
    def __init__(self):
        self.width = int(os.popen('stty size', 'r').read().split()[1])

    def fullscreen(self):
        return Term()

