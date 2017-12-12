from device_definitions.cisco import CiscoIOS, CiscoNXOS, CiscoASA

# The keys of this dictionary are the supported device_types
CLASS_MAPPER= {
	'cisco_ios': CiscoIOS,
	'cisco_iosxe': CiscoIOS,
	'cisco_nxos': CiscoNXOS,
	'cisco_asa': CiscoASA
}

platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_str = "\n".join(platforms)
platforms_str = "\n" + platforms_str

def DeviceHandler(*args, **kwargs):
	"""Factory function selects the proper class and creates object based on ios_type."""
	if kwargs['ios_type'] not in platforms:
		raise ValueError('Unsupported ios_type: currently supported platforms are: {}'.format(platforms_str))
	DeviceClass = device_dispatcher(kwargs['ios_type'])
	return DeviceClass(*args, **kwargs)

def device_dispatcher(ios_type):
	"""Select the class to be instantiated based on vendor/platform."""
	return CLASS_MAPPER[ios_type]