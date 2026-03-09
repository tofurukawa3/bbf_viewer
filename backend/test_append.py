from app.parser import generate_netconf_edit_config

xml1 = generate_netconf_edit_config("Device.WLAN.SSID.{i}.SSID", "TestSSID")
print("First generated XML:")
print(xml1)

xml2 = generate_netconf_edit_config("Device.WLAN.SSID.{i}.Enable", "true", existing_xml=xml1)
print("\nSecond generated XML (Appended):")
print(xml2)
