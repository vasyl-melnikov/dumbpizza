import os.path
import time
from enum import Enum
from typing import Dict

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.image import AsyncImage, Image
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import OneLineListItem, MDList
from sqlmodel import SQLModel, create_engine, Session, Field, Relationship
import base64
from models import OrderStatus, User, Admin, OrderMenuItems, MenuItem, Order
from managers import AdminManager, UserManager

# SQLite database URL
DATABASE_URL = "sqlite:///./pizzeria.db"

# User session info
SESSION_FILE = 'session_data.txt'

# Set up SQLite database
engine = create_engine(DATABASE_URL, echo=True)
user_manager = UserManager(engine)
admin_manager = AdminManager(engine)


def gen_metadata():
    SQLModel.metadata.create_all(engine)
    MENU_ITEMS = [
        {"name": "Margherita Pizza",
         "price": 8.99,
         "description": "Classic pizza topped with tomato sauce, mozzarella cheese, and fresh basil leaves.",
         "image": "pizza_img.jpg",
         "weight": 245,
         "radius": 30
         },
        {"name": "Pepperoni Pizza",
         "price": 9.99,
         "description": "Delicious pizza topped with spicy pepperoni slices and mozzarella cheese on a tomato sauce base.",
         "image": "pizza_img.jpg",
         "weight": 245,
         "radius": 30
         },
        {"name": "Vegetarian Pizza",
         "price": 10.99,
         "description": "Healthy pizza loaded with assorted vegetables such as bell peppers, onions, mushrooms, and olives.",
         "image": "pizza_img.jpg",
         "weight": 245,
         "radius": 30
         },
        {"name": "Supreme Pizza",
         "price": 11.99,
         "description": "A flavorful pizza topped with a variety of ingredients including pepperoni, sausage, bell peppers, onions, and mushrooms.",
         "image": "pizza_img.jpg",
         "weight": 245,
         "radius": 30
         }
    ]
    for item in MENU_ITEMS:
        with open(item['image'], 'rb') as f:
            img_data = f.read()
        menu = MenuItem(name=item['name'],
                        description=item['description'],
                        price=item['price'],
                        image=base64.b64encode(img_data).decode('utf-8'),
                        weight=item['weight'],
                        radius=item['radius'])
        admin_manager.insert_menu_item(menu)


