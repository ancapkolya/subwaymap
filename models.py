import datetime
import json

from peewee import *


connection = SqliteDatabase('data.db')


class BaseModel(Model):

    class Meta:
        database = connection


class JsonModel(BaseModel):

    def save(self, *args, **kwargs):
        for field in self._meta.json_fields:
            self.__data__[field] = json.dumps(self.__data__[field])
        super().save(*args, **kwargs)

    def load_data(self):
        for field in self._meta.json_fields:
            self.__data__[field] = json.loads(self.__data__[field])

    class Meta:
        json_fields = []


# models
class GameSession(JsonModel):
    score = IntegerField(default=0)
    map = TextField()
    centers = TextField()
    datetime = DateTimeField(default=datetime.datetime(year=2000, month=1, day=1, hour=1, minute=1, second=1, microsecond=1))

    class Meta:
        json_fields = ['map', 'centers']


class Station(BaseModel):
    game = ForeignKeyField(GameSession, backref='stations')
    x = IntegerField()
    y = IntegerField()


class Line(JsonModel):
    game = ForeignKeyField(GameSession, backref='lines')
    stations = TextField()

    class Meta:
        json_fields = ['stations']


class Route(JsonModel):
    game = ForeignKeyField(GameSession, backref='routes')
    stations = TextField()
    train_n = IntegerField()

    class Meta:
        json_fields = ['stations']


# creating models
if __name__ == '__main__':
    connection.create_tables([GameSession, Line, Station, Route])