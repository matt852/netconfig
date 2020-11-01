import unittest
from app import app, db
from app.plugins.data_handler import DataHandler


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

    def tearDown(self):
        """Cleanup once test completes."""
        del self.datahandler

    def test_add_and_delete_host_in_db(self):
        """Test adding a host to the database is successful."""
        result_add, h_id, err = self.datahandler.add_device_to_db("test", "192.168.1.5",
                                                            "switch", "cisco_ios",
                                                                  False)

        # Delete host from db if above adding was successful
        if result_add:
            result_delete = self.datahandler.delete_host_in_db(h_id)
        else:
            # Force test failure
            assert True is False

        # Verify adding host worked
        assert result_add is True
        assert result_delete is True

    def test_import_hosts_to_db(self):
        """Test importing hosts to database."""
        csv_data = """
10Test,10.0.1.1,Switch,IOS,True
11Test,10.0.1.2,Router,IOS-XE,False
12Test,10.0.1.3,Firewall,ASA
13Test,10.0.1.4,Switch
14Test,10.0.1.5,blah,Router
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
        err_expect = [{'hostname': '13Test', 'error': 'Invalid number of fields in entry'},
                      {'hostname': '14Test', 'error': 'Invalid device type'},
                      {'hostname': '15Test', 'error': 'Invalid OS type'},
                      {'hostname': '16Test', 'error': 'Invalid number of fields in entry'},
                      {'hostname': '17Test', 'error': 'Invalid IP address'}]
        # {'hostname': '18Test', 'error': 'Duplicate hostname - already exists in database'} <---need to test
        # {'hostname': '18Test', 'error': 'Duplicate IP address - already exists in database'} <---need to test

        hosts_result, err_result = self.datahandler.import_devices_to_db(csv_data)
        for x, y in zip(hosts_expect, hosts_result):
            self.assertEqual(x['hostname'], y['hostname'])
            self.assertEqual(x['ipv4_addr'], y['ipv4_addr'])
            self.assertEqual(x['id'], y['id'])

        for x, y in zip(err_expect, err_result):
            self.assertEqual(x['hostname'], y['hostname'])
            self.assertEqual(x['error'], y['error'])
