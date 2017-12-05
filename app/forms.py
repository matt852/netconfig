from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, BooleanField, HiddenField, SelectField, RadioField, IntegerField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, IPAddress
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class LoginForm(FlaskForm):
    user = StringField('Username', validators=[DataRequired()])
    pw = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class GetConfigForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    host = StringField('Host', validators=[DataRequired()])
    user = StringField('Username', validators=[DataRequired()])
    pw = PasswordField('Password', validators=[DataRequired()])

class GetInterfaceConfigForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    port = StringField('Port', validators=[DataRequired()])
    user = StringField('Username', validators=[DataRequired()])
    pw = PasswordField('Password', validators=[DataRequired()])

class AddHostForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    ipv4_addr = StringField('IPv4 Address', validators=[DataRequired(), IPAddress()])
    hosttype_choices = [('', ''), ('Switch', 'Switch'), ('Router', 'Router'), ('Firewall', 'Firewall')]
    hosttype = SelectField('Host Type', choices=hosttype_choices, validators=[DataRequired()])
    ios_type_choices = [('cisco_ios', 'IOS'), ('cisco_asa', 'ASA'), ('cisco_nxos', 'NX-OS'), ('cisco_xe', 'IOS-XE')]
    ios_type = SelectField('IOS Type', choices=ios_type_choices, validators = [DataRequired()])

class ImportHostsForm(FlaskForm):
    csvimport = StringField('Devices to Import via CSV format', widget=TextArea())

class DeleteHostsForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])

class EditInterfaceForm(FlaskForm):
    datavlan = StringField('Data Vlan')
    voicevlan = StringField('Voice Vlan')
    other = StringField('Other', widget=TextArea())
    host = HiddenField('Host')
    interface = HiddenField('Interface')

class EditHostForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    ipv4_addr = StringField('IPv4 Address', validators=[DataRequired()])
    hosttype_choices = [('', ''), ('Switch', 'Switch'), ('Router', 'Router'), ('Firewall', 'Firewall')]
    hosttype = SelectField('Host Type', choices=hosttype_choices, validators=[DataRequired()])
    ios_type_choices = [('', ''), ('cisco_ios', 'IOS'), ('cisco_asa', 'ASA'), ('cisco_nxos', 'NX-OS'), ('cisco_xe', 'IOS-XE'), ('cisco_wlc_ssh', 'WLC')]
    ios_type = SelectField('IOS Type', choices=ios_type_choices, validators=[DataRequired()])

class CustomCommandsForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    command = StringField('Commands', widget=TextArea())

class CustomCfgCommandsForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    command = StringField('Commands', widget=TextArea())

class FWACLGeneratorForm(FlaskForm):
    hostname = QuerySelectField('Firewall', validators=[DataRequired()], get_label='hostname')
    changeTicket = StringField('Change Ticket', validators=[DataRequired()])
    changeDesc = StringField('Change Description', validators=[DataRequired()], render_kw={"placeholder": "(1-3 words max)"})
    sourceIP = StringField('Source IP Addresses & Subnet Masks', widget=TextArea(), render_kw={"placeholder": "[ip.addr] [netmask]:\n10.0.0.0 255.255.255.0\n10.1.1.1 255.255.255.255"})
    destIP = StringField('Destination IP Addresses & Subnet Masks', widget=TextArea(), render_kw={"placeholder": "[ip.addr] [netmask]:\n10.0.0.0 255.255.255.0\n10.1.1.1 255.255.255.255"})
    ports = StringField('Ports & Protocols', widget=TextArea(), render_kw={"placeholder": "[port] [protocol]:\n80 TCP\n161 UDP"})

class FWCheckOpenPortsForm(FlaskForm):
    hostname = QuerySelectField('Firewall', get_label='hostname')
    sourceIP = StringField('Source IP Address', render_kw={"placeholder": "[x.x.x.x]"})
    destIP = StringField('Destination IP Address', render_kw={"placeholder": "[x.x.x.x]"})
    port = StringField('Port', render_kw={"placeholder": "[1-65535]"})
    protocol = StringField('Protocol', render_kw={"placeholder": "[TCP/UDP/ICMP]"})
