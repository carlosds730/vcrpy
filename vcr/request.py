import StringIO
from six.moves.urllib.parse import urlparse, parse_qsl


class Request(object):
    """
    VCR's  representation of a request.

    There is a weird quirk in HTTP.  You can send the same header twice.  For
    this reason, headers are represented by a dict, with lists as the values.
    However, it appears that HTTPlib is completely incapable of sending the
    same header twice.  This puts me in a weird position: I want to be able to
    accurately represent HTTP headers in cassettes, but I don't want the extra
    step of always having to do [0] in the general case, i.e.
    request.headers['key'][0]

    In addition, some servers sometimes send the same header more than once,
    and httplib *can* deal with this situation.

    Futhermore, I wanted to keep the request and response cassette format as
    similar as possible.

    For this reason, in cassettes I keep a dict with lists as keys, but once
    deserialized into VCR, I keep them as plain, naked dicts.
    """

    def __init__(self, method, uri, body, headers):
        self.method = method
        self.uri = uri
        self._was_file = hasattr(body, 'read')
        self._body = body.read() if self._was_file else body
        self.headers = {}
        for key in headers:
            self.add_header(key, headers[key])

    @property
    def body(self):
        return StringIO.StringIO(self._body) if self._was_file else self._body

    @body.setter
    def body(self, value):
        self._body = value

    def add_header(self, key, value):
        # see class docstring for an explanation
        if isinstance(value, (tuple, list)):
            self.headers[key] = value[0]
        else:
            self.headers[key] = value

    @property
    def scheme(self):
        return urlparse(self.uri).scheme

    @property
    def host(self):
        return urlparse(self.uri).hostname

    @property
    def port(self):
        parse_uri = urlparse(self.uri)
        port = parse_uri.port
        if port is None:
            port = {'https': 443, 'http': 80}[parse_uri.scheme]
        return port

    @property
    def path(self):
        return urlparse(self.uri).path

    @property
    def query(self):
        q = urlparse(self.uri).query
        return sorted(parse_qsl(q))

    # alias for backwards compatibility
    @property
    def url(self):
        return self.uri

    # alias for backwards compatibility
    @property
    def protocol(self):
        return self.scheme

    def __str__(self):
        return "<Request ({0}) {1}>".format(self.method, self.uri)

    def __repr__(self):
        return self.__str__()

    def _to_dict(self):
        return {
            'method': self.method,
            'uri': self.uri,
            'body': self.body,
            'headers': dict(((k, [v]) for k, v in self.headers.items())),
        }

    @classmethod
    def _from_dict(cls, dct):
        return Request(**dct)
