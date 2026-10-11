import datetime
import os

import flet
import backend


FLET_APP_STORAGE_DATA = os.getenv("FLET_APP_STORAGE_DATA") or os.getcwd()
DATABASE_PATH = os.path.join(FLET_APP_STORAGE_DATA, "database.db")

interface = backend.UserData(DATABASE_PATH)

# Items expiring within this many days are shown as "expiring soon".
# Uses the same value as the backend so the colours and the list agree.
WARNING_DAYS = interface.DEFAULT_WARNING_DAYS

CATEGORIES = [
    "Fruits",
    "Vegetables",
    "Dairy",
    "Meat",
    "Fish & Seafood",
    "Bakery",
    "Grains",
    "Canned Food",
    "Frozen Food",
    "Snacks",
    "Beverages",
    "Spices & Condiments",
    "Sweets",
    "Other",
]
# Python should implement enums soon ;-;

def main(page: flet.Page):

    # The app remembers the user from the last session (username is
    # entered once). Change to `False` to always show the login screen.
    logged_in = interface.alr_init
    active_tab = 0
    auth_mode = None

    page.title = "ShelfSense"
    page.theme_mode = flet.ThemeMode.SYSTEM

    # =========================================================
    # MESSAGE
    # =========================================================

    def show_message(message):
        page.show_dialog(
            flet.SnackBar(
                content=flet.Text(message),
                open=True,
            )
        )

    # =========================================================
    # NAVIGATION
    # =========================================================

    def navigate(event):
        nonlocal active_tab

        selected_tab = event.control.selected_index

        if selected_tab in (1, 2) and not logged_in:
            navigation_bar.selected_index = 0
            active_tab = 0
            render()
            show_message("Sign up or log in before opening this section.")
            return

        active_tab = selected_tab
        render()

    navigation_bar = flet.NavigationBar(
        destinations=[
            flet.NavigationBarDestination(
                icon=flet.Icons.HOME,
                selected_icon=flet.Icons.HOME,
                label="Home",
            ),
            flet.NavigationBarDestination(
                icon=flet.Icons.ADD,
                selected_icon=flet.Icons.ADD,
                label="Add Item",
            ),
            flet.NavigationBarDestination(
                icon=flet.Icons.SETTINGS,
                selected_icon=flet.Icons.SETTINGS,
                label="Settings",
            ),
        ],
        on_change=navigate,
    )

    page.navigation_bar = navigation_bar

    # =========================================================
    # AUTH
    # =========================================================

    def set_auth_mode(mode):
        nonlocal auth_mode
        auth_mode = mode
        render()

    def submit_auth(username):
        nonlocal logged_in
        nonlocal auth_mode
        nonlocal active_tab

        username = (username or "").strip()

        if not username:
            show_message("Enter a username to continue.")
            return

        # ---- sign up ----
        if auth_mode == "signup":

            if interface.user_exists(username):
                show_message("That username already exists. Try logging in.")
                auth_mode = "login"
                render()
                return

            try:
                interface.user_init(username)
            except ValueError as error:
                show_message(str(error))
                return

        # ---- log in ----
        elif not interface.login_user(username):
            show_message(
                "No account was found with that username. "
                "Sign up to get started."
            )
            return

        logged_in = True
        auth_mode = None
        active_tab = 0
        navigation_bar.selected_index = 0

        render()

    # =========================================================
    # INVENTORY HELPERS
    # =========================================================

    def get_status(expiry_text):
        """Return (colour, label) for an item's expiry date."""
        try:
            expiry_date = datetime.date.fromisoformat(str(expiry_text))
        except ValueError:
            return flet.Colors.GREY, "Invalid date"

        days_left = (expiry_date - datetime.date.today()).days

        if days_left < 0:
            return flet.Colors.RED, "Expired"

        if days_left == 0:
            label = "Today"
        elif days_left == 1:
            label = "1 day"
        else:
            label = f"{days_left} days"

        if days_left <= WARNING_DAYS:
            return flet.Colors.AMBER, label

        return flet.Colors.GREEN, label

    def remove_item_clicked(item_id):
        removed = interface.remove_item(item_id)
        render()

        if removed:
            show_message("Item removed from your inventory.")
        else:
            show_message("Could not remove that item.")

    def build_cards(items):
        """One card per item: easy to read on a narrow phone screen."""

        cards = []

        for item in items:

            color, days_text = get_status(item["expiry"])

            details = (
                f"Mfd: {item.get('mfd_date') or '-'}   "
                f"Added: {item.get('add_date') or '-'}"
            )

            cards.append(
                flet.Container(
                    content=flet.Row(
                        [
                            # ---- left: name and details ----
                            flet.Column(
                                [
                                    flet.Text(
                                        item["name"].title(),
                                        size=18,
                                        weight=flet.FontWeight.BOLD,
                                        color=color,
                                    ),
                                    flet.Text(
                                        f"{item['category']}  ·  "
                                        f"Expires {item['expiry']}",
                                        size=13,
                                    ),
                                    flet.Text(
                                        details,
                                        size=11,
                                        color=flet.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            # ---- right: days left and delete ----
                            flet.Column(
                                [
                                    flet.Text(
                                        days_text,
                                        size=15,
                                        weight=flet.FontWeight.BOLD,
                                        color=color,
                                    ),
                                    flet.IconButton(
                                        icon=flet.Icons.DELETE_OUTLINE,
                                        tooltip="Remove item",
                                        icon_color=flet.Colors.RED,
                                        on_click=lambda _, item_id=item["id"]:
                                            remove_item_clicked(item_id),
                                    ),
                                ],
                                spacing=0,
                                horizontal_alignment=flet.CrossAxisAlignment.END,
                            ),
                        ],
                        vertical_alignment=flet.CrossAxisAlignment.START,
                    ),
                    padding=12,
                    border=flet.Border.all(1.5, color),
                    border_radius=12,
                )
            )

        return flet.Column(cards, spacing=10)

    # =========================================================
    # HOME
    # =========================================================

    def render_home():

        # ---- not logged in ----
        if not logged_in:

            controls: list[flet.Control] = [
                flet.Text(
                    "Your shelves, at a glance",
                    size=24,
                    weight=flet.FontWeight.BOLD,
                ),
                flet.Text(
                    "Sign up or log in to start managing your inventory."
                ),
                flet.Text(
                    "This prototype uses a username only; "
                    "it does not use passwords.",
                    size=12,
                ),
            ]

            if auth_mode is None:

                controls.extend([
                    flet.Button(
                        "Sign up",
                        on_click=lambda _: set_auth_mode("signup"),
                    ),
                    flet.OutlinedButton(
                        "Log in",
                        on_click=lambda _: set_auth_mode("login"),
                    ),
                ])

            else:

                username_field = flet.TextField(
                    label="Username",
                    on_submit=lambda _: submit_auth(username_field.value),
                )

                action_label = (
                    "Create account" if auth_mode == "signup" else "Log in"
                )

                controls.extend([
                    flet.Text(
                        action_label,
                        size=18,
                        weight=flet.FontWeight.BOLD,
                    ),
                    username_field,
                    flet.Button(
                        action_label,
                        on_click=lambda _: submit_auth(username_field.value),
                    ),
                    flet.TextButton(
                        "Back",
                        on_click=lambda _: set_auth_mode(None),
                    ),
                ])

            return flet.Column(controls, spacing=14)

        # ---- logged in ----
        controls = [
            flet.Text(
                f"Welcome, {interface.get_user_data()['username']}",
                size=24,
                weight=flet.FontWeight.BOLD,
            ),
        ]

        if not interface.grocery_data:

            controls.append(
                flet.Container(
                    content=flet.Text(
                        "Your inventory is empty. "
                        "Add your first item to get started."
                    ),
                    padding=20,
                )
            )

            return flet.Column(controls, spacing=12)

        expired_items = interface.check_expired()
        soon_items = interface.check_to_expire()

        # ---- expired items (separate section) ----
        if expired_items:
            controls.extend([
                flet.Text(
                    f"Expired ({len(expired_items)})",
                    size=18,
                    weight=flet.FontWeight.BOLD,
                    color=flet.Colors.RED,
                ),
                build_cards(expired_items),
            ])

        # ---- expiring soon (separate section) ----
        if soon_items:
            controls.extend([
                flet.Text(
                    f"Expiring within {WARNING_DAYS} days ({len(soon_items)})",
                    size=18,
                    weight=flet.FontWeight.BOLD,
                    color=flet.Colors.AMBER,
                ),
                build_cards(soon_items),
            ])

        if not expired_items and not soon_items:
            controls.append(
                flet.Text("Nothing is expired or expiring soon.")
            )

        # ---- full inventory ----
        controls.extend([
            flet.Text(
                f"All items ({len(interface.grocery_data)})",
                size=18,
                weight=flet.FontWeight.BOLD,
            ),
            build_cards(interface.grocery_data),
        ])

        return flet.Column(
            controls,
            spacing=12,
            scroll=flet.ScrollMode.AUTO,
        )

    # =========================================================
    # ADD ITEM
    # =========================================================

    def render_add_item():

        name_field = flet.TextField(label="Item name")

        category_field = flet.Dropdown(
            label="Food category",
            options=[
                flet.DropdownOption(key=category, text=category)
                for category in CATEGORIES
            ],
        )

        current_year = datetime.date.today().year

        def create_date_dropdowns(label):

            day_dropdown = flet.Dropdown(
                label="Day",
                width=110,
                options=[
                    flet.DropdownOption(key=str(day), text=str(day))
                    for day in range(1, 32)
                ],
            )

            month_dropdown = flet.Dropdown(
                label="Month",
                width=150,
                options=[
                    flet.DropdownOption(
                        key=str(month),
                        text=datetime.date(2000, month, 1).strftime("%B"),
                    )
                    for month in range(1, 13)
                ],
            )

            year_dropdown = flet.Dropdown(
                label="Year",
                width=120,
                options=[
                    flet.DropdownOption(key=str(year), text=str(year))
                    for year in range(current_year - 10, current_year + 21)
                ],
            )

            return (
                flet.Text(label, size=16, weight=flet.FontWeight.BOLD),
                flet.Row(
                    [day_dropdown, month_dropdown, year_dropdown],
                    spacing=10,
                    wrap=True,
                ),
                day_dropdown,
                month_dropdown,
                year_dropdown,
            )

        (
            manufacture_title,
            manufacture_row,
            mfd_day,
            mfd_month,
            mfd_year,
        ) = create_date_dropdowns("Manufacturing date")

        (
            expiry_title,
            expiry_row,
            expiry_day,
            expiry_month,
            expiry_year,
        ) = create_date_dropdowns("Expiry date")

        def get_date(day_dropdown, month_dropdown, year_dropdown):
            """Returns a date, None if incomplete, or "invalid"."""

            if (
                not day_dropdown.value
                or not month_dropdown.value
                or not year_dropdown.value
            ):
                return None

            try:
                return datetime.date(
                    int(year_dropdown.value),
                    int(month_dropdown.value),
                    int(day_dropdown.value),
                )
            except ValueError:
                return "invalid"

        def save_item(_):
            nonlocal active_tab

            name = (name_field.value or "").strip()
            category = category_field.value

            if not name:
                show_message("Enter an item name.")
                return

            if not category:
                show_message("Select a food category.")
                return

            mfd_date = get_date(mfd_day, mfd_month, mfd_year)
            expiry_date = get_date(expiry_day, expiry_month, expiry_year)

            if mfd_date is None or expiry_date is None:
                show_message(
                    "Select both manufacturing and expiry dates."
                )
                return

            if mfd_date == "invalid" or expiry_date == "invalid":
                show_message("Please select valid dates.")
                return

            if expiry_date < mfd_date:
                show_message(
                    "Expiry date cannot be earlier than the "
                    "manufacture date."
                )
                return

            # The backend saves the item straight away and sets the
            # "date added" itself. It also re-validates the dates.
            try:
                interface.add_item(
                    name,
                    mfd_date.isoformat(),
                    None,
                    category,
                    expiry_date.isoformat(),
                )
            except ValueError as error:
                show_message(str(error))
                return

            # Go back to Home so the new item is visible.
            active_tab = 0
            navigation_bar.selected_index = 0
            render()

            show_message(f"{name} added to your inventory.")

        controls: list[flet.Control] = [
            flet.Text(
                "Add an item",
                size=24,
                weight=flet.FontWeight.BOLD,
            ),
            name_field,
            category_field,
            manufacture_title,
            manufacture_row,
            expiry_title,
            expiry_row,
            flet.Button("Save item", on_click=save_item),
        ]

        return flet.Column(
            controls,
            spacing=14,
            scroll=flet.ScrollMode.AUTO,
        )

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(_):
        nonlocal logged_in
        nonlocal auth_mode
        nonlocal active_tab

        logged_in = False
        auth_mode = None
        active_tab = 0
        navigation_bar.selected_index = 0

        render()

    # =========================================================
    # SETTINGS
    # =========================================================

    def render_settings():

        def set_theme(mode):
            page.theme_mode = mode
            page.update()

        controls: list[flet.Control] = [
            flet.Text(
                "Settings",
                size=24,
                weight=flet.FontWeight.BOLD,
            ),
            flet.Text(
                f"Username: {interface.get_user_data()['username']}"
            ),
            flet.Text("Appearance"),
            flet.Row(
                [
                    flet.OutlinedButton(
                        "Light",
                        on_click=lambda _: set_theme(flet.ThemeMode.LIGHT),
                    ),
                    flet.OutlinedButton(
                        "Dark",
                        on_click=lambda _: set_theme(flet.ThemeMode.DARK),
                    ),
                    flet.OutlinedButton(
                        "System",
                        on_click=lambda _: set_theme(flet.ThemeMode.SYSTEM),
                    ),
                ],
                wrap=True,
            ),
            flet.TextButton("Log out", on_click=logout),
        ]

        return flet.Column(controls, spacing=14)

    # =========================================================
    # MAIN RENDER
    # =========================================================

    def render():

        page.clean()

        if active_tab == 1:
            content = render_add_item()
        elif active_tab == 2:
            content = render_settings()
        else:
            content = render_home()

        page.add(
            flet.SafeArea(
                content=flet.Container(
                    content,
                    padding=24,
                    expand=True,
                ),
                expand=True,
            )
        )

    # =========================================================
    # START APP
    # =========================================================

    render()


flet.run(main)
