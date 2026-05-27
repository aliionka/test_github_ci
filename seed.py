"""Скрипт для заполнения базы данных тестовыми данными"""

from datetime import datetime, timedelta
from app import create_app
from app import db
from app.models import Client, Parking, ClientParking


def clear_database():
    """Очистка всех таблиц"""
    print("🗑️  Очистка базы данных...")
    db.session.query(ClientParking).delete()
    db.session.query(Client).delete()
    db.session.query(Parking).delete()
    db.session.commit()
    print("✅ База данных очищена")


def create_clients():
    """Создание тестовых клиентов"""
    print("👥 Создание клиентов...")
    clients = [
        Client(
            name="Иван",
            surname="Петров",
            credit_card="1111-2222-3333-4444",
            car_number="A123BC",
        ),
        Client(
            name="Мария",
            surname="Иванова",
            credit_card="2222-3333-4444-5555",
            car_number="B456CD",
        ),
        Client(
            name="Алексей",
            surname="Сидоров",
            credit_card="3333-4444-5555-6666",
            car_number="C789EF",
        ),
        Client(
            name="Елена",
            surname="Кузнецова",
            credit_card="4444-5555-6666-7777",
            car_number="D012GH",
        ),
        Client(
            name="Дмитрий",
            surname="Смирнов",
            credit_card="5555-6666-7777-8888",
            car_number="E345IJ",
        ),
        Client(
            name="Ольга",
            surname="Волкова",
            credit_card=None,  # без кредитной карты
            car_number="F678KL",
        ),
    ]

    for client in clients:
        db.session.add(client)

    db.session.commit()
    print(f"✅ Создано {len(clients)} клиентов")
    return clients


def create_parkings():
    """Создание тестовых парковок"""
    print("🅿️  Создание парковок...")
    parkings = [
        Parking(
            address="ул. Ленина, 10",
            opened=True,
            count_places=50,
            count_available_places=50,
        ),
        Parking(
            address="пр. Мира, 25",
            opened=True,
            count_places=30,
            count_available_places=25,  # 5 мест занято
        ),
        Parking(
            address="ул. Гагарина, 5",
            opened=False,  # закрытая парковка
            count_places=20,
            count_available_places=20,
        ),
        Parking(
            address="ул. Пушкина, 15",
            opened=True,
            count_places=100,
            count_available_places=85,  # 15 мест занято
        ),
    ]

    for parking in parkings:
        db.session.add(parking)

    db.session.commit()
    print(f"✅ Создано {len(parkings)} парковок")
    return parkings


