import backend
import datetime
from typing import cast

interface: backend.UserData = backend.UserData("database.db")
print("\t\t\tShelfSense — Your Local Smart Inventory")
if interface.alr_init:
    print(f"Name: {interface.get_user_data().get('username')}")
    print(f"User ID: {interface.get_user_data().get('id')}")
    print()
    print("Currently in your inventory:")
    print()
    print("Expired Items:")
    if interface.check_to_expire() is None:
        print("No items that are expired at the moment.")
    else:
        for item in interface.check_to_expire():
            print(f"{item['name']}\nManufactured on {item['mfd_date']}\nAdded on {item['add_date']}\nExpired on {item['expiry']}")
else:
    username = input("Enter your permanent username: ")
    interface.user_init(username)
    print(f"Name: {interface.user_data['username']}")
    print(f"User ID: {interface.user_data['id']}") 
print()

while True:
    print("1. Add Item")
    print("2. Remove Item")
    print("3. Check Expired Items")
    print("4. Check Items About to Expire")
    print("5. Exit")
    print()
    input_choice = input("Enter your choice: ")

    if input_choice == "1":
        name = input("Enter the name of the item: ")
        mfd_date = input("Enter the manufacture date of the item (YYYY-MM-DD): ")
        add_date = datetime.date.today().strftime("%Y-%m-%d")
        category = input("Enter the category of the item: ")
        expiry = input("Enter the expiry date of the item (YYYY-MM-DD): ")
        interface.add_item(name, mfd_date, add_date, category, expiry)
        print(f"{name} has been added to your inventory.")
    elif input_choice == "2":
        name = input("Enter the name of the item to remove: ")
        interface.remove_item(name)
        print(f"{name} has been removed from your inventory.")
    elif input_choice == "3":
        expired_items = interface.check_expired()
        if not expired_items:
            print("No items that are expired at the moment.")
        else:
            print("Expired Items:")
            for item in expired_items:
                print(f"{item['name']}\nManufactured on {item['mfd_date']}\nAdded on {item['add_date']}\nExpired on {item['expiry']}")
    elif input_choice == "4":
        to_expire_items = interface.check_to_expire()
        if not to_expire_items:
            print("No items that are about to expire at the moment.")
        else:
            print("Items About to Expire:")
            for item in to_expire_items:
                print(f"{item['name']}\nManufactured on {item['mfd_date']}\nAdded on {item['add_date']}\nExpires on {item['expiry']}")
    elif input_choice == "5":
        interface.push_to_db()
        print("Exiting. Thank you for logging on to ShelfSense. Will refresh expired items on next load.")
        break