class AdminPage:
    def __init__(self, screen_manager, login_page_entrance):
        self.dialog = None
        self.screen_manager = screen_manager
        self.login_page_entrance = login_page_entrance

    def show_admin_order_screen(self):
        orders_screen = Screen(name='orders')

        # Create a scrollable view for orders list
        orders_scroll_view = ScrollView()
        orders_list = MDList(padding=dp(24), spacing=dp(16))
        for order in admin_manager.get_all_orders():
            card = MDCard(size_hint=(None, None), size=(1000, 200),
                          padding=dp(16), spacing=dp(8))
            card.add_widget(MDLabel(text=f"Order ID: {order.id}",
                                    font_style='Subtitle1'))
            card.add_widget(MDLabel(text=f"Created at: {order.created_at}",
                                    font_style='Subtitle1'))
            card.add_widget(MDLabel(text=f"Status: {order.status}",
                                    font_style='Subtitle1'))
            card.add_widget(MDLabel(text=f"{order.user.dict()}",
                                    font_style='Subtitle1'))

            menu_items_text = ""
            for menu_item in order.menu_items:
                menu_items_text += f"{menu_item.name} - ${menu_item.price}\n"
            card.add_widget(
                MDLabel(text=menu_items_text, font_style='Body1',
                        height=dp(100)))

            # Add buttons for controlling order status
            status_button = MDIconButton(
                icon="checkbox-blank-circle-outline",
                pos_hint={'center_x': 0.5})
            status_button.order_id = order.id
            status_button.bind(on_release=self.show_status_menu)
            card.add_widget(status_button)
            orders_list.add_widget(card)

        orders_scroll_view.add_widget(orders_list)

        # Create buttons section as a footer
        buttons_layout = BoxLayout(orientation='horizontal', padding=dp(12),
                                   spacing=dp(12), height=dp(120))
        add_item_button = MDRaisedButton(text="Add Item", size_hint_x=None,
                                         width=dp(120),
                                         on_release=self.add_menu_item)
        back_button = MDRaisedButton(text="Back to Login", size_hint_x=None,
                                     width=dp(120),
                                     on_release=self.back_to_login)
        orders_menu = MDRaisedButton(text="Menu", size_hint_x=None,
                                     width=dp(120),
                                     on_release=self.back_to_menu)
        buttons_layout.add_widget(orders_menu)
        buttons_layout.add_widget(add_item_button)
        buttons_layout.add_widget(back_button)

        orders_screen.add_widget(orders_scroll_view)
        orders_screen.add_widget(buttons_layout)

        self.screen_manager.add_widget(orders_screen)

    def show_status_menu(self, button):
        menu = MDDropdownMenu(
            caller=button,
            items=[{"viewclass": "OneLineListItem",
                    "text": OrderStatus.CREATED.value.title(),
                    "on_release": lambda: self.on_status_change(button.order_id,
                                                                OrderStatus.CREATED.value)},
                   {"viewclass": "OneLineListItem",
                    "text": OrderStatus.COOKING.value.title(),
                    "on_release": lambda: self.on_status_change(button.order_id,
                                                                OrderStatus.COOKING.value)},
                   {"viewclass": "OneLineListItem",
                    "text": OrderStatus.CANCELLED.value.title(),
                    "on_release": lambda: self.on_status_change(button.order_id,
                                                                OrderStatus.CANCELLED.value)},
                   {"viewclass": "OneLineListItem",
                    "text": OrderStatus.READY.value.title(),
                    "on_release": lambda: self.on_status_change(button.order_id,
                                                                OrderStatus.READY.value)},
                   {"viewclass": "OneLineListItem",
                    "text": OrderStatus.DONE.value.title(),
                    "on_release": lambda: self.on_status_change(button.order_id,
                                                                OrderStatus.DONE.value)}
                   ],
            width_mult=4
        )
        # menu.bind(on_release=self.on_status_change)  # Bind on_release event
        menu.open()
        self.dialog = menu

    def on_status_change(self, order_id: int, status: str):
        admin_manager.update_order_status(order_id, OrderStatus(status))
        self.dismiss_dialog()
        self.back_to_orders()

    def show_admin_menu_screen(self):
        menu_list = MDList(padding=dp(24), spacing=dp(16))
        cards = []
        for item in user_manager.get_menu_items():
            card = MDCard(size_hint_y=None, height=dp(200), padding=dp(16),
                          spacing=dp(8))
            card.md_bg_color = "#808080"
            card.add_widget(
                MDLabel(text=item.name, halign='center', font_style='H6'))
            card.add_widget(MDLabel(text=f"Price: ${item.price}", halign='center'))
            card.add_widget(MDLabel(text=f"Weight: {item.weight}", halign='center'))
            card.add_widget(MDLabel(text=f"Radius: {item.radius}", halign='center'))
            card.add_widget(MDLabel(text=item.description, halign='left'))
            if not os.path.exists('assets'):
                os.mkdir('assets')
            with open(os.path.join(f'assets', f'menu_item{item.id}.jpg'), 'wb') as f:
                f.write(base64.b64decode(item.image))
            card.add_widget(AsyncImage(source=os.path.join(f'assets', f'menu_item{item.id}.jpg'),
                                       nocache=True))

            # Add an "Edit" button to each menu item card
            edit_button = MDRaisedButton(text="Edit", size_hint=(None, None),
                                         size=(100, 50))
            edit_button.bind(
                on_release=lambda button, item=item: self.show_edit_popup(item))
            card.add_widget(edit_button)
            cards.append(card)

        for card in cards:
            menu_list.add_widget(card)

        menu_scroll_view = ScrollView()
        menu_scroll_view.add_widget(menu_list)

        buttons_layout = MDBoxLayout(orientation='horizontal', padding=dp(12),
                                     spacing=dp(12))
        add_item_button = MDRaisedButton(text="Add Item", size_hint_x=None,
                                         width=dp(120),
                                         on_release=self.add_menu_item)
        back_button = MDRaisedButton(text="Back to Login", size_hint_x=None,
                                     width=dp(120),
                                     on_release=self.back_to_login)
        orders_button = MDRaisedButton(text="Orders", size_hint_x=None,
                                       width=dp(120),
                                       on_release=self.back_to_orders)
        buttons_layout.add_widget(orders_button)
        buttons_layout.add_widget(add_item_button)
        buttons_layout.add_widget(back_button)

        admin_screen = Screen(name='admin')
        admin_layout = MDBoxLayout(orientation='vertical')
        admin_layout.add_widget(menu_scroll_view)
        admin_screen.add_widget(admin_layout)
        admin_screen.add_widget(buttons_layout)

        self.screen_manager.add_widget(admin_screen)

    def show_edit_popup(self, item):
        # Create a popup window for editing menu item properties
        self.cur_menu_item_edit = item
        popup_content = BoxLayout(orientation='vertical', padding=dp(24),
                                  spacing=dp(16))

        # Add text input fields for editing menu item properties
        name_input = MDTextField(text=item.name, hint_text="Name",  foreground_color=(0, 0, 0, .4))
        price_input = MDTextField(text=str(item.price), hint_text="Price")
        weight_input = MDTextField(text=str(item.weight), hint_text="Weight")
        radius_input = MDTextField(text=str(item.radius), hint_text="Radius")
        description_input = MDTextField(text=item.description,
                                      hint_text="Description")

        popup_content.add_widget(name_input)
        popup_content.add_widget(price_input)
        popup_content.add_widget(weight_input)
        popup_content.add_widget(radius_input)
        popup_content.add_widget(description_input)

        # Add a button to select a new image
        choose_image_button = MDRaisedButton(text="Choose Image")
        choose_image_button.bind(
            on_release=lambda button: self.choose_image(popup_content))
        popup_content.add_widget(choose_image_button)

        # Add a button to save changes
        save_button = MDRaisedButton(text="Save Changes",
                                     size_hint=(None, None), size=(150, 50))
        save_button.bind(
            on_release=lambda button: self.save_menu_item_changes(item,
                                                                  name_input.text,
                                                                  float(
                                                                      price_input.text),
                                                                  description_input.text,
                                                                  float(
                                                                      weight_input.text),
                                                                  float(
                                                                      radius_input.text)))
        popup_content.add_widget(save_button)

        # Create and open the popup
        popup = Popup(title="Edit Menu Item", content=popup_content,
                      size_hint=(None, None), size=(800, 1200),
                      separator_color=[0, 0, 0, 1],
                      background_color=[255, 255, 255, 255],
                      )
        popup.open()
        self.dialog = popup

    def choose_image(self, popup_content):
        self.dialog.background_color = [0, 0, 0, 1]
        # Create a file chooser to select an image
        file_chooser = FileChooserIconView()
        file_chooser.path = '.'  # Set initial path
        file_chooser.bind(
            on_submit=lambda chooser, path, _: self.on_image_selected(path,
                                                                      popup_content))

        # Clear existing widgets and add the file chooser
        popup_content.clear_widgets()
        popup_content.add_widget(file_chooser)

    def on_image_selected(self, path, popup_content):
        # Show the selected image in the popup and provide an option to upload it
        image_preview = Image(source=path[0])
        upload_button = Button(text="Upload Image")
        upload_button.bind(on_release=lambda button: self.upload_image(path))

        # Clear existing widgets and add the image preview and upload button
        popup_content.clear_widgets()
        popup_content.add_widget(image_preview)
        popup_content.add_widget(upload_button)

    def upload_image(self, path):
        with open(path[0], 'rb') as f:
            img_data = f.read()
        self.cur_menu_item_edit.image = base64.b64encode(img_data).decode(
            'utf-8')
        admin_manager.insert_menu_item(self.cur_menu_item_edit)
        self.cur_menu_item_edit = None
        self.dismiss_dialog()
        # self.back_to_menu()

    def save_menu_item_changes(self, item, name, price, description, weight,
                               radius):
        item.name = name
        item.price = price
        item.description = description
        item.weight = weight
        item.radius = radius
        admin_manager.insert_menu_item(item)
        self.dismiss_dialog()
        self.back_to_menu()

    def dismiss_dialog(self, *_):
        if self.dialog is not None:
            self.dialog.dismiss()

    def add_menu_item(self, _):
        # Create a popup window for adding a new menu item
        popup_content = BoxLayout(orientation='vertical', padding=dp(24),
                                  spacing=dp(4))

        # Add a label indicating to upload a photo
        upload_label = MDLabel(text="Upload Your Photo", size_hint_y=None,
                               height=dp(40))
        popup_content.add_widget(upload_label)

        # Add a file chooser for uploading a photo
        file_chooser = FileChooserIconView(height=300)
        file_chooser.path = '.'  # Set initial path

        def set_img(path):
            self.selected_img = path[0]

        file_chooser.bind(
            on_submit=lambda chooser, path, _: set_img(path))
        popup_content.add_widget(file_chooser)

        # Add text input fields for editing menu item properties
        name_input = MDTextField(hint_text="Name", size=(50, 50))
        price_input = MDTextField(hint_text="Price", size=(50, 50))
        weight_input = MDTextField(hint_text="Weight", size=(50, 50))
        radius_input = MDTextField(hint_text="Radius", size=(50, 50))
        description_input = MDTextField(hint_text="Description", size=(50, 50))

        popup_content.add_widget(name_input)
        popup_content.add_widget(price_input)
        popup_content.add_widget(weight_input)
        popup_content.add_widget(radius_input)
        popup_content.add_widget(description_input)

        # Add a button to save changes
        save_button = MDRaisedButton(text="Save Changes",
                                     size_hint=(None, None), size=(150, 50))
        save_button.bind(
            on_release=lambda button: self.save_add_menu_item_changes(
                name_input.text,
                float(price_input.text),
                description_input.text,
                float(weight_input.text),
                float(radius_input.text)))  # Pass the selected photo preview
        popup_content.add_widget(save_button)

        # Create and open the popup
        popup = Popup(title="Add new menu item", content=popup_content,
                      size_hint=(None, None), size=(800, 1300),
                      # separator_color=[0, 0, 0, 1],
                      # background_color=[255, 255, 255, 255],
                      )
        popup.open()
        self.dialog = popup

    def save_add_menu_item_changes(self, name, price, description, weight,
                                   radius):
        # Handle saving the new menu item, including the photo
        item = MenuItem()
        item.name = name
        item.price = price
        item.description = description
        item.weight = weight
        item.radius = radius
        item.photo_path = self.selected_img  # Save the selected photo path
        admin_manager.insert_menu_item(item)
        self.dismiss_dialog()
        self.back_to_menu()

    def back_to_login(self, *_):
        self.screen_manager.clear_widgets()
        self.login_page_entrance()

    def back_to_menu(self, *_):
        self.screen_manager.clear_widgets()
        self.show_admin_menu_screen()

    def back_to_orders(self, *_):
        self.screen_manager.clear_widgets()
        self.show_admin_order_screen()


