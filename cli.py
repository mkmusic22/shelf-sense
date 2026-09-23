import backend
interface = backend.UserData("database.db")
interface.groceryData()
print("\t\t\tShelfSense — Your Local Smart Inventory")
if interface.alr_init:
print(f"Name: {interface.user_data['username']}")
print(f"User ID: {interface.user_data['id']}")
print()
print("Currently in your inventory:")
print()
print("Expired Items:")
if interface.check_to_expire() isNone:
print("No items that are expired at the moment.")
else:
for item in interface.check_to_expire():
print(f"{item['name']}\nManufactured on {item['mfd_date']}\nAdded on {item['add_date']}\nExpired on {item['expiry']}")
