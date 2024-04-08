from datetime import datetime
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship


class OrderStatus(str, Enum):
    CREATED = "created"
    COOKING = "cooking"
    READY = "ready to take"
    DONE = "done"
    CANCELLED = "cancelled"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    phone_number: str
    orders: list["Order"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "delete"})


class Admin(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    password: str


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
    weight: int
    radius: int
    orders: list["Order"] = Relationship(back_populates="menu_items",
                                         link_model=OrderMenuItems)


class Order(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )
    total_price: float
    status: OrderStatus = Field()
    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="orders")
    menu_items: list[MenuItem] = Relationship(back_populates="orders",
                                              link_model=OrderMenuItems)
