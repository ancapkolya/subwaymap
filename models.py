import datetime

from peewee import *
import json


connection = SqliteDatabase('data.db')


# mixins
class EmptyClass: pass


class JsonModel(Model):
    json_fields = []

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


# models
class GameSession(JsonModel):
    score = IntegerField()
    map = TextField()
    centers = TextField()
    datetime = DateTimeField()

    class Meta:
        database = connection
        json_fields = ['map', 'centers']


    def create(cls, **query):
        query['datetime'] = datetime.datetime(2000, 1, 1, 1, 1)
        super().create(cls, **query)


class Line(Model):
    game = ForeignKeyField(GameSession, backref='lines')
    train_n = IntegerField()

    class Meta:
        database = connection


class Station(Model):
    line = ForeignKeyField(GameSession, backref='stations')

    class Meta:
        database = connection


# creating models
if __name__ == '__main__':
    connection.create_tables([GameSession, Line, Station])