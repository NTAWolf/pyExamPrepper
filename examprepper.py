# encoding: utf-8

def run(interface, file_path, media_path_rel='./media'):
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
    qc = QuizConductor(categories)
    qc.run(interface)
