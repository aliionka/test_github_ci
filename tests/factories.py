# from factory.fuzzy import FuzzyChoice
import random

import factory
from factory import LazyAttribute
from factory.alchemy import SQLAlchemyModelFactory
from app.models import Client, Parking
from app import db


class ClientFactory(SQLAlchemyModelFactory):
    """Фабрика для создания клиентов в БД"""

    class Meta:
        model = Client  # для какой модели эта фабрика
        sqlalchemy_session = db.session  # сессия для сохранения в БД
        sqlalchemy_session_persistence = (
            "flush"  # чтобы ClientFactory.create() автоматически сохранял объект
        )

    # Поля, реалистичные значения которых генерируются динамически
    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")

    credit_card = LazyAttribute(
        lambda _: random.choice(
            [
                None,
                factory.Faker("credit_card_number").evaluate(
                    None, None, {"locale": None}
                ),
            ]
        )
    )  # карта или есть, или нет
    car_number = factory.Faker("bothify", text="?###??")
    # ☝️генерирует строку по шаблону (где ? — буква, # — цифра)


class ParkingFactory(SQLAlchemyModelFactory):
    """Фабрика для создания парковок в БД"""

    class Meta:
        model = Parking  # для какой модели эта фабрика
        sqlalchemy_session = db.session  # сессия для сохранения в БД
        sqlalchemy_session_persistence = "flush"

    # Поля, реалистичные значения которых генерируются динамически
    address = factory.Faker("address")
    opened = factory.Faker("boolean")  # ИЛИ factory.fuzzy.FuzzyChoice([True, False])
    count_places = factory.Faker("random_int", min=1, max=100)
    count_available_places = factory.LazyAttribute(
        lambda x: x.count_places
    )  # зависит от других полей того же объекта
