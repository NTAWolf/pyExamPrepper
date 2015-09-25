# encoding: utf-8

"""This is a command-line interface for starting the examprepper
with a given interface. Available arguments can be found using
    python examprepper --help
In the command line, you may navigate to the folder containing a .ep file
(or .ep.txt, or any file name containg '.ep.' or ending in '.ep')
and just invoke this program directly - it will find the quiz file and open it.
"""

import os


def run(interface, file_path, media_path_rel='./media', presets=None):
    """Runs a quiz using the supplied interface (instance of QuizInterfaceBase)
    and the quiz document in file_path. It looks for media (images, sound) in
    the media_path_rel, which is relative to the file_path.
    """
    from parser import parse
    from quiz_handler import QuizConductor
    from os.path import normpath, join, dirname
    media_folder = normpath(join(dirname(file_path), media_path_rel))
    interface.set_media_folder(media_folder)
    categories = parse(file_path)
    qc = QuizConductor(categories, presets=presets)
    qc.run(interface)

def find_ep_file(directory):
    files = os.listdir(directory)

    for f in files:
        if '.ep.' in f or f.endswith('.ep'):
            return os.path.join(directory, f)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="CLI for starting the examprepper")
    parser.add_argument("-i", "--interface", dest="interface",default="terminal", 
                        help="Interface type. Currently only supporting 'terminal' for a terminal interface.")
    file_arg = parser.add_argument("-f", "--file", dest="file_path", default=None,
                        help="Path to quiz file, absolute or relative. Or path to its containing directory.")
    parser.add_argument("-m", "--media", dest="media_path",
                        default="./media", help="Relative or absolute path to media folder")
    
    parser.add_argument("-r", "--repetition_lag", dest="repetition_lag", type=int,
                      default=None, help="Preset. Optional. How far ahead in the queue a failed question should be placed.")
    parser.add_argument("-c", "--categories", dest="category_indices",
                      default=None, help="Preset. Optional list of category indices to use")
    parser.add_argument("-o", "--order", dest="order",
                      default=None,
                      help="""Preset. Optional. Whether and how question order should be randomized. 
                      Choose among random, no_random, random_within_category, 
                      random_between_category, and
                      categories_random_and_random_within_category""")

    args = parser.parse_args()
    
    presets = dict()
    if args.order: presets['order'] = args.order
    if args.category_indices: presets['category_indices'] = [int(x) for x in args.category_indices.split(',')]
    if args.repetition_lag != None: presets['repetition_lag'] = args.repetition_lag

    interface = None
    if args.interface == 'terminal':
        from interfaces.terminal import Terminal
        interface = Terminal()
    else:
        raise NotImplementedError("{} not an implemented interface type".format(args.interface))

    file_path = args.file_path
    # If no file path given, look for a .ep file in the current directory.
    if file_path == None:
        directory = os.getcwd()
        file_path = find_ep_file(directory)
        if file_path == None:
            raise argparse.ArgumentError(file_arg, "No quiz file given, and no quiz file found in current working directory {}".format(directory))
    # If file path is actually a directory, look for .ep files in that directory
    elif os.path.isdir(file_path):
        directory = file_path
        file_path = find_ep_file(directory)
        if file_path == None:
            raise argparse.ArgumentError(file_arg, "No quiz file (.ep) found in given directory {}".format(directory))

    run(interface, file_path, args.media_path, presets=presets)



