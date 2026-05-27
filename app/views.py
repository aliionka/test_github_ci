import math

from flask import Blueprint, jsonify, request
from . import db
from .models import Client, Parking, ClientParking
from datetime import datetime, timezone

bp = Blueprint("api", __name__, url_prefix="/api")


# =============== РОУТЫ ДЛЯ КЛИЕНТОВ ===============
@bp.route("/clients", methods=["GET"])
def get_clients():
    """Получение всех клиентов +"""
    try:
        clients = Client.query.all()
        return jsonify([c.to_dict() for c in clients]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/clients/<int:client_id>", methods=["GET"])
def get_client_by_id(client_id):
    """Получение клиентов по id +"""
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client.to_dict()), 200


@bp.route("/clients", methods=["POST"])
def create_client():
    """Создание клиента +"""
    try:
        client_data = request.get_json()
        # Валидация обязательных полей
        if not client_data.get("name") or not client_data.get("surname"):
            return jsonify({"error": "Name and surname are required"}), 400

        # Проверка уникальности car_number (если указан)
        car_number = client_data.get("car_number")
        if car_number:
            existing = Client.query.filter_by(car_number=car_number).first()
            if existing:
                return jsonify({"error": "Car number already exists"}), 409

        # Проверка уникальности credit_card (если указан)
        credit_card = client_data.get("credit_card")
        if credit_card:
            existing = Client.query.filter_by(credit_card=credit_card).first()
            if existing:
                return jsonify({"error": "Credit card already exists"}), 409

        client = Client(
            name=client_data.get("name"),
            surname=client_data.get("surname"),
            credit_card=client_data.get("credit_card"),
            car_number=client_data.get("car_number"),
        )
        db.session.add(client)
        db.session.commit()
        return jsonify(client.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =============== РОУТЫ ДЛЯ ПАРКОВОК ===============
@bp.route("/parkings", methods=["GET"])
def get_parkings():
    """Получение всех парковок +"""
    try:
        parkings = Parking.query.all()
        return jsonify([p.to_dict() for p in parkings]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/parkings", methods=["POST"])
def create_parking():
    """Создание парковки +"""
    try:
        parking_data = request.get_json()
        # Валидация обязательных полей
        if (
            not parking_data.get("address")
            or not parking_data.get("count_places")
            or not parking_data.get("count_available_places")
        ):
            return (
                jsonify(
                    {
                        "error": "Address, count places and count available places are required"
                    }
                ),
                400,
            )

        # Проверка уникальности address
        address = parking_data.get("address")
        if address:
            existing = Parking.query.filter_by(address=address).first()
            if existing:
                return jsonify({"error": "Address already exists"}), 409

        parking = Parking(
            address=parking_data.get("address"),
            opened=parking_data.get("opened", True),
            count_places=parking_data.get("count_places"),
            count_available_places=parking_data.get("count_available_places"),
        )
        db.session.add(parking)
        db.session.commit()
        return jsonify(parking.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =============== РОУТЫ ДЛЯ ВЪЕЗДА/ВЫЕЗДА ===============
@bp.route("/client_parkings/enter", methods=["POST"])
def check_in_to_the_parking():
    """Заезд на парковку +"""
    try:
        data = request.get_json()
        client_id = data.get("client_id")
        parking_id = data.get("parking_id")

        if not client_id or not parking_id:
            return jsonify({"error": "Client ID and Parking ID are required"}), 400

        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": "Client not found"}), 404

        parking = Parking.query.get(parking_id)
        if not parking:
            return jsonify({"error": "Parking not found"}), 404

        # Открыта ли парковка
        if not parking.opened:
            return jsonify({"error": "Parking is closed"}), 400

        # Есть ли свободные места
        if parking.count_available_places <= 0:
            return jsonify({"error": "No available places"}), 400

        # Проверяем, не находится ли уже клиент на этой парковке
        active_parking = ClientParking.query.filter_by(
            client_id=client_id, parking_id=parking_id, time_out=None
        ).first()

        if active_parking:
            return jsonify({"error": "Client already on this parking"}), 400

        active_anywhere = ClientParking.query.filter_by(
            client_id=client_id, time_out=None
        ).first()

        if active_anywhere:
            return jsonify({"error": "Client already on another parking"}), 400

        client_parking = ClientParking(
            client_id=client_id,
            parking_id=parking_id,
            time_in=datetime.now(timezone.utc),
        )

        # Уменьшаем количество свободных мест
        parking.count_available_places -= 1

        db.session.add(client_parking)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Car entered successfully",
                    "client_parking_id": client_parking.id,
                    "time_in": client_parking.time_in.isoformat(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def process_payment(credit_card, amount):
    """Функция для проверки карты и списания средств"""

    class PaymentResult:
        def __init__(self, success, message):
            self.success = success
            self.message = message

    if not credit_card:
        return PaymentResult(False, "Credit card is required")

    if amount < 0:
        return PaymentResult(False, "Amount must be positive")

    if amount == 0:
        return PaymentResult(True, "Free parking")

    return PaymentResult(True, f"Payment of {amount} rubles successful")


def calculate_cost(duration_minutes):
    """Рассчитывает стоимость парковки на основе времени"""
    # Тарифы:
    # - первые 15 минут: бесплатно
    # - следующие 45 минут: 100 рублей
    # - каждый следующий час: 50 рублей

    if duration_minutes <= 15:
        return 0
    elif duration_minutes <= 60:
        return 100
    else:
        additional_hours = math.ceil((duration_minutes - 60) / 60)
        return 100 + (additional_hours * 50)


@bp.route("/client_parkings/exit", methods=["DELETE"])
def exit_from_the_parking_lot():
    """Выезд с парковки +"""
    try:
        data = request.get_json()
        client_id = data.get("client_id")
        parking_id = data.get("parking_id")

        if not client_id or not parking_id:
            return jsonify({"error": "Client ID and Parking ID are required"}), 400

        # Ищем активную запись о парковке
        client_parking = ClientParking.query.filter_by(
            client_id=client_id, parking_id=parking_id, time_out=None
        ).first()

        if not client_parking:
            return jsonify({"error": "No active parking record found"}), 400

        client = Client.query.get(client_id)
        if not client.credit_card:
            return (
                jsonify({"error": "No credit card linked. Please add payment method"}),
                402,
            )

        time_out = datetime.utcnow()
        duration_seconds = (time_out - client_parking.time_in).total_seconds()
        duration_minutes = duration_seconds / 60

        cost = calculate_cost(duration_minutes)

        # Обработка платежа
        payment_result = process_payment(client.credit_card, cost)
        if not payment_result.success:
            return jsonify({"error": payment_result.message}), 402

        # Обновление данных после успешной оплаты
        client_parking.time_out = time_out

        parking = Parking.query.get(parking_id)
        # Увеличиваем количество свободных мест
        if parking:
            parking.count_available_places += 1

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Car exited successfully",
                    "cost": cost,
                    "payment_status": "paid",
                    "payment_message": payment_result.message,
                    "time_in": client_parking.time_in.isoformat(),
                    "time_out": client_parking.time_out.isoformat(),
                    "duration_minutes": round(duration_minutes, 2),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
