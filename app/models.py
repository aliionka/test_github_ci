from datetime import datetime, timezone
from . import db


class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    credit_card = db.Column(db.String(50), unique=True)
    car_number = db.Column(db.String(6), unique=True)

    # связь с парковками
    parkings = db.relationship(
        "ClientParking", back_populates="client", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "credit_card": self.credit_card,
            "car_number": self.car_number,
        }


class Parking(db.Model):
    __tablename__ = "parking"

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False, unique=True)
    opened = db.Column(db.Boolean, default=True)
    count_places = db.Column(db.Integer, nullable=False)
    count_available_places = db.Column(db.Integer, nullable=False)

    # связь с клиентами
    clients = db.relationship(
        "ClientParking", back_populates="parking", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "address": self.address,
            "opened": self.opened,
            "count_places": self.count_places,
            "count_available_places": self.count_available_places,
        }


class ClientParking(db.Model):
    __tablename__ = "client_parking"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"))
    parking_id = db.Column(db.Integer, db.ForeignKey("parking.id", ondelete="CASCADE"))
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    time_out = db.Column(db.DateTime, nullable=True)

    client = db.relationship("Client", back_populates="parkings")
    parking = db.relationship("Parking", back_populates="clients")
