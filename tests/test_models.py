from datetime import datetime, timedelta

import pytest

from app.models import Parking, ClientParking, Client
from app.views import calculate_cost
from tests.factories import ClientFactory, ParkingFactory


class TestGetEndpoints:
    """Тестирование GET-методов"""

    # Позитивные тесты +
    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/clients",
            "/api/parkings",
        ],
    )
    def test_list_endpoints_success(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

    # Негативные тесты +
    @pytest.mark.parametrize(
        "endpoint", ["/api/clients/999", "/api/parkings/888", "/api/nonexistent"]
    )
    def test_nonexistent_endpoints(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code == 404

    def test_get_existing_client(self, client, sample_client):
        """Получение существующего клиента по ID +"""
        client_id = sample_client.id
        response = client.get(f"/api/clients/{client_id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["id"] == client_id
        assert data["name"] == sample_client.name
        assert data["surname"] == sample_client.surname
        assert data["car_number"] == sample_client.car_number

    @pytest.mark.parametrize("client_id", [999, -1, 0, 456])
    def test_get_nonexisting_client(self, client, client_id):
        """Получение несуществующего клиента по ID +"""
        response = client.get(f"/api/clients/{client_id}")
        assert response.status_code == 404
        assert "Client not found"
        # assert 'Client not found' in response.get_json()['error']

    def test_get_client_invalid_id_type(self, client):
        """Получение клиента с некорректным ID (строка) +"""
        response = client.get("/api/client/lala")
        assert response.status_code == 404


class TestCreate:
    """Тестирование создания клиентов и парковок"""

    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": "Bob",
                "surname": "Marli",
                "car_number": "C333CC",
                "credit_card": "0987-6543-2109-8765",
            },
            {
                "name": "Lady",
                "surname": "Gaga",
                "car_number": "E555EE",
                "credit_card": "2109-8765-0987-6543",
            },
        ],
    )
    def test_create_client_success(self, client, data):
        """Тест проверки создания клиента +"""
        response = client.post("/api/clients", json=data)
        assert response.status_code == 201

    # ЗАДАНИЕ 4
    def test_create_client_with_factory(self, db_session):
        """Тест создания клиента с использованием фабрики +"""
        client = ClientFactory.create()

        saved_client = db_session.get(Client, client.id)
        assert saved_client is not None
        assert saved_client.name == client.name
        assert saved_client.surname == client.surname
        assert saved_client.credit_card == client.credit_card
        assert saved_client.car_number == client.car_number

    @pytest.mark.parametrize(
        "data",
        [
            {
                "name": None,
                "surname": "Petrov",
                "car_number": "C333CC",
                "credit_card": "0987-6543-2109-8765",
            },
            {
                "name": "Lady",
                "surname": None,
                "car_number": "E555EE",
                "credit_card": "2109-8765-0987-6543",
            },
        ],
    )
    def test_no_name_create_client(self, client, data):
        """Негативный тест создания клиента (нет имени/фамилии) +"""
        response = client.post("/api/clients", json=data)
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "data",
        [
            {
                "address": "St. Petersburg, Nevsky avenue, 1",
                "opened": True,
                "count_places": 28,
                "count_available_places": 14,
            },
            {
                "address": "St. Petersburg, Nevsky avenue, 2",
                "opened": False,
                "count_places": 34,
                "count_available_places": 17,
            },
        ],
    )
    def test_create_parking_success(self, client, data):
        """Тест проверки создания парковки +"""
        response = client.post("/api/parkings", json=data)
        assert response.status_code == 201

    # ЗАДАНИЕ 4
    def test_create_parking_with_factory(self, db_session):
        """Тест создания парковки с использованием фабрики +"""
        parking = ParkingFactory.create()

        saved_parking = db_session.get(Parking, parking.id)
        assert saved_parking is not None
        assert saved_parking.address == parking.address
        assert saved_parking.opened == parking.opened
        assert saved_parking.count_places == parking.count_places
        assert saved_parking.count_available_places == parking.count_available_places


class TestParkingAPI:
    """Тестирование парковочных операций"""

    ############### ЗАЕЗД НА ПАРКОВКУ ###############
    def test_enter_success(self, client, sample_client, sample_parking):
        """Позитивный тест заезда на парковку +"""
        # Запоминаем количество свободных мест ДО
        initial_spots = sample_parking.count_available_places
        # Делаем запрос
        response = client.post(
            "/api/client_parkings/enter",
            json={"client_id": sample_client.id, "parking_id": sample_parking.id},
        )
        # Проверяем статус ответа
        assert response.status_code == 201
        # Проверяем содержимое ответа
        data = response.get_json()
        assert data["message"] == "Car entered successfully"
        assert "client_parking_id" in data
        assert "time_in" in data
        # Проверяем БД: появилась ли запись
        log = ClientParking.query.filter_by(
            client_id=sample_client.id, parking_id=sample_parking.id, time_out=None
        ).first()
        assert log is not None
        # Проверяем БД: уменьшилось ли количество мест
        updated_parking = Parking.query.get(sample_parking.id)
        assert updated_parking.count_available_places == initial_spots - 1


    def test_enter_no_spots(self, client, sample_client, full_parking):
        """Заезд на заполненную парковку +"""
        response = client.post(
            "/api/client_parkings/enter",
            json={"client_id": sample_client.id, "parking_id": full_parking.id},
        )
        assert response.status_code == 400
        assert "No available places" in response.get_json()["error"]


    def test_enter_to_close_parking(self, client, sample_client, closed_parking):
        """Заезд на закрытую парковку +"""
        response = client.post(
            "/api/client_parkings/enter",
            json={"client_id": sample_client.id, "parking_id": closed_parking.id},
        )
        assert response.status_code == 400
        assert "Parking is closed" in response.get_json()["error"]


    def test_enter_with_nonexists_client(self, client, sample_parking):
        """Заезд на парковку с несуществующим клиентом +"""
        response = client.post(
            "/api/client_parkings/enter",
            json={"client_id": 99999, "parking_id": sample_parking.id},
        )
        assert response.status_code == 404
        assert "Client not found" in response.get_json()["error"]

    ############### ВЫЕЗД С ПАРКОВКИ ###############
    def test_exit_success(self, client, active_parking_log):
        """Позитивный тест выезда с парковки +"""
        parking = Parking.query.get(active_parking_log.parking_id)
        initial_spots = parking.count_available_places

        db_client = Client.query.get(active_parking_log.client_id)
        assert db_client.credit_card is not None

        # Делаем запрос
        response = client.delete(
            "/api/client_parkings/exit",
            json={
                "client_id": active_parking_log.client_id,
                "parking_id": active_parking_log.parking_id,
            },
        )

        # Проверяем ответ
        assert response.status_code == 200
        data = response.get_json()

        assert data["message"] == "Car exited successfully"
        assert "cost" in data
        assert data["payment_status"] == "paid"
        assert "payment_message" in data
        assert "time_in" in data
        assert "time_out" in data
        assert "duration_minutes" in data

        updated_log = ClientParking.query.get(active_parking_log.id)
        assert updated_log.time_out is not None
        assert updated_log.time_out > updated_log.time_in

        now = datetime.utcnow()
        assert updated_log.time_out >= now - timedelta(seconds=15)

        assert ClientParking.query.get(active_parking_log.id) is not None

        updated_parking = Parking.query.get(active_parking_log.parking_id)
        assert updated_parking.count_available_places == initial_spots + 1

        duration_minutes = (
            updated_log.time_out - updated_log.time_in
        ).total_seconds() / 60
        expected_cost = calculate_cost(duration_minutes)
        assert data["cost"] == expected_cost
