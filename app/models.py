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
        return '<User {}>'.format(self.nickname)


class ProxySettings(db.Model):
    """Store proxy settings in database."""

    id = db.Column(db.Integer, primary_key=True)
    proxy_name = db.Column(db.String(25), index=True, unique=True)
    proxy_settings = db.Column(db.String(255), index=True, unique=True)

    def __repr__(self):
        """Proxy settings."""
        return '<Proxy setting {}>'.format(self.proxy_name)


class DeviceType(db.Model):
    """Device type stored in database."""

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(30), index=True)
    model = db.Column(db.String(30), index=True)
    hardware_category = db.Column(db.String(30), index=True)
    netmiko_category = db.Column(db.Text, index=True)
    device = db.relationship('Device', backref='devicetype', lazy='dynamic')

    def __repr__(self):
        """Device type."""
        return '<Devicetype {}>'.format(self.model)


class Device(db.Model):
    """Store devices in database."""

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(64), index=True, unique=True)
    ipv4_addr = db.Column(db.String(15), index=True, unique=True)
    local_creds = db.Column(db.Boolean, default=False)
    devicetype_id = db.Column(db.Integer, db.ForeignKey(DeviceType.id))
    proxy_id = db.Column(db.Integer, db.ForeignKey(ProxySettings.id))

    def __repr__(self):
        """Devices."""
        return '<Device {}>'.format(self.hostname)
