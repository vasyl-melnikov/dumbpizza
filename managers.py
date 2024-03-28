import hashlib

from sqlmodel import create_engine, Session, select

from models import MenuItem, User, Order, OrderStatus, Admin

DATABASE_URL = "sqlite:///./pizzeria.db"


class AdminManager:                                                 #total orders, total price of all orders

    def __init__(self):
        self.__db = create_engine(DATABASE_URL, echo=True)

    def get_all_users(self) -> list[User]:
        with Session(self.__db) as session:
            return session.query(User).all()

    def get_user_by_id(self, user_id: int) -> User:
        with Session(self.__db) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).one()

    def get_all_orders(self) -> list[Order]:
        with Session(self.__db) as session:
            return session.query(Order).all()

    def get_order_by_id(self, order_id: int) -> Order:
        with Session(self.__db) as session:
            statement = select(Order).where(Order.id == order_id)
            return session.exec(statement).one()

    def insert_menu_item(self, menu_item: MenuItem) -> None:
        with Session(self.__db) as session:
            session.add(menu_item)
            session.commit()
            session.refresh(menu_item)

    def insert_order(self, order: Order) -> None:
        with Session(self.__db) as session:
            session.add(order)
            session.commit()
            session.refresh(order)

    def update_order_status(self, order_id: int, new_status: OrderStatus) -> None:
        with Session(self.__db) as session:
            statement = select(Order).where(Order.id == order_id)
            order = session.exec(statement).one()
            if order:
                order.status = new_status
                session.add(order)
                session.commit()
            else:
                print("ORDERA NEMA TAKOGO")

    def insert_admin(self, admin: Admin):
        with Session(self.__db) as session:
            session.add(admin)
            session.commit()
            session.refresh(admin)

    def is_valid_credentials(self, name: str, password: str) -> bool:
        with Session(self.__db) as session:
            statement = select(Admin).where(Admin.name == name)
            admin = session.exec(statement).one()
            if not admin:
                print("ADMINA NEMA TAKOGO")
                return False
            if admin.password != hashlib.sha256(password.encode()).hexdigest():
                return False
            return True


class UserManager:
    def __init__(self):
        self.__db = create_engine(DATABASE_URL, echo=True)

    def get_menu_items(self) -> list[MenuItem]:
        with Session(self.__db) as session:
            return session.query(MenuItem).all()

    def get_menu_item_by_id(self, menu_item_id: int) -> MenuItem:
        with Session(self.__db) as session:
            statement = select(MenuItem).where(MenuItem.id == menu_item_id)
            return session.exec(statement).one()

    def get_order_by_id(self, order_id: int) -> Order:
        with Session(self.__db) as session:
            statement = select(Order).where(Order.id == order_id)
            return session.exec(statement).one()

    def get_orders_by_user_id(self, user_id: int) -> list[Order]:
        with Session(self.__db) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).one().orders






