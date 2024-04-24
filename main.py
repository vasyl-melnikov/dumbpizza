import os.path

from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage, Image
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, \
    MDRectangleFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import OneLineListItem, MDList
from sqlmodel import SQLModel, create_engine, Session
import base64
from models import OrderStatus, User, MenuItem, Order
from managers import AdminManager, UserManager

# SQLite database URL
DATABASE_URL = "sqlite:///./pizzeria.db"

# User session info
SESSION_FILE = 'session_data.txt'

# Set up SQLite database
engine = create_engine(DATABASE_URL, echo=True)
user_manager = UserManager(engine)
admin_manager = AdminManager(engine)

status_colors = {
    OrderStatus.CREATED: "[color=008080]",  # Green color
    OrderStatus.COOKING: "[color=FFD700]",  # Gold color
    OrderStatus.READY: "[color=FFA500]",  # Orange color
    OrderStatus.DONE: "[color=32CD32]",  # Lime Green color
    OrderStatus.CANCELLED: "[color=FF0000]"  # Red color
}


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
        orders_scroll_view = MDScrollView()

        # Create a grid layout for orders list
        orders_grid = MDGridLayout(cols=1, padding=dp(12), spacing=dp(12),
                                   size_hint_y=None)
        orders_grid.bind(minimum_height=orders_grid.setter('height'))

        for order in admin_manager.get_all_orders():
            # Create a card for each order
            card = MDCard(size_hint=(None, None), size=(dp(700), dp(250)),
                          padding=dp(16), spacing=dp(8))

            card.add_widget(
                MDLabel(text=f"[color=008080]Order ID:[/color] {order.id}",
                        font_size=sp(16), markup=True))
            card.add_widget(MDLabel(
                text=f"[color=008080]Created at:[/color] {order.created_at.strftime('%m/%d/%Y, %H:%M:%S')}",
                font_size=sp(16), markup=True))
            card.add_widget(
                MDLabel(text=f"[color=008080]Status:[/color] {order.status}",
                        font_size=sp(16), markup=True))
            card.add_widget(MDLabel(
                text=f"[color=008080]Guest name:[/color] {order.user.first_name}",
                font_size=sp(16), markup=True))
            card.add_widget(MDLabel(
                text=f"[color=008080]Guest last name:[/color] {order.user.last_name}",
                font_size=sp(16), markup=True))
            card.add_widget(MDLabel(
                text=f"[color=008080]Guest phone number:[/color] {order.user.phone_number}",
                font_size=sp(16), markup=True))
            menu_items_text = "["
            for menu_item in order.menu_items:
                menu_items_text += f"{menu_item.name},\n"
            menu_items_text += "]"
            card.add_widget(MDLabel(
                text=f"[color=008080]Menu Items:[/color]\n{menu_items_text}",
                font_size=sp(16), markup=True))

            card.add_widget(MDLabel(
                text=f"[color=008080]Total price of order:[/color] {order.total_price}",
                font_size=sp(16), markup=True))

            # Add button for controlling order status
            status_button = MDRectangleFlatButton(text='Change status',
                                                  size_hint=(None, None),
                                                  size=(dp(150), dp(50)))
            status_button.order_id = order.id
            status_button.bind(on_release=self.show_status_menu)
            card.add_widget(status_button)

            # Add card to the grid layout
            orders_grid.add_widget(card)

        # Add grid layout to the scrollable view
        orders_scroll_view.add_widget(orders_grid)

        # Create footer buttons
        add_item_button = MDRectangleFlatButton(text="Add Item",
                                                size_hint=(None, None),
                                                size=(dp(150), dp(50)),
                                                on_release=self.add_menu_item)
        back_button = MDRectangleFlatButton(text="Back to Login",
                                            size_hint=(None, None),
                                            size=(dp(150), dp(50)),
                                            on_release=self.back_to_login)
        orders_menu = MDRectangleFlatButton(text="Menu",
                                            size_hint=(None, None),
                                            size=(dp(150), dp(50)),
                                            on_release=self.back_to_menu)

        stats_menu = MDRectangleFlatButton(text="Stats",
                                           size_hint=(None, None),
                                           size=(dp(150), dp(50)),
                                           on_release=self.back_to_stats)

        # Create grid layout for footer buttons
        buttons_layout = MDBoxLayout(orientation='horizontal', padding=dp(12),
                                     spacing=dp(12))
        buttons_layout.add_widget(orders_menu)
        buttons_layout.add_widget(stats_menu)
        buttons_layout.add_widget(add_item_button)
        buttons_layout.add_widget(back_button)

        # Add scrollable view and footer buttons to the screen
        orders_screen.add_widget(orders_scroll_view)
        orders_screen.add_widget(buttons_layout)

        # Add the screen to the screen manager
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
            card.add_widget(
                MDLabel(text=f"Price: ${item.price}", halign='center'))
            card.add_widget(
                MDLabel(text=f"Weight: {item.weight}", halign='center'))
            card.add_widget(
                MDLabel(text=f"Radius: {item.radius}", halign='center'))
            card.add_widget(MDLabel(text=item.description, halign='left'))
            if not os.path.exists('assets'):
                os.mkdir('assets')
            with open(os.path.join(f'assets', f'menu_item{item.id}.jpg'),
                      'wb') as f:
                f.write(base64.b64decode(item.image))
            card.add_widget(AsyncImage(
                source=os.path.join(f'assets', f'menu_item{item.id}.jpg'),
                nocache=True))

            # Add an "Edit" button to each menu item card
            edit_button = MDRaisedButton(text="Edit", size_hint=(None, None),
                                         size=(100, 50))
            edit_button.bind(
                on_release=lambda button, item=item: self.show_edit_popup(item))

            delete_button = MDRaisedButton(text="Delete", size_hint=(None, None),
                                         size=(100, 50))
            delete_button.bind(
                on_release=lambda button, item=item: self.show_delete_popup(item))
            card.add_widget(edit_button)
            card.add_widget(delete_button)
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
        orders_button = MDRaisedButton(text="Back", size_hint_x=None,
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

    def show_delete_popup(self, item):
        popup_content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16))

        delete_button = MDRaisedButton(text="DELETE", size_hint=(None, None), size=(150, 50))
        delete_button.bind(on_release=lambda button: admin_manager.delete_menu_item(item))
        popup_content.add_widget(delete_button)

        popup = Popup(title="Are you sure you want to delete this item?", content=popup_content,
                      size_hint=(None, None), size=(400, 400),
                      separator_color=[0, 0, 0, 1],
                      title_color=[0, 0, 0, 1],
                      title_align='center',
                      background_color=[255, 255, 255, 255])

        popup.open()
        self.dialog = popup

    def show_edit_popup(self, item):
        # Create a popup window for editing menu item properties
        self.cur_menu_item_edit = item
        popup_content = BoxLayout(orientation='vertical', padding=dp(24),
                                  spacing=dp(16))

        # Add text input fields for editing menu item properties
        name_input = MDTextField(text=item.name, hint_text="Name",
                                 foreground_color=(0, 0, 0, .4))
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
                      size_hint=(None, None), size=(400, 400),
                      separator_color=[0, 0, 0, 1],
                      title_color=[0, 0, 0, 1],
                      title_align='center',
                      background_color=[255, 255, 255, 255])
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
                      size_hint=(None, None), size=(400, 400),
                      separator_color=[0, 0, 0, 1],
                      title_color=[0, 0, 0, 1],
                      title_align='center',
                      background_color=[255, 255, 255, 255])
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

    def show_admin_stats_screen(self, *_):

        stats_screen = Screen(name='stats')

        card = MDCard(size_hint_y=None, height=dp(300), padding=dp(16),
                      spacing=dp(8), pos_hint={"top": 1})
        card.md_bg_color = "#808080"

        card.add_widget(
            MDLabel(text=f"Total number of orders: ${admin_manager.get_total_number_of_orders()}", halign='center',
                    font_style='H6'))
        card.add_widget(
            MDLabel(text=f"Total revenue: ${admin_manager.get_total_revenue()}", halign='center'))
        card.add_widget(
            MDLabel(text=f"Average order price: ${admin_manager.get_avg_order_price()}", halign='center'))
        card.add_widget(
            MDLabel(text=f"Average order size: ${admin_manager.get_avg_order_size()}", halign='center'))

        back_button = MDRectangleFlatButton(text="Back",
                                            size_hint=(None, None),
                                            size=(dp(150), dp(50)),
                                            on_release=self.back_to_orders)

        # Create grid layout for footer buttons
        buttons_layout = MDBoxLayout(orientation='horizontal', padding=dp(12),
                                     spacing=dp(12))

        buttons_layout.add_widget(back_button)

        stats_screen.add_widget(card)
        stats_screen.add_widget(buttons_layout)

        self.screen_manager.add_widget(stats_screen)

    def back_to_login(self, *_):
        self.screen_manager.clear_widgets()
        self.login_page_entrance()

    def back_to_menu(self, *_):
        self.screen_manager.clear_widgets()
        self.show_admin_menu_screen()

    def back_to_orders(self, *_):
        self.screen_manager.clear_widgets()
        self.show_admin_order_screen()

    def back_to_stats(self, *_):
        self.screen_manager.clear_widgets()
        self.show_admin_stats_screen()


