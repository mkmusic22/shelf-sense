import datetime
import os

import flet
import backend

FLET_APP_STORAGE_DATA = os.getenv("FLET_APP_STORAGE_DATA") or os.getcwd()
DATABASE_PATH = os.path.join(FLET_APP_STORAGE_DATA, "database.db")
FLET_APP_CONSOLE = os.getenv("FLET_APP_CONSOLE") or "none"
interface = backend.UserData(DATABASE_PATH)


def main(page: flet.Page):
    logged_in = False
    active_tab = 0
    auth_mode = None

    page.title = "ShelfSense"
    page.theme_mode = flet.ThemeMode.SYSTEM

    def show_message(message):
        page.show_dialog(flet.SnackBar(content=flet.Text(message), open=True))

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

    def set_auth_mode(mode):
        nonlocal auth_mode
        auth_mode = mode
        render()

    def submit_auth(username):
        nonlocal logged_in, auth_mode, active_tab
        username = (username or "").strip()
        if not username:
            show_message("Enter a username to continue.")
            return

        if auth_mode == "signup":
            if interface.user_exists(username):
                show_message("That username already exists. Try logging in.")
                auth_mode = "login"
                render()
                return
            interface.user_init(username)
        elif not interface.login_user(username):
            show_message("No account was found with that username. Sign up to get started.")
            return

        logged_in = True
        auth_mode = None
        active_tab = 0
        navigation_bar.selected_index = 0
        render()

    def render_home():
        if not logged_in:
            controls: list[flet.Control] = [
                flet.Text("Your shelves, at a glance", size=24, weight=flet.FontWeight.BOLD),
                flet.Text("Sign up or log in to start managing your inventory."),
                flet.Text(
                    "This prototype uses a username only; it does not use passwords.",
                    size=12,
                ),
            ]
            if auth_mode is None:
                controls.extend([
                    flet.Button("Sign up", on_click=lambda _: set_auth_mode("signup")),
                    flet.OutlinedButton("Log in", on_click=lambda _: set_auth_mode("login")),
                ])
            else:
                username_field = flet.TextField(
                    label="Username",
                    on_submit=lambda _: submit_auth(username_field.value),
                )
                action_label = "Create account" if auth_mode == "signup" else "Log in"
                controls.extend([
                    flet.Text(action_label, size=18, weight=flet.FontWeight.BOLD),
                    username_field,
                    flet.Button(
                        action_label,
                        on_click=lambda _: submit_auth(username_field.value),
                    ),
                    flet.TextButton("Back", on_click=lambda _: set_auth_mode(None)),
                ])
            return flet.Column(controls, spacing=14)

        inventory_controls: list[flet.Control] = [
            flet.Text(
                f"Welcome, {interface.get_user_data()['username']}",
                size=24,
                weight=flet.FontWeight.BOLD,
            ),
            flet.Text("Your inventory"),
        ]
        if not interface.grocery_data:
            inventory_controls.append(
                flet.Text("Your inventory is empty. Add your first item to get started.")
            )
        else:
            inventory_controls.extend(
                flet.ListTile(
                    title=flet.Text(item["name"].title()),
                    subtitle=flet.Text(f"{item['category']} · Expires {item['expiry']}"),
                )
                for item in interface.grocery_data
            )
        return flet.Column(inventory_controls, spacing=12, scroll=flet.ScrollMode.AUTO)

    def render_add_item():
        name_field = flet.TextField(label="Item name")
        mfd_field = flet.TextField(label="Manufactured on (YYYY-MM-DD)")
        category_field = flet.TextField(label="Category")
        expiry_field = flet.TextField(label="Expires on (YYYY-MM-DD)")

        def save_item(_):
            name = (name_field.value or "").strip()
            category = (category_field.value or "").strip()
            if not name or not category:
                show_message("Enter both an item name and category.")
                return
            try:
                expiry = datetime.date.fromisoformat((expiry_field.value or "").strip())
                mfd_date = datetime.date.fromisoformat((mfd_field.value or "").strip())
            except ValueError:
                show_message("Enter both dates in YYYY-MM-DD format.")
                return
            if expiry < mfd_date:
                show_message("Expiry date cannot be earlier than the manufacture date.")
                return

            interface.add_item(
                name,
                mfd_date.isoformat(),
                datetime.date.today().isoformat(),
                category,
                expiry.isoformat(),
            )
            interface.push_to_db()
            show_message(f"{name} added to your inventory.")
            render()

        controls: list[flet.Control] = [
            flet.Text("Add an item", size=24, weight=flet.FontWeight.BOLD),
            name_field,
            mfd_field,
            category_field,
            expiry_field,
            flet.Button(content="Save item", on_click=save_item),
        ]
        return flet.Column(controls, spacing=14)

    def logout(_):
        nonlocal logged_in, auth_mode, active_tab
        logged_in = False
        auth_mode = None
        active_tab = 0
        navigation_bar.selected_index = 0
        render()

    def render_settings():
        def set_theme(mode):
            page.theme_mode = mode
            page.update()

        controls: list[flet.Control] = [
            flet.Text("Settings", size=24, weight=flet.FontWeight.BOLD),
            flet.Text(f"Username: {interface.get_user_data()['username']}"),
            flet.Text("Appearance"),
            flet.Row([
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
            ], wrap=True),
            flet.TextButton("Log out", on_click=logout),
        ]
        return flet.Column(controls, spacing=14)

    def render():
        page.clean()
        if active_tab == 1:
            content = render_add_item()
        elif active_tab == 2:
            content = render_settings()
        else:
            content = render_home()
        page.add(flet.Container(content, padding=24, expand=True))

    render()


flet.run(main)
