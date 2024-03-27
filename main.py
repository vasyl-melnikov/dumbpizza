from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import OneLineListItem, MDList
from sqlmodel import SQLModel, create_engine, Session, Field, Relationship
import base64


class OrderMenuItems(SQLModel, table=True):
    order_id: int | None = Field(default=None, foreign_key="order.id",
                                 primary_key=True)
    menu_item_id: int | None = Field(default=None, foreign_key="menuitem.id",
                                     primary_key=True)


class MenuItem(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    price: float
    description: str
    image: str
    orders: list["Order"] = Relationship(back_populates="menu_items",
                                         link_model=OrderMenuItems)


class Order(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    total_price: float
    menu_items: list[MenuItem] = Relationship(back_populates="orders",
                                              link_model=OrderMenuItems)


# SQLite database URL
DATABASE_URL = "sqlite:///./pizzeria.db"

# Set up SQLite database
engine = create_engine(DATABASE_URL, echo=True)


def gen_metadata():
    SQLModel.metadata.create_all(engine)
    MENU_ITEMS = [
        {"name": "Margherita Pizza", "price": 8.99,
         "description": "Classic pizza topped with tomato sauce, mozzarella cheese, and fresh basil leaves.",
         "image": "pizza_img.jpg"},
        {"name": "Pepperoni Pizza", "price": 9.99,
         "description": "Delicious pizza topped with spicy pepperoni slices and mozzarella cheese on a tomato sauce base.",
         "image": "pizza_img.jpg"},
        {"name": "Vegetarian Pizza", "price": 10.99,
         "description": "Healthy pizza loaded with assorted vegetables such as bell peppers, onions, mushrooms, and olives.",
         "image": "pizza_img.jpg"},
        {"name": "Supreme Pizza", "price": 11.99,
         "description": "A flavorful pizza topped with a variety of ingredients including pepperoni, sausage, bell peppers, onions, and mushrooms.",
         "image": "pizza_img.jpg"}
    ]
    with Session(engine) as session:
        for item in MENU_ITEMS:
            with open(item['image'], 'rb') as f:
                img_data = f.read()
            menu = MenuItem(name=item['name'],
                            description=item['description'],
                            price=item['price'],
                            image=base64.b64encode(img_data).decode('utf-8'))
            session.add(menu)
        session.commit()


class AdminPage:
    def __init__(self, screen_manager, login_page_entrance):
        self.dialog = None
        self.screen_manager = screen_manager
        self.login_page_entrance = login_page_entrance

    def get_menu_items(self) -> list[MenuItem]:
        with Session(engine) as session:
            return session.query(MenuItem).all()

    def show_admin_order_screen(self):
        orders_screen = Screen(name='orders')

        # Create a layout for orders
        orders_layout = BoxLayout(orientation='vertical', padding=dp(24),
                                  spacing=dp(16))

        # Create a scrollable view for orders list
        orders_scroll_view = ScrollView()
        orders_list = MDList(padding=dp(24), spacing=dp(16))
        with Session(engine) as session:
            for order in session.query(Order).all():
                card = MDCard(size_hint=(None, None), size=(400, 200),
                              padding=dp(16), spacing=dp(8))
                card.add_widget(MDLabel(text=f"Order ID: {order.id}",
                                        font_style='Subtitle1'))
                menu_items_text = ""
                for menu_item in order.menu_items:
                    menu_items_text += f"{menu_item.name} - ${menu_item.price}\n"
                card.add_widget(
                    MDLabel(text=menu_items_text, font_style='Body1',
                            size_hint_y=None, height=dp(100)))

                # Add buttons for controlling order status
                status_button = MDIconButton(
                    icon="checkbox-blank-circle-outline",
                    pos_hint={'center_x': 0.5})
                status_button.bind(on_release=self.show_status_menu)
                card.add_widget(status_button)
                orders_list.add_widget(card)

        orders_scroll_view.add_widget(orders_list)

        # Add the scrollable view to the layout
        orders_layout.add_widget(orders_scroll_view)

        # Create buttons section as a footer
        buttons_layout = BoxLayout(orientation='horizontal', padding=dp(12),
                                   spacing=dp(12))
        add_item_button = MDRaisedButton(text="Add Item", size_hint_x=None,
                                         width=dp(120),
                                         on_release=self.add_item)
        back_button = MDRaisedButton(text="Back to Login", size_hint_x=None,
                                     width=dp(120),
                                     on_release=self.back_to_login)
        orders_menu = MDRaisedButton(text="Menu", size_hint_x=None,
                                     width=dp(120),
                                     on_release=self.back_to_menu)
        buttons_layout.add_widget(orders_menu)
        buttons_layout.add_widget(add_item_button)
        buttons_layout.add_widget(back_button)

        # Add the buttons layout to the main orders layout
        orders_layout.add_widget(buttons_layout)

        orders_screen.add_widget(orders_layout)

        self.screen_manager.add_widget(orders_screen)

    def show_status_menu(self, button):
        menu = MDDropdownMenu(
            caller=button,
            items=[{"text": "In Progress"}, {"text": "Cancelled"},
                   {"text": "Done"}],
            position="bottom",
            width_mult=4
        )
        menu.open()

    def on_status_change(self, text):
        print(1)

    def show_admin_menu_screen(self):
        menu_screen = Screen(name='menu')
        menu_list = MDList(padding=dp(24), spacing=dp(16))
        for item in self.get_menu_items():
            card = MDCard(size_hint_y=None, height=dp(200), padding=dp(16),
                          spacing=dp(8))
            card.md_bg_color = "#808080"
            card.add_widget(MDLabel(text=item.name, halign='center', font_style='H6'))
            card.add_widget(MDLabel(text=f"${item.price}", halign='center'))
            card.add_widget(MDLabel(text=item.description, halign='left'))
            with open('tmp.img', 'wb') as f:
                f.write(base64.b64decode(item.image))
            card.add_widget(AsyncImage(source='tmp.img'))
            menu_list.add_widget(card)
        menu_scroll_view = ScrollView()
        menu_scroll_view.add_widget(menu_list)

        buttons_layout = MDBoxLayout(orientation='horizontal', padding=dp(12),
                                     spacing=dp(12))
        add_item_button = MDRaisedButton(text="Add Item", size_hint_x=None,
                                         width=dp(120),
                                         on_release=self.add_item)
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

    def dismiss_dialog(self, instance):
        if self.dialog is not None:
            self.dialog.dismiss()

    def add_item(self, instance):
        dialog = MDDialog(title="Add Menu Item",
                          size_hint=(0.7, 0.3),
                          auto_dismiss=False,
                          buttons=[MDRaisedButton(text="Add",
                                                  on_release=self.dismiss_dialog),
                                   MDFlatButton(text="Cancel",
                                                on_release=self.dismiss_dialog)])
        dialog.open()
        self.dialog = dialog

    def back_to_login(self, instance):
        self.screen_manager.clear_widgets()
        self.login_page_entrance()

    def back_to_menu(self, instance):
        self.screen_manager.clear_widgets()
        self.show_admin_menu_screen()

    def back_to_orders(self, instance):
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

    def show_login_screen(self):
        layout = MDBoxLayout(orientation='vertical', padding=dp(48),
                             spacing=dp(24))
        username_field = MDTextField(hint_text="Username", required=True)
        password_field = MDTextField(hint_text="Password", required=True,
                                     password=True)
        login_button = MDRaisedButton(text="Login",
                                      on_release=lambda x: self.login(
                                          username_field.text,
                                          password_field.text))
        guest_button = MDRaisedButton(text="Login as Guest",
                                      on_release=self.login_as_guest)
        layout.add_widget(username_field)
        layout.add_widget(password_field)
        layout.add_widget(login_button)
        layout.add_widget(guest_button)
        login_screen = Screen(name='login')
        login_screen.add_widget(layout)
        self.screen_manager.add_widget(login_screen)

    def login(self, username, password):
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
    def __init__(self, screen_manager, login_page_entrance):
        self.screen_manager = screen_manager
        self.login_page_entrance = login_page_entrance
        self.dialog = None
        self.selected_items = []
        self.total_price = 0

    def get_menu_items(self) -> list[MenuItem]:
        with Session(engine) as session:
            return session.query(MenuItem).all()

    def get_menu_item(self, id) -> MenuItem:
        with Session(engine) as session:
            return session.query(MenuItem).where(MenuItem.id == id).one()

    def get_orders(self) -> list[Order]:
        with Session(engine) as session:
            return session.query(Order).all()

    def add_order(self, menu_items: list[int]):
        items = [self.get_menu_item(m_id) for m_id in menu_items]
        order = Order(total_price=self.total_price, menu_items=items)
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

        for item in self.get_menu_items():
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
        back_button = MDRaisedButton(text="Back to Login",
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
        self.login_page_entrance()

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
                                    login_page_entrance=self.login_page_entrance)
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
    # gen_metadata()
    PizzeriaApp().run()
