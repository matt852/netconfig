import unittest
from app.device_classes.device_definitions.cisco.cisco_nxos import CiscoNXOS
try:
    import mock
except ImportError:
    from unittest import mock


class TestCiscoNXOS(unittest.TestCase):
    """CI testing class for Cisco NXOS devices."""

    @mock.patch.object(CiscoNXOS, 'run_ssh_command')
    def test_pull_interface_mac_addresses(self, mocked_method):
        """Test MAC address table formatting."""
        device = CiscoNXOS('na', 'na', 'na', 'na', 'na', 'na')
        device.interface = 'Eth1/1'

        mocked_method.return_value = '''
<?xml version="1.0" encoding="ISO-8859-1"?>
<nf:rpc-reply xmlns:nf="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="http://www.cisco.com/nxos:1.0:l2fm">
 <nf:data>
  <show>
   <mac>
    <address-table>
     <__XML__OPT_Cmd_show_mac_addr_tbl_static>
      <__XML__OPT_Cmd_show_mac_addr_tbl_address>
       <__XML__BLK_Cmd_show_mac_addr_tbl_address_3>
        <__XML__OPT_Cmd_show_mac_addr_tbl_address>
         <interface>
          <__XML__INTF_interface-name>
           <__XML__PARAM_value>
            <__XML__INTF_output>port-channel50</__XML__INTF_output>
           </__XML__PARAM_value>
          </__XML__INTF_interface-name>
         </interface>
        </__XML__OPT_Cmd_show_mac_addr_tbl_address>
       </__XML__BLK_Cmd_show_mac_addr_tbl_address_3>
       <__XML__OPT_Cmd_show_mac_addr_tbl___readonly__>
        <__readonly__>
         <header> Note: MAC table entries displayed are getting read from software.
 Use the 'hardware-age' keyword to get information related to 'Age'

 </header>
         <header>Legend:
        * - primary entry, G - Gateway MAC, (R) - Routed MAC, O - Overlay MAC
        age - seconds since last seen,+ - primary entry using vPC Peer-Link,
        (T) - True, (F) - False ,  ~~~ - use 'hardware-age' keyword to retrieve age info
</header>
         <header>   VLAN     MAC Address      Type      age     Secure NTFY Ports/SWID.SSID.LID
</header>
         <header>---------+-----------------+--------+---------+------+----+------------------
</header>
         <TABLE_mac_address>
          <ROW_mac_address>
           <disp_mac_addr>1234.5678.90ab</disp_mac_addr>
           <disp_type>* </disp_type>
           <disp_vlan>1</disp_vlan>
           <disp_is_static>disabled</disp_is_static>
           <disp_age>0</disp_age>
           <disp_is_secure>disabled</disp_is_secure>
           <disp_is_ntfy>disabled</disp_is_ntfy>
           <disp_port>port-channel1</disp_port>
          </ROW_mac_address>
          <ROW_mac_address>
           <disp_mac_addr>90ab.1234.5678</disp_mac_addr>
           <disp_type>* </disp_type>
           <disp_vlan>10</disp_vlan>
           <disp_is_static>disabled</disp_is_static>
           <disp_age>0</disp_age>
           <disp_is_secure>disabled</disp_is_secure>
           <disp_is_ntfy>disabled</disp_is_ntfy>
           <disp_port>Ethernet1/1</disp_port>
          </ROW_mac_address>
          <ROW_mac_address>
           <disp_mac_addr>5678.90ab.1234</disp_mac_addr>
           <disp_type>* </disp_type>
           <disp_vlan>100</disp_vlan>
           <disp_is_static>disabled</disp_is_static>
           <disp_age>0</disp_age>
           <disp_is_secure>disabled</disp_is_secure>
           <disp_is_ntfy>disabled</disp_is_ntfy>
           <disp_port>port-channel100</disp_port>
          </ROW_mac_address>
         </TABLE_mac_address>
        </__readonly__>
       </__XML__OPT_Cmd_show_mac_addr_tbl___readonly__>
      </__XML__OPT_Cmd_show_mac_addr_tbl_address>
     </__XML__OPT_Cmd_show_mac_addr_tbl_static>
    </address-table>
   </mac>
  </show>
 </nf:data>
</nf:rpc-reply>
]]>]]>
'''

        expected_output = [{'macAddr': '1234.5678.90ab', 'port': 'port-channel1', 'vlan': '1'},
                           {'macAddr': '90ab.1234.5678', 'port': 'Ethernet1/1', 'vlan': '10'},
                           {'macAddr': '5678.90ab.1234', 'port': 'port-channel100', 'vlan': '100'}]

        self.assertEqual(device.pull_interface_mac_addresses(None), expected_output)

if __name__ == '__main__':
    unittest.main()
