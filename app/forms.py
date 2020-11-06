#!/usr/bin/python3

from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, BooleanField
from wtforms.fields import HiddenField, SelectField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, IPAddress


class LocalCredentialsForm(FlaskForm):
    """Local credentials form, on a per device basis."""

    local_creds_used = HiddenField('LocalCredsUsed')
    user = StringField('Username', validators=[DataRequired()])
    pw = PasswordField('Login Password', validators=[DataRequired()])
    privpw = PasswordField('Privileged Password (if applicable)')


class AddDeviceForm(FlaskForm):
    """Add new device to local database form."""

    # TODO: Abstract out choices
    hostname = StringField('Hostname', validators=[DataRequired()])
    ipv4_addr = StringField('IPv4 Address', validators=[DataRequired(), IPAddress()])
    device_type = SelectField('Device Type', choices=list(), validators=[DataRequired()])
    local_creds = BooleanField('Use Local/Different Credentials', default=False)


class AddDeviceTypeForm(FlaskForm):
    """Add new device type to local database form."""

    # TODO: Abstract out choices
    brand_choices = [('', ''),
                     ('cisco', 'Cisco')]
    brand = SelectField('Brand', choices=brand_choices, validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    hardware_category_choices = [('', ''),
                           ('switch', 'Switch'),
                           ('router', 'Router'),
                           ('firewall', 'Firewall')]
    hardware_category = SelectField('Hardware Category', choices=hardware_category_choices, validators=[DataRequired()])
    netmiko_category_choices = [('', ''),
                                ('cisco_ios', 'IOS'),
                                ('cisco_asa', 'ASA'),
                                ('cisco_nxos', 'NX-OS'),
                                ('cisco_xe', 'IOS-XE')]
    netmiko_category = SelectField('OS Type', choices=netmiko_category_choices, validators=[DataRequired()])


class ImportDevicesForm(FlaskForm):
    """Import devices into local database using CSV format."""

    csvimport = StringField('Devices to Import via CSV format', widget=TextArea())


class EditInterfaceForm(FlaskForm):
    """Edit device interface form."""

    datavlan = StringField('Data Vlan')
    voicevlan = StringField('Voice Vlan')
    other = StringField('Other', widget=TextArea())
    device = HiddenField('Device')
    interface = HiddenField('Interface')


class EditDeviceForm(FlaskForm):
    """Edit device in local database form."""

    hostname = StringField('Hostname')
    ipv4_addr = StringField('IPv4 Address', validators=[IPAddress()])
    device_type = SelectField('Device Type', choices=list())
    local_creds = BooleanField('Use Local/Different Credentials', default=False)


class CustomCommandsForm(FlaskForm):
    """Bulk commands form."""

    hostname = StringField('Hostname', validators=[DataRequired()])
    command = StringField('Commands', widget=TextArea())


class CustomCfgCommandsForm(FlaskForm):
    """Bulk configuration commands form."""

    hostname = StringField('Hostname', validators=[DataRequired()])
    command = StringField('Commands', widget=TextArea())


class ProxySettingsForm(FlaskForm):
    """Proxy settings page form."""

    proxy_settings_choices = [('', '(create new)'),
                              ('test', 'TEST')]
    proxy_settings = SelectField('Edit proxy settings', choices=proxy_settings_choices)
    proxy_name = StringField('Name', validators=[DataRequired()])
    proxy_ip = StringField('IP Address', validators=[DataRequired(), IPAddress()])
    proxy_key = StringField('SSH Key')
    proxy_edit = StringField('Settings', widget=TextArea())