class LoginPage:
    def __init__(self, screen_manager, admin_username,
                 admin_password, admin_page_entrance, guest_page_entrance):
        self.screen_manager = screen_manager
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.admin_page_entrance = admin_page_entrance
        self.guest_page_entrance = guest_page_entrance
        self.dialog = None

    def get_logged_in_user(self) -> dict[str, str] | None:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as file:
                data = file.read().split(',')
                if len(data) == 3:
                    return {'firstname': data[0], 'lastname': data[1], 'phone': data[2]}
        return None

    def show_login_screen(self):

        if self.get_logged_in_user() is not None:
            self.login_as_guest(self)

        layout = MDBoxLayout(orientation='vertical', padding=dp(48),
                             spacing=dp(24))
        first_name_field = MDTextField(hint_text="First Name", required=True)
        last_name_field = MDTextField(hint_text="Last Name", required=True)
        phone_number_field = MDTextField(hint_text="Phone Number", required=True)

        register_button = MDRaisedButton(text="Register",
                                         on_release=lambda x: self.register_user(
                                             first_name_field.text,
                                             last_name_field.text,
                                             phone_number_field.text))
        login_as_admin_button = MDRaisedButton(text="Admin Login",
                                               on_release=self.show_admin_login_screen)
        layout.add_widget(first_name_field)
        layout.add_widget(last_name_field)
        layout.add_widget(phone_number_field)
        layout.add_widget(register_button)
        layout.add_widget(login_as_admin_button)
        login_screen = Screen(name='login')
        login_screen.add_widget(layout)
        self.screen_manager.add_widget(login_screen)

    def register_user(self, first_name, last_name, phone_num):
        user = User(first_name=first_name, last_name=last_name, phone_number=int(phone_num))
        user_manager.add_user(user)

        new_user = user_manager.get_user(phone_num)

        with open(SESSION_FILE, 'w') as file:
            file.write(f"{new_user.id},{first_name},{last_name},{phone_num}")

        self.login_as_guest(self)

    def show_admin_login_screen(self, instance):
        self.screen_manager.clear_widgets()

        layout = MDBoxLayout(orientation='vertical', padding=dp(48),
                             spacing=dp(24))
        username_field = MDTextField(hint_text="Username", required=True)
        password_field = MDTextField(hint_text="Password", required=True, password=True)

        login_button = MDRaisedButton(text="Login",
                                      on_release=lambda x: self.login_admin(
                                          username_field.text,
                                          password_field.text))

        layout.add_widget(username_field)
        layout.add_widget(password_field)
        layout.add_widget(login_button)
        login_screen = Screen(name='admin_login')
        login_screen.add_widget(layout)
        self.screen_manager.add_widget(login_screen)

    def login_admin(self, username, password):
        if username == self.admin_username and password == self.admin_password:
            self.screen_manager.clear_widgets()
            self.admin_page_entrance()
        else:
            dialog = MDDialog(title="Invalid Credentials",
                              text="Please enter valid username and password.",
                              size_hint=(0.7, 0.3),
                              auto_dismiss=True,
                              buttons=[MDFlatButton(text="OK",
                                                    on_release=self.dismiss_dialog)])
            dialog.open()
            self.dialog = dialog

    def login_as_guest(self, instance):
        self.screen_manager.clear_widgets()
        self.guest_page_entrance()

    def dismiss_dialog(self, instance):
        if self.dialog is not None:
            self.dialog.dismiss()


