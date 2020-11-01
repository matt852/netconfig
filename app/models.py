#!/usr/bin/python3

from app import db


class User(db.Model):
    """Not used."""

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    username = db.Column(db.String(15), index=True, unique=True)
    password = db.Column(db.String(20), index=True)

    def __repr__(self):
        """Not used."""
        return '<User %r>' % self.nickname


class DeviceType(db.Model):
    """Device type stored in database."""

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(30), index=True)
    model = db.Column(db.String(30), index=True)
    netmiko_category = db.Column(db.Text, index=True)
    device = db.relationship('Device', backref='devicetype', lazy='dynamic')

    def __repr__(self):
        """Device type."""
        return '<Devicetype %r>' % self.model


class Device(db.Model):
    """Store devices in database."""

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(64), index=True, unique=True)
    ipv4_addr = db.Column(db.String(15), index=True, unique=True)
    type = db.Column(db.Text)
    ios_type = db.Column(db.String(15), index=True)
    local_creds = db.Column(db.Boolean, default=False)
    devicetype_id = db.Column(db.Integer, db.ForeignKey('devicetype.id'))
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxysettings.id'))

    def __repr__(self):
        """Devices."""
        return '<Device %r>' % self.hostname


class ProxySettings(db.Model):
    """Store proxy settings in database."""

    id = db.Column(db.Integer, primary_key=True)
    proxy_name = db.Column(db.String(25), index=True, unique=True)
    proxy_settings = db.Column(db.String(255), index=True, unique=True)

    def __repr__(self):
        """Proxy settings."""
        return '<Proxy setting %r>' % self.proxy_name
