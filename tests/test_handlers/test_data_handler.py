import unittest
import os
from app import app, db
from app.data_handler import DataHandler
from app.models import Host


class TestDataHandler(unittest.TestCase):
    """Unit testing for data handler class."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.datahandler = DataHandler('local')

        # use a memory database rather than using app.db
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
        db.session.close()
        db.drop_all()
        db.create_all()

    def test_addHostToDB(self):
        """
        Test adding a host to the database is successful
        """
        b, h_id, err = self.datahandler.addHostToDB("test", "192.168.56.2",
                                                    "switch", "cisco_ios",
                                                    False)
        assert b is True

    def test_importHostsToDB(self):
        csv_data = """
10Test,10.0.1.1,Switch,IOS,True
11Test,10.0.1.2,Router,IOS-XE,False
12Test,10.0.1.3,Firewall,ASA
13Test,10.0.1.4,Switch
14Test,10.0.1.5,blah
15Test,10.0.1.6,Switch,OSS
16Test,10.0.1.7
17Test,10.500.999.8,Switch,IOS,False
18Test,10.0.0.88,Switch,IOS,True
19Test,10.0.0.1,Firewall,NX-OS
20Test,10.0.1.9,Switch,IOS,False
        """

        hosts_expect = [{'hostname': '10Test', 'ipv4_addr': '10.0.1.1',
                        'id': 1},
                        {'hostname': '11Test', 'ipv4_addr': '10.0.1.2',
                        'id': 2},
                        {'hostname': '12Test', 'ipv4_addr': '10.0.1.3',
                        'id': 3},
                        {'hostname': '18Test', 'ipv4_addr': '10.0.0.88',
                        'id': 4},
                        {'hostname': '19Test', 'ipv4_addr': '10.0.0.1',
                        'id': 5},
                        {'hostname': '20Test', 'ipv4_addr': '10.0.1.9',
                        'id': 6}]
        err_expect = [{'host': '13Test', 'error': 'Invalid entry'},
                      {'host': '14Test', 'error': 'Invalid entry'},
                      {'host': '15Test', 'error': 'Invalid OS type'},
                      {'host': '16Test', 'error': 'Invalid entry'},
                      {'host': '17Test', 'error': 'Invalid IP address'}]

        hosts_result, err_result = self.datahandler.importHostsToDB(csv_data)
        assert hosts_expect == hosts_result
        assert err_expect == err_result