def get_logged_in_user() -> dict[str, str] | None:
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as file:
            data = file.read().split(',')
            if len(data) == 4:
                return {'id': data[0], 'first_name': data[1],
                        'last_name': data[2], 'phone_number': data[3]}
    return None


class LoginPage:
    def __init__(self, screen_manager, admin_username,
                 admin_password, admin_page_entrance, guest_page_entrance):
        self.screen_manager = screen_manager
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.admin_page_entrance = admin_page_entrance
        self.guest_page_entrance = guest_page_entrance
        self.dialog = None

    def show_login_screen(self, *_):
        self.screen_manager.clear_widgets()
        if get_logged_in_user() is not None:
            self.login_as_guest(self)

        layout = MDBoxLayout(orientation='vertical', padding=dp(48),
                             spacing=dp(24))
        first_name_field = MDTextField(hint_text="First Name", required=True)
        last_name_field = MDTextField(hint_text="Last Name", required=True)
        phone_number_field = MDTextField(hint_text="Phone Number",
                                         required=True)

        register_button = MDRaisedButton(text="Register",
                                         on_release=lambda
                                             x: self.register_user(
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
        if not first_name or not last_name or not phone_num:
            dialog = MDDialog(title="Invalid Credentials",
                              text="Please enter valid credentials.",
                              size_hint=(0.7, 0.3),
                              auto_dismiss=True,
                              buttons=[MDFlatButton(text="OK",
                                                    on_release=self.dismiss_dialog)])
            dialog.open()
            self.dialog = dialog
        else:
            user = User(first_name=first_name, last_name=last_name,
                        phone_number=str(phone_num))
            user_manager.add_user(user)

            new_user = user_manager.get_user(phone_num)

            with open(SESSION_FILE, 'w') as file:
                file.write(
                    f"{new_user.id},{first_name},{last_name},{phone_num}")

            self.login_as_guest(self)

    def show_admin_login_screen(self, *_):
        self.screen_manager.clear_widgets()

        layout = MDBoxLayout(orientation='vertical', padding=dp(48),
                             spacing=dp(24))
        username_field = MDTextField(hint_text="Username", required=True)
        password_field = MDTextField(hint_text="Password", required=True,
                                     password=True)

        login_button = MDRaisedButton(text="Login",
                                      on_release=lambda x: self.login_admin(
                                          username_field.text,
                                          password_field.text))
        guest_button = MDRaisedButton(text="Back to guest screen",
                                      on_release=self.show_login_screen)

        layout.add_widget(username_field)
        layout.add_widget(password_field)
        layout.add_widget(login_button)
        layout.add_widget(guest_button)
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
    def __init__(self, screen_manager, show_admin_login_screen,
                 admin_login_page_entrance, show_login_screen):
        self.screen_manager = screen_manager
        self.show_login_screen = show_login_screen
        self.show_admin_login_screen = show_admin_login_screen
        self.admin_login_page_entrance = admin_login_page_entrance
        self.dialog = None
        self.selected_items = []
        self.total_price = 0

    def add_order(self, menu_items: list[int]):
        items = [user_manager.get_menu_item_by_id(m_id) for m_id in menu_items]
        order = Order(total_price=self.total_price, menu_items=items,
                      status=OrderStatus.CREATED,
                      user_id=get_logged_in_user()['id'])
        with Session(engine) as session:
            session.add(order)
            session.commit()

    def show_guest_screen(self, *_):
        self.screen_manager.clear_widgets()
        menu_list = MDList(padding=dp(24), spacing=dp(16))
        cards = []
        self.selected_items = []
        self.total_price = 0

        for item in user_manager.get_menu_items():
            card = MDCard(size_hint_y=None, height=dp(200), padding=dp(16),
                          spacing=dp(8))
            card.md_bg_color = "#808080"
            checkbox = CheckBox(size_hint=(None, None), size=(dp(48), dp(48)))
            checkbox.item = item
            checkbox.bind(active=self.on_checkbox_active)
            card.add_widget(checkbox)
            card.add_widget(
                MDLabel(text=item.name, halign='center', font_style='H6'))
            card.add_widget(
                MDLabel(text=f"Price: ${item.price}", halign='center'))
            card.add_widget(
                MDLabel(text=f"Weight: {item.weight}", halign='center'))
            card.add_widget(
                MDLabel(text=f"Radius: {item.radius}", halign='center'))
            card.add_widget(MDLabel(text=item.description, halign='left'))
            if not os.path.exists('assets'):
                os.mkdir('assets')
            with open(os.path.join(f'assets', f'menu_item{item.id}.jpg'),
                      'wb') as f:
                f.write(base64.b64decode(item.image))
            card.add_widget(AsyncImage(
                source=os.path.join(f'assets', f'menu_item{item.id}.jpg'),
                nocache=True))
            cards.append(card)

        for card in cards:
            menu_list.add_widget(card)

        menu_scroll_view = ScrollView()
        menu_scroll_view.add_widget(menu_list)

        buttons_layout = MDBoxLayout(orientation='horizontal', padding=dp(12),
                                     spacing=dp(12))
        order_button = MDRaisedButton(text="Place Order",
                                      pos_hint={'center_x': 0.5},
                                      on_release=self.place_order)
        back_button = MDRaisedButton(text="Admin Login",
                                     pos_hint={'center_x': 0.5},
                                     on_release=self.admin_login_page_entrance)

        edit_profile_button = MDRaisedButton(text="Edit Profile",
                                             pos_hint={'center_x': 0.5},
                                             on_release=self.edit_credentials_page)

        logout_button = MDRaisedButton(text="Logout",
                                       pos_hint={'center_x': 0.5},
                                       on_release=self.logout)
        o_history_button = MDRaisedButton(text="Orders history",
                                          pos_hint={'center_x': 0.5},
                                          on_release=self.show_order_history_screen)
        stats_button = MDRaisedButton(text="Stats",
                                      pos_hint={'center_x': 0.5},
                                      on_release=self.show_user_stats_screen)
        buttons_layout.add_widget(order_button)
        buttons_layout.add_widget(back_button)
        buttons_layout.add_widget(edit_profile_button)
        buttons_layout.add_widget(logout_button)
        buttons_layout.add_widget(o_history_button)
        buttons_layout.add_widget(stats_button)

        guest_screen = Screen(name='guest')
        guest_layout = MDBoxLayout(orientation='vertical')
        guest_layout.add_widget(menu_scroll_view)
        guest_screen.add_widget(guest_layout)
        guest_screen.add_widget(buttons_layout)

        self.screen_manager.add_widget(guest_screen)

    def show_user_stats_screen(self, *_):
        self.screen_manager.clear_widgets()

        stats_screen = Screen(name='stats')

        card = MDCard(size_hint_y=None, height=dp(300), padding=dp(16),
                      spacing=dp(8), pos_hint={"top": 1})
        card.md_bg_color = "#808080"

        user_id = int(get_logged_in_user()['id'])

        card.add_widget(
            MDLabel(text=f"Total number of orders: {user_manager.get_total_number_of_orders_by_user_id(user_id)}", halign='center',
                    font_style='H6'))
        card.add_widget(
            MDLabel(text=f"Total money spent: ${user_manager.get_total_amount_spent_by_user_id(user_id)}", halign='center'))
        card.add_widget(
            MDLabel(text=f"Average money spent: ${user_manager.get_avg_amount_spent_by_user_id(user_id)}", halign='center'))
        card.add_widget(
            MDLabel(text=f"Most ordered item: {user_manager.get_most_ordered_item_by_user_id(user_id)}", halign='center'))

        back_button = MDRectangleFlatButton(text="Back",
                                            size_hint=(None, None),
                                            size=(dp(150), dp(50)),
                                            on_release=self.show_guest_screen)

        # Create grid layout for footer buttons
        buttons_layout = MDBoxLayout(orientation='horizontal', padding=dp(12),
                                     spacing=dp(12))

        buttons_layout.add_widget(back_button)

        stats_screen.add_widget(card)
        stats_screen.add_widget(buttons_layout)

        self.screen_manager.add_widget(stats_screen)


    def show_order_history_screen(self, *_):
        self.screen_manager.clear_widgets()
        orders_screen = Screen(name='orders')

        # Create a scrollable view for orders list
        orders_scroll_view = MDScrollView()

        # Create a grid layout for orders list
        orders_grid = MDGridLayout(cols=1, padding=dp(12), spacing=dp(12),
                                   size_hint_y=None)
        orders_grid.bind(minimum_height=orders_grid.setter('height'))

        for order in user_manager.get_orders_by_user_id(
                int(get_logged_in_user()['id'])):
            # Create a card for each order
            card = MDCard(size_hint=(None, None), size=(dp(700), dp(250)),
                          padding=dp(16), spacing=dp(8))

            card.add_widget(
                MDLabel(text=f"[color=008080]Order ID:[/color] {order.id}",
                        font_size=sp(16), markup=True))
            card.add_widget(MDLabel(
                text=f"[color=008080]Created at:[/color] {order.created_at.strftime('%m/%d/%Y, %H:%M:%S')}",
                font_size=sp(16), markup=True))
            card.add_widget(
                MDLabel(
                    text=f"[color=008080]Status:[/color] [b]{status_colors[order.status]}{order.status.title()}[/b][/color] ",
                    font_size=sp(16), markup=True))
            menu_items_text = "["
            for menu_item in order.menu_items:
                menu_items_text += f"{menu_item.name},\n"
            menu_items_text += "]"
            card.add_widget(MDLabel(
                text=f"[color=008080]Menu Items:[/color]\n{menu_items_text}",
                font_size=sp(16), markup=True))

            card.add_widget(MDLabel(
                text=f"[color=008080]Total price of order:[/color] {order.total_price}",
                font_size=sp(16), markup=True))

            # Add card to the grid layout
            orders_grid.add_widget(card)

        buttons_layout = MDBoxLayout(orientation='horizontal',
                                     padding=dp(12),
                                     spacing=dp(12))
        back_button = MDRaisedButton(text="Admin Login",
                                     pos_hint={'center_x': 0.5},
                                     on_release=self.admin_login_page_entrance)
        o_button = MDRaisedButton(text="Back",
                                  pos_hint={'center_x': 0.5},
                                  on_release=self.show_guest_screen)

        edit_profile_button = MDRaisedButton(text="Edit Profile",
                                             pos_hint={'center_x': 0.5},
                                             on_release=self.edit_credentials_page)

        logout_button = MDRaisedButton(text="Logout",
                                       pos_hint={'center_x': 0.5},
                                       on_release=self.logout)
        buttons_layout.add_widget(o_button)
        buttons_layout.add_widget(back_button)
        buttons_layout.add_widget(edit_profile_button)
        buttons_layout.add_widget(logout_button)
        # Add grid layout to the scrollable view
        orders_scroll_view.add_widget(orders_grid)

        # Add scrollable view and footer buttons to the screen
        orders_screen.add_widget(orders_scroll_view)
        orders_screen.add_widget(buttons_layout)

        # Add the screen to the screen manager
        self.screen_manager.add_widget(orders_screen)

    def logout(self, *_):
        if os.path.exists(SESSION_FILE):
            user_id: int = int(get_logged_in_user().get("id"))
            user_manager.delete_user(user_id)
            os.remove(SESSION_FILE)
            self.screen_manager.clear_widgets()
            self.show_login_screen()

    def edit_credentials_page(self, *_):
        self.screen_manager.clear_widgets()

        user_credentials: dict[str, str] = get_logged_in_user()
        self.screen_manager.clear_widgets()

        layout = MDBoxLayout(orientation='vertical', padding=dp(48),
                             spacing=dp(24))
        first_name_field = MDTextField(text=user_credentials.get("first_name"),
                                       hint_text="First Name", required=True)
        last_name_field = MDTextField(text=user_credentials.get("last_name"),
                                      hint_text="Last Name", required=True)
        phone_num_field = MDTextField(text=user_credentials.get("phone_number"),
                                      hint_text="Phone Number", required=True)

        save_changes_button = MDRaisedButton(text="Save",
                                             on_release=lambda
                                                 x: self.save_changes(
                                                 first_name_field.text,
                                                 last_name_field.text,
                                                 phone_num_field.text))

        guest_screen_button = MDRaisedButton(text="Main page",
                                             on_release=self.show_guest_screen)

        layout.add_widget(first_name_field)
        layout.add_widget(last_name_field)
        layout.add_widget(phone_num_field)
        layout.add_widget(save_changes_button)
        layout.add_widget(guest_screen_button)
        login_screen = Screen(name='edit_credentials')
        login_screen.add_widget(layout)
        self.screen_manager.add_widget(login_screen)

    def save_changes(self, first_name, last_name, phone_num):
        if not first_name or not last_name or not phone_num:
            dialog = MDDialog(title="Invalid Credentials",
                              text="Please enter valid credentials.",
                              size_hint=(0.7, 0.3),
                              auto_dismiss=True,
                              buttons=[MDFlatButton(text="OK",
                                                    on_release=self.dismiss_dialog)])
            dialog.open()
            self.dialog = dialog
        else:
            old_phone_number = get_logged_in_user().get("phone_number")
            user = User(first_name=first_name, last_name=last_name,
                        phone_number=phone_num)
            new_user = user_manager.update_user(old_phone_number, user)

            if not new_user:
                dialog = MDDialog(title="Invalid User",
                                  text="User with current credentials doesn't exist.",
                                  size_hint=(0.7, 0.3),
                                  auto_dismiss=True,
                                  buttons=[MDFlatButton(text="OK",
                                                        on_release=self.dismiss_dialog)])
                dialog.open()
                self.dialog = dialog
            else:
                with open(SESSION_FILE, 'w') as file:
                    file.write(
                        f"{new_user.id},{first_name},{last_name},{phone_num}")

            self.screen_manager.clear_widgets()
            self.edit_credentials_page()

    def on_checkbox_active(self, checkbox, value):
        if value:
            self.selected_items.append(checkbox.item.id)
            self.total_price += checkbox.item.price
        else:
            self.selected_items.remove(checkbox.item.id)
            self.total_price -= checkbox.item.price

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
        self.admin_username = "123"
        self.admin_password = "123"
        self.title = "Pizzeria App"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.screen_manager = ScreenManager()
        self.guest_page = GuestPage(screen_manager=self.screen_manager,
                                    show_admin_login_screen=self.login_page_entrance,
                                    admin_login_page_entrance=self.admin_login_page_entrance,
                                    show_login_screen=self.login_page_entrance)
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

    def admin_login_page_entrance(self, *_):
        self.login_page.show_admin_login_screen()


if __name__ == '__main__':
    # gen_metadata()
    PizzeriaApp().run()
