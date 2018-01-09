from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
host = Table('host', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('hostname', String(length=64)),
    Column('ipv4_addr', String(length=15)),
    Column('type', Text),
    Column('ios_type', String(length=15)),
    Column('local_creds', Boolean),
    Column('devicetype_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['host'].columns['local_creds'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['host'].columns['local_creds'].drop()
