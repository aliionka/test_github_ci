from datetime import datetime, timedelta, timezone

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../hw")))

from app import create_app, db as _db
from app.config import config_dict
from app.models import Client, Parking, ClientParking


# Автоматическая очистка таблиц
@pytest.fixture(autouse=True)
def clean_tables(db_session):
    """Очищает таблицы перед каждым тестом"""
    db_session.query(ClientParking).delete()
    db_session.query(Parking).delete()
    db_session.query(Client).delete()
    db_session.commit()
    yield


# ======================= БАЗОВЫЕ ФИКСТУРЫ =======================
@pytest.fixture(scope="session")  # 1 раз на все тесты
def app():
    """Создание тестового приложения"""
    _app = create_app(config_dict["testing"])
    _app.config["TESTING"] = True

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    """Тестовый клиент для запросов"""
    return app.test_client()


@pytest.fixture(scope="function")  # для каждого теста заново
def db_session(app):
    """Сессия БД для каждого теста с очисткой"""
    with app.app_context():
        _db.create_all()
        # Начинаем транзакции
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Привязывем сессию
        _db.session.configure(bind=connection)
        yield _db.session

        # Откатываем транзакцию
        transaction.rollback()
        _db.session.close()
        _db.session.remove()


# ======================= ФИКСТУРЫ КЛИЕНТОВ =======================
@pytest.fixture(scope="function")
def sample_client(db_session):
    """Создание тестового клиента в БД"""
    client = Client(
        name="Sharik",
        surname="Sharikov",
        credit_card="0101-0101-0101-0101",
        car_number="A111AA",
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture(scope="function")
def client_without_card(db_session):
    """Тестовый клиент без кредитной карты"""
    client = Client(
        name="Bobik", surname="Bobikov", credit_card=None, car_number="Б222ББ"
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture(scope="function")
def client_with_active_parking(db_session, sample_parking, active_parking_log):
    """Клиент уже на парковке (с активным логом)"""
    client = Client(
        name="Very",
        surname="Active",
        credit_card="1234-5678-9101-1123",
        car_number="В333ВВ",
    )
    db_session.add(client)
    db_session.commit()

    # активный лог для клиента
    active_log = ClientParking(
        client_id=client.id,
        parking_id=sample_parking.id,
        time_in=datetime.now(timezone.utc) - timedelta(hours=2),
        time_out=None,
    )
    db_session.add(active_log)
    db_session.commit()
    return client


# ======================= ФИКСТУРЫ ПАРКОВОК =======================
@pytest.fixture(scope="function")
def sample_parking(db_session):
    """Создание тестового паркинга в БД"""
    parking = Parking(
        address="Suvorovsky avenue, 10A",
        opened=True,
        count_places=50,
        count_available_places=20,
    )
    db_session.add(parking)
    db_session.commit()
    return parking


@pytest.fixture(scope="function")
def closed_parking(db_session):
    """Закрытая парковка"""
    parking = Parking(
        address="Closed street, 2",
        opened=False,
        count_places=45,
        count_available_places=30,
    )
    db_session.add(parking)
    db_session.commit()
    return parking


@pytest.fixture(scope="function")
def full_parking(db_session):
    """Парковка без свободных мест"""
    parking = Parking(
        address="Full avenue, 2", opened=True, count_places=45, count_available_places=0
    )
    db_session.add(parking)
    db_session.commit()
    return parking


# ======================= ФИКСТУРЫ ЛОГОВ =======================
@pytest.fixture(scope="function")
def sample_parking_log(db_session):
    """Создание тестового лога парковки в БД"""
    parking_log = ClientParking(
        client_id=10,
        parking_id=10,
        time_in=datetime.now(timezone.utc) - timedelta(hours=1),
        time_out=datetime.now(timezone.utc) - timedelta(minutes=30),
    )
    db_session.add(parking_log)
    db_session.commit()
    return parking_log


@pytest.fixture(scope="function")
def active_parking_log(db_session, sample_client, sample_parking):
    """Активный лог для парковки (без time_out)"""
    active_parking_log = ClientParking(
        client_id=sample_client.id,
        parking_id=sample_parking.id,
        time_in=datetime.now(timezone.utc) - timedelta(hours=2),
        time_out=None,  # активно
    )
    db_session.add(active_parking_log)
    db_session.commit()
    return active_parking_log
