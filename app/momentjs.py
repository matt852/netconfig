#!/usr/bin/python3

from jinja2 import Markup


class MomentJS(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, fmt):
        return Markup("<script>\ndocument.write(moment(\"%s\").%s);\n</script>" %
                      (self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z"), fmt))

    def format(self, fmt):
        return self.render("format(\"%s\")" % fmt)

    def calendar(self):
        return self.render("calendar()")

    def from_now(self):
        return self.render("from_now()")
