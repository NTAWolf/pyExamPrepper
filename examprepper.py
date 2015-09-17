# encoding: utf-8

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
    import argparse
    
    parser = argparse.ArgumentParser(description="CLI for starting the examprepper")
    parser.add_argument("-i", "--interface", dest="interface",default="terminal", 
                        help="Interface type. Currently only supporting 'terminal' for a terminal interface.")
    parser.add_argument("-f", "--file", dest="file_path", required=True,
                        help="Absolute path to quiz file")
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

    run(interface, args.file_path, args.media_path, presets=presets)