def create_parking_logs(clients, parkings):
    """Создание истории въездов-выездов"""
    print("📝 Создание логов парковки...")

    logs = []

    # 1. Активная парковка (клиент сейчас на парковке)
    log1 = ClientParking(
        client_id=clients[0].id,  # Иван Петров
        parking_id=parkings[1].id,  # пр. Мира, 25
        time_in=datetime.utcnow() - timedelta(hours=2),  # заехал 2 часа назад
        time_out=None,  # ещё не выезжал
    )
    logs.append(log1)

    # 2. Завершённая парковка (сегодня)
    log2 = ClientParking(
        client_id=clients[1].id,  # Мария Иванова
        parking_id=parkings[0].id,  # ул. Ленина, 10
        time_in=datetime.utcnow() - timedelta(hours=5),
        time_out=datetime.utcnow() - timedelta(hours=3),  # стояла 2 часа
    )
    logs.append(log2)

    # 3. Завершённая парковка (вчера)
    log3 = ClientParking(
        client_id=clients[2].id,  # Алексей Сидоров
        parking_id=parkings[3].id,  # ул. Пушкина, 15
        time_in=datetime.utcnow() - timedelta(days=1, hours=3),
        time_out=datetime.utcnow() - timedelta(days=1, hours=1),  # стоял 2 часа
    )
    logs.append(log3)

    # 4. Ещё одна активная парковка
    log4 = ClientParking(
        client_id=clients[3].id,  # Елена Кузнецова
        parking_id=parkings[3].id,  # ул. Пушкина, 15
        time_in=datetime.utcnow() - timedelta(hours=30),  # заехал вчера
        time_out=None,  # всё ещё на парковке
    )
    logs.append(log4)

    # 5. Долгая парковка (неделю назад)
    log5 = ClientParking(
        client_id=clients[4].id,  # Дмитрий Смирнов
        parking_id=parkings[0].id,  # ул. Ленина, 10
        time_in=datetime.utcnow() - timedelta(days=7, hours=10),
        time_out=datetime.utcnow() - timedelta(days=7, hours=8),  # стоял 2 часа
    )
    logs.append(log5)

    # 6. Попытка заехать на закрытую парковку (создаём, но парковка закрыта - добавим для теста)
    # Этот лог будет создан, но парковка закрыта - тестовая ситуация
    log6 = ClientParking(
        client_id=clients[5].id,  # Ольга Волкова
        parking_id=parkings[2].id,  # ул. Гагарина, 5 (закрыта!)
        time_in=datetime.utcnow() - timedelta(hours=1),
        time_out=datetime.utcnow() - timedelta(minutes=30),  # быстро выехал
    )
    logs.append(log6)

    for log in logs:
        db.session.add(log)

    # Обновляем количество свободных мест на парковках в соответствии с логами
    # Парковка 1 (ул. Ленина, 10) - изначально 50 мест
    # Лог2: занято, Лог5: было занято (уже выехал) - итого: 1 место занято в данный момент
    parkings[0].count_available_places = (
        49  # 1 место занято (Мария уже выехала, но лог4 на другой)
    )

    # Парковка 2 (пр. Мира, 25) - изначально 25 мест свободно
    # Лог1: активная парковка - 1 место занято
    parkings[1].count_available_places = 24  # Иван на парковке

    # Парковка 3 (ул. Гагарина, 5) - закрыта, 20 мест свободно
    # (не меняем)

    # Парковка 4 (ул. Пушкина, 15) - изначально 85 мест свободно
    # Лог3: завершена, Лог4: активна - итого: 1 место занято
    parkings[3].count_available_places = 84  # Елена на парковке

    db.session.commit()
    print(f"✅ Создано {len(logs)} логов парковки")


def show_statistics():
    """Вывод статистики после заполнения"""
    print("\n" + "=" * 50)
    print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("=" * 50)

    clients = Client.query.all()
    print(f"\n👥 Клиенты: {len(clients)}")
    for client in clients:
        active_logs = ClientParking.query.filter_by(
            client_id=client.id, time_out=None
        ).all()
        active_status = "🔴 НА ПАРКОВКЕ" if active_logs else "⚪ СВОБОДЕН"
        print(
            f"  - {client.name} {client.surname} ({client.car_number}) - {active_status}"
        )

    parkings = Parking.query.all()
    print(f"\n🅿️  Парковки: {len(parkings)}")
    for parking in parkings:
        status = "🟢 ОТКРЫТА" if parking.opened else "🔴 ЗАКРЫТА"
        occupied = parking.count_places - parking.count_available_places
        print(
            f"  - {parking.address}: {status}, свободно {parking.count_available_places}/{parking.count_places} мест (занято {occupied})"
        )

    active_parkings = ClientParking.query.filter_by(time_out=None).all()
    print(f"\n🚗 Активных парковок: {len(active_parkings)}")
    for log in active_parkings:
        client = Client.query.get(log.client_id)
        parking = Parking.query.get(log.parking_id)
        print(
            f"  - {client.name} {client.surname} на {parking.address} с {log.time_in.strftime('%H:%M:%S')}"
        )

    print("\n" + "=" * 50)


def main():
    """Основная функция"""
    print("🚀 ЗАПУСК СКРИПТА ЗАПОЛНЕНИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)

    # Создаём приложение
    app = create_app()

    with app.app_context():
        try:
            # Очищаем существующие данные
            clear_database()

            # Создаём тестовые данные
            clients = create_clients()
            parkings = create_parkings()
            create_parking_logs(clients, parkings)

            # Показываем статистику
            show_statistics()

            print("\n✅ База данных успешно заполнена тестовыми данными!")

        except Exception as e:
            print(f"\n❌ Ошибка при заполнении базы данных: {str(e)}")
            db.session.rollback()


if __name__ == "__main__":
    main()
