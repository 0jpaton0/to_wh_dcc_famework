import os
import ctypes
import urllib.parse


_resolvers = {}
""":type : dict[str, callable]"""


def resolve(uri):
    """
    Resolve a URI in to a file path.

    e.g.:
        "env://PROJECT_ROOT/content/characters/squid.ma" => "d:/p4/workspace/project/content/characters/squid.ma"

    :param uri: URI.
    :type uri: basestring
    :return: Resolved URI as file path. If no resolver for the scheme can be found, None will be returned.
    :rtype: unicode | None
    """
    p = urllib.parse.urlparse(uri)

    scheme = str(p.scheme)
    if scheme in _resolvers:
        path = _resolvers[scheme](p)
        if path is not None:
            if isinstance(path, str):
                path = path
            path = os.path.abspath(path)
        return path
    else:
        raise ValueError('No resolve handler for scheme `{0}`'.format(p.scheme))


# noinspection PyPep8Naming
class resolver(object):
    """
    Decorator to register a class as a resolver. The class must have a `resolve` method that takes a path parameter as a
    string, and returns a resolved path as a string.
    """
    def __init__(self, scheme):
        """
        :param scheme: URI scheme to register for.
        :type scheme: str
        """
        self.scheme = scheme

    def __call__(self, cls):
        _resolvers[self.scheme] = cls.resolve
        return cls


@resolver('framework')
class FrameworkPathResolver(object):

    @classmethod
    def resolve(cls, p):
        print('\nin framework :: {}'.format(p))


@resolver('env')
class EnvironmentPathResolver(object):

    @classmethod
    def resolve(cls, p):
        print('\nin env :: {}'.format(p))


@resolver('module')
class PackagePathResolver(object):

    @classmethod
    def resolve(cls, p):
        print('\nin module :: {}'.format(p))


ui_file=resolve('env://cooldog/cooldogwindow.ui')