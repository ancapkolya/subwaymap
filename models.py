import datetime

from peewee import *
import json


connection = SqliteDatabase('data.db')


# mixins
class EmptyClass: pass


class DefaultModel(Model):
    class Meta:
        database = connection


class JsonModel(DefaultModel):
    def create(cls, **query):
        for field in cls.Meta.json_fields:
            query[field] = json.dumps(query[field])
        return super().create(cls, **query)

    def save(self, *args, **kwargs):
        for field in self.json_fields:
            self.__dict__[field] = json.dumps(self.loaded_data.__dict__[field])
        super().save(*args, **kwargs)

    def load_data(self):
        self.loaded_data = EmptyClass()
        for field in self.json_fields:
            self.loaded_data.__dict__[field] = json.loads(self.__dict__[field])

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


class Station(DefaultModel):
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