class GuestPage:
    def __init__(self, screen_manager, show_admin_login_screen):
        self.screen_manager = screen_manager
        self.show_admin_login_screen = show_admin_login_screen
        self.dialog = None
        self.selected_items = []
        self.total_price = 0

    def add_order(self, menu_items: list[int]):
        items = [user_manager.get_menu_item_by_id(m_id) for m_id in menu_items]
        order = Order(total_price=self.total_price, menu_items=items,
                      status=OrderStatus.CREATED)
        with Session(engine) as session:
            session.add(order)
            session.commit()

    def show_guest_screen(self):
        guest_screen = Screen(name='guest')
        layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        scroll_view = ScrollView()
        menu_list = MDBoxLayout(orientation='vertical', adaptive_height=True,
                                spacing=dp(10))

        # Keep track of selected items and total price
        self.selected_items = []
        self.total_price = 0

        for item in user_manager.get_menu_items():
            checkbox = CheckBox(size_hint=(None, None), size=(dp(48), dp(48)))
            checkbox.item_name = item.name
            checkbox.id = item.id
            checkbox.item_price = item.price
            checkbox.bind(active=self.on_checkbox_active)
            menu_list.add_widget(checkbox)
            menu_list.add_widget(
                OneLineListItem(text=f"{item.name} - ${item.price}"))

        scroll_view.add_widget(menu_list)
        layout.add_widget(scroll_view)
        order_button = MDRaisedButton(text="Place Order",
                                      pos_hint={'center_x': 0.5},
                                      on_release=self.place_order)
        back_button = MDRaisedButton(text="Admin Login",
                                     pos_hint={'center_x': 0.5},
                                     on_release=self.back_to_login)
        layout.add_widget(order_button)
        layout.add_widget(back_button)
        guest_screen.add_widget(layout)
        self.screen_manager.add_widget(guest_screen)

    def on_checkbox_active(self, checkbox, value):
        if value:
            self.selected_items.append(checkbox.id)
            self.total_price += checkbox.item_price
        else:
            self.selected_items.remove(checkbox.id)
            self.total_price -= checkbox.item_price

    def place_order(self, instance):
        if not self.selected_items:
            dialog = MDDialog(title="Error",
                              text="Please select at least one item to place an order.",
                              size_hint=(0.7, 0.3),
                              auto_dismiss=True,
                              buttons=[MDFlatButton(text="OK",
                                                    on_release=self.dismiss_dialog)])
            dialog.open()
            self.dialog = dialog
            return

        # Store the order and display confirmation dialog
        self.add_order(self.selected_items)
        dialog = MDDialog(title="Order Confirmation",
                          text="Your order has been placed!",
                          size_hint=(0.7, 0.3),
                          auto_dismiss=False,
                          buttons=[MDFlatButton(text="OK",
                                                on_release=self.dismiss_dialog)])
        dialog.open()
        self.dialog = dialog

    def back_to_login(self, instance):
        self.screen_manager.clear_widgets()
        self.show_admin_login_screen()

    def dismiss_dialog(self, instance):
        if self.dialog is not None:
            self.dialog.dismiss()


class PizzeriaApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_username = "admin"
        self.admin_password = "123"
        self.title = "Pizzeria App"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.screen_manager = ScreenManager()
        self.guest_page = GuestPage(screen_manager=self.screen_manager,
                                    show_admin_login_screen=self.login_page_entrance)
        self.admin_page = AdminPage(screen_manager=self.screen_manager,
                                    login_page_entrance=self.login_page_entrance)
        self.login_page = LoginPage(screen_manager=self.screen_manager,
                                    admin_password=self.admin_password,
                                    admin_username=self.admin_username,
                                    admin_page_entrance=self.admin_page.show_admin_order_screen,
                                    guest_page_entrance=self.guest_page.show_guest_screen)
        self.login_page.show_login_screen()

    def build(self):
        return self.screen_manager

    def login_page_entrance(self):
        self.login_page.show_login_screen()


if __name__ == '__main__':
    gen_metadata()
    PizzeriaApp().run()
