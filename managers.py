import hashlib
from typing import Sequence

from sqlalchemy import func, desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from models import MenuItem, User, Order, OrderStatus, Admin, OrderMenuItems


class AdminManager:

    def __init__(self, db):
        self.__db = db

    def get_all_users(self) -> list[User]:
        with Session(self.__db) as session:
            return session.query(User).all()

    def get_user_by_id(self, user_id: int) -> User:
        with Session(self.__db) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).one()

    def get_all_orders(self) -> list[Order]:
        with Session(self.__db) as session:
            return session.exec(
                select(Order).options(selectinload(Order.menu_items),
                                      selectinload(Order.user))).all()

    def get_order_by_id(self, order_id: int) -> Order:
        with Session(self.__db) as session:
            statement = select(Order).where(Order.id == order_id)
            return session.exec(statement).one()

    def insert_menu_item(self, menu_item: MenuItem) -> None:
        with Session(self.__db) as session:
            session.add(menu_item)
            session.commit()
            # session.refresh(menu_item)

    def delete_menu_item(self, menu_item: MenuItem) -> None:
        with Session(self.__db) as session:
            session.delete(menu_item)
            session.commit()
            # session.refresh(menu_item)

    def insert_order(self, order: Order) -> None:
        with Session(self.__db) as session:
            session.add(order)
            session.commit()
            session.refresh(order)

    def update_order_status(self, order_id: int,
                            new_status: OrderStatus) -> None:
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
        admin.password = hashlib.sha256(admin.password.encode()).hexdigest()
        with Session(self.__db) as session:
            session.add(admin)
            session.commit()
            session.refresh(admin)

    def is_valid_credentials(self, name: str, password: str) -> bool:
        with Session(self.__db) as session:
            statement = select(Admin).where(Admin.name == name)
            try:
                admin = session.exec(statement).one()
            except Exception:
                return False
            if not admin:
                return False
            if admin.password != hashlib.sha256(password.encode()).hexdigest():
                return False
            return True

    def get_total_number_of_orders(self) -> int:
        with Session(self.__db) as session:
            statement = select(func.count()).select_from(Order)
            return session.exec(statement).one()

    def get_total_revenue(self) -> float:
        with Session(self.__db) as session:
            statement = select(func.sum(Order.total_price)).select_from(Order)
            return session.exec(statement).one() or 0.0

    def get_avg_order_price(self) -> float:
        with Session(self.__db) as session:
            statement = select(func.avg(Order.total_price)).select_from(Order)
            return session.exec(statement).one() or 0.0

    def get_avg_order_size(self) -> float:
        with Session(self.__db) as session:
            statement = select(func.avg(Order.total_price)).select_from(Order)
            return session.exec(statement).one() or 0.0


class UserManager:
    def __init__(self, db):
        self.__db = db

    def add_user(self, user: User) -> None:
        with Session(self.__db) as session:
            session.add(user)
            session.commit()
            session.refresh(user)

    def delete_user(self, user_id: int) -> None:
        with Session(self.__db) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).one()
            if user:
                session.delete(user)
                session.commit()

    def update_user(self, old_phone_number: str, user: User) -> User | None:
        with Session(self.__db) as session:
            statement = select(User).where(
                User.phone_number == old_phone_number)
            old_user = session.exec(statement).one()
            if old_user:
                old_user.first_name = user.first_name
                old_user.last_name = user.last_name
                old_user.phone_number = user.phone_number
                session.commit()
                session.refresh(old_user)
                return old_user
            else:
                print("USERA NEMA TAKOGO")
                return None

    def get_user(self, number: int) -> User:
        with Session(self.__db) as session:
            return session.exec(select(User)
                                .where(User.phone_number == number)
                                .options(selectinload(User.orders))).one()

    def get_user_by_id(self, id: int) -> User:
        with Session(self.__db) as session:
            return session.exec(select(User)
                                .where(User.id == id)
                                .options(selectinload(User.orders))).one()

    def get_menu_items(self) -> list[MenuItem]:
        with Session(self.__db) as session:
            return session.query(MenuItem).all()

    def get_menu_item_by_id(self, menu_item_id: int) -> MenuItem:
        with Session(self.__db) as session:
            statement = select(MenuItem).where(MenuItem.id == menu_item_id)
            return session.exec(statement).one()

    def get_order_by_id(self, order_id: int) -> Order:
        with Session(self.__db) as session:
            return session.exec(
                select(Order).where(Order.id == order_id).options(selectinload(Order.menu_items))).one()

    def get_orders_by_user_id(self, user_id: int) -> Sequence[Order]:
        with Session(self.__db) as session:
            return session.exec(
                select(Order).where(User.id == user_id).order_by(Order.created_at.desc()).options(
                    selectinload(Order.menu_items))).all()

    def get_total_number_of_orders_by_user_id(self, user_id: int) -> int:
        with Session(self.__db) as session:
            statement = select(func.count(Order.id)).where(Order.user_id == user_id)
            return session.exec(statement).one() or 0

    def get_total_amount_spent_by_user_id(self, user_id: int) -> float:
        with Session(self.__db) as session:
            statement = select(func.sum(Order.total_price)).where(Order.user_id == user_id)
            return session.exec(statement).one() or 0.0

    def get_avg_amount_spent_by_user_id(self, user_id: int) -> float:
        with Session(self.__db) as session:
            statement = select(func.avg(Order.total_price)).where(Order.user_id == user_id)
            return session.exec(statement).one() or 0.0

    def get_most_ordered_item_by_user_id(self, user_id: int) -> str:
        with Session(self.__db) as session:
            statement = (select(MenuItem.name)
                         .join(OrderMenuItems, MenuItem.id == OrderMenuItems.menu_item_id)
                         .join(Order, Order.id == OrderMenuItems.order_id)
                         .filter(Order.user_id == user_id)
                         .group_by(MenuItem.name)
                         .order_by(desc(func.count(OrderMenuItems.menu_item_id)))
                         .limit(1))
            try:
                return session.exec(statement).one()
            except NoResultFound:
                return "None"
