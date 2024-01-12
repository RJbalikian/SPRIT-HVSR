import inspect
import typing_extensions

_old_getfile = inspect.getfile
def _getfile(object):
    """
    Override inspect.getfile to try to return __file__ from the given frame
    """
    if inspect.isframe(object):
        try:
            file = object.f_globals['__file__']
            # print("inspect.getfile returning %s" % file)
            return file
        except:
            pass
    return _old_getfile(object)
inspect.getfile = _getfile