from app import db
from math import ceil


class User(db.Model):
    """Not used."""

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    username = db.Column(db.String(15), index=True, unique=True)
    password = db.Column(db.String(20), index=True)

    def __repr__(self):
        """Not used."""
        return '<User %r>' % (self.nickname)


class Devicetype(db.Model):
    """Device type stored in database."""

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(30), index=True)
    model = db.Column(db.String(30), index=True)
    netmiko_cat = db.Column(db.Text, index=True)
    device = db.relationship('Host', backref='devicetype')

    def __repr__(self):
        """Device type."""
        return '<Devicetype %r>' % (self.model)


class Host(db.Model):
    """Store devices in database."""

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(64), index=True, unique=True)
    ipv4_addr = db.Column(db.String(15), index=True, unique=True)
    type = db.Column(db.Text)
    ios_type = db.Column(db.String(15), index=True)
    local_creds = db.Column(db.Boolean, default=False)
    devicetype_id = db.Column(db.Integer, db.ForeignKey('devicetype.id'))

    def __repr__(self):
        """Devices."""
        return '<Host %r>' % (self.hostname)


class Pagination(object):
    """Pagination class for local database."""

    def __init__(self, page, per_page, total_count):
        """Init method."""
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        """Multiple pages method."""
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """Prev page method."""
        return self.page > 1

    @property
    def has_next(self):
        """Next page method."""
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """Iterate pages method."""
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
