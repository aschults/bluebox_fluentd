import sys
import re
import argparse
import json
import requests
import string


class MyFormatter(string.Formatter):
    def get_field(self, field_name, args, kwargs):
        try:
            return string.Formatter.get_field(self, field_name, args, kwargs)
        except Exception as e:
            return ('', field_name)


def parse_args():
    parser = argparse.ArgumentParser(
        description=
        'Read Fluent messages from file (exec output) and call URL.',
        fromfile_prefix_chars='@')

    parser.add_argument(
        'files',
        metavar='file',
        type=argparse.FileType('r'),
        nargs='+',
        help='Files to read from')

    parser.add_argument(
        '--method',
        dest='method',
        action='store',
        default='GET',
        help='HTTP Method to use.')

    parser.add_argument(
        '--url',
        dest='url',
        action='store',
        required=True,
        help='URL (pattern) to use when calling out.')

    parser.add_argument(
        '--content_type',
        dest='content_type',
        action='store',
        default=None,
        help='URL (pattern) to use when calling out.')

    parser.add_argument(
        '--content',
        dest='content',
        action='store',
        help='Request content (pattern).')

    parser.add_argument(
        '--msg_re',
        dest='msg_re',
        action='store',
        default='',
        help='Regex to parse the message body with.')

    parser.add_argument(
        '--response_re',
        dest='response_re',
        action='store',
        default='',
        help='Regex to match with the HTTP response for success.')

    parser.add_argument(
        '--msg_json',
        dest='msg_json',
        action='store_true',
        help='Interpret message as JSON.')

    parser.add_argument(
        '-v', dest='verbose', action='store_true', help='Switch to verbose.')

    return parser.parse_args()


class LineParser(object):
    def __init__(self, parse_message_re=None, parse_message_json=False):
        self.message_re = None
        if parse_message_re:
            self.message_re = re.compile(parse_message_re)

        self.with_json = parse_message_json

    def parse_line(self, l):
        try:
            data = json.loads(l)
        except Exception as e:
            raise Exception("log line:\n{}\nException:\n{}".format(l,e))

        if self.with_json:
            try:
                msg = json.loads(data["message"])
                data["message"] = msg
                #data.update(("message_{}".format(k), v)
                #            for (k, v) in msg.iteritems())
            except Exception as e:
                raise Exception("log message:\n{}\nException:\n{}".format(l,e))
        elif self.message_re:
            match = self.message_re.match(data["message"])
            if not match:
                raise Exception("Content does not match content_re")
            msg = match.groupdict()
            data["message"] = msg
        return data


class RequestHandler(object):
    def __init__(self,
               url_format,
               content_format=None,
               method="GET",
               content_type=None,
               verbose=False):
        self.url_format = url_format

        self.content_format = content_format
        if self.content_format.startswith("@"):
            with open(self.content_format[1:]) as content_file:
                self.content_format = content_file.read()

        self.method = method
        self.headers = {}
        if content_type:
            self.headers['Content-Type'] = content_type
        self.fmt = MyFormatter()
        self.verbose = verbose

    def do_request(self, **data):
        expanded_url = self.fmt.format(self.url_format, **data)

        content_expanded = None
        if self.content_format:
            content_expanded = self.fmt.format(self.content_format, **data)

        if self.verbose:
            sys.stderr.write(str(data))
            sys.stderr.write("\n")
            sys.stderr.write(str(expanded_url))
            sys.stderr.write("\n")
            sys.stderr.write(str(content_expanded))
            sys.stderr.write("\n")

        return requests.request(
            self.method, expanded_url, headers=self.headers, data=content_expanded)


def main():
    args = parse_args()
    response_re = re.compile(args.response_re)

    line_parser = LineParser(args.msg_re, args.msg_json)
    request_handler = RequestHandler(
        args.url,
        method=args.method,
        content_type=args.content_type,
        content_format=args.content,
        verbose=args.verbose)

    for f in args.files:
        for l in f.readlines():
            try:
                data = line_parser.parse_line(l)
                resp = request_handler.do_request(**data)

                if resp.status_code != 200:
                    raise Exception(
                        "HTTP returned status {}".format(resp.status_code))

                if not response_re.search(resp.text):
                    raise Exception(
                        "HTTP successful but does not contain re. Content:\n{}".
                        format(resp.text))
            except Exception as e:
                sys.stderr.write(str(e))
                sys.stderr.write("\n")

if __name__ == "__main__":
    main()
