# encoding: utf-8

import optparse
from interfaces.terminal import Terminal

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

if __name__ == '__main__':
    parser = optparse.OptionParser("usage: %prog interface_type [options]")
    parser.add_option("-i", "--interface", dest="interface", type="string",
                      default="terminal", help="Interface type. Currently only supporting 'terminal' for a terminal interface.")
    parser.add_option("-f", "--file", dest="file_path", type="string",
                      help="Absolute path to quiz file")
    parser.add_option("-m", "--media", dest="media_path", type="string",
                      default="./media", help="Relative or absolute path to media folder")
    

    parser.add_option("-r", "--repetition_lag", dest="repetition_lag", type="int",
                      default=None, help="Preset. Optional. How far ahead in the queue a failed question should be placed.")
    parser.add_option("-c", "--categories", dest="category_indices", type="string",
                      default=None, help="Preset. Optional list of category indices to use")
    parser.add_option("-o", "--order", dest="order", type="string",
                      default=None,
                      help="""Preset. Optional. Whether and how question order should be randomized. 
                      Choose among random, no_random, random_within_category, 
                      random_between_category, and
                      categories_random_and_random_within_category""")

    options, args = parser.parse_args()

    
    presets = dict()
    if options.order: presets['order'] = options.order
    if options.category_indices: presets['category_indices'] = [int(x) for x in options.category_indices.split(',')]
    if options.repetition_lag: presets['repetition_lag'] = options.repetition_lag

    interface = None
    if options.interface == 'terminal':
        interface = Terminal()
    else:
        print options.interface, "not an implemented interface type"
        raise NotImplementedError()

    run(interface, options.file_path, options.media_path, presets=presets)