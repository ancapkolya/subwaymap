import datetime
import json

from peewee import *


connection = SqliteDatabase('data/data.db')


class BaseModel(Model):

    class Meta:
        database = connection


class JsonModel(BaseModel):

    def save(self, *args, **kwargs):
        self.dump_data()
        super().save(*args, **kwargs)

    def load_data(self):
        for field in self._meta.json_fields:
            if self.__data__[field].__class__.__name__ == 'str':
                self.__data__[field] = json.loads(self.__data__[field])

    def dump_data(self):
        for field in self._meta.json_fields:
            if self.__data__[field].__class__.__name__ != 'str':
                self.__data__[field] = json.dumps(self.__data__[field])

    class Meta:
        json_fields = []


# models
class GameData(JsonModel):

    data = TextField(default={})

    class Meta:
        json_fields = ['data']


class GameSession(JsonModel):

    score = IntegerField(default=0)
    level = IntegerField(default=0)
    cash_amount = IntegerField(default=5000)

    map = TextField()
    centers = TextField()
    datetime = DateTimeField(default=datetime.datetime(year=2000, month=1, day=1, hour=1, minute=1, second=1, microsecond=1))

    meta_data = TextField(default={'lines_len': 0, })

    class Meta:
        json_fields = ['map', 'centers', 'meta_data']

    def check_meta(self):
        if self.meta_data.__class__.__name__ != 'str':
            if 'lines_len' not in self.meta_data or ('lines_len' in self.meta_data and self.meta_data['lines_len'].__class__.__name__ not in ['int', 'float']):
                self.meta_data['lines_len'] = int(sum([((line.start.x-line.end.x)**2+(line.start.y-line.end.y)**2)**0.5 // 30 for line in self.lines]))


class Station(BaseModel):

    game = ForeignKeyField(GameSession, backref='stations')

    x = IntegerField()
    y = IntegerField()

    def get_lines(self):
        return self.lines_1 + self.lines_2


class Line(BaseModel):

    game = ForeignKeyField(GameSession, backref='lines')

    start = ForeignKeyField(Station, backref='lines_1')
    end = ForeignKeyField(Station, backref='lines_2')

    @property
    def routes(self):
        res = []
        for route in Route.select():
            route.load_data()
            if self.id in route.lines_queue:
                res.append(route)
        return res


ROUTES_COLORS = [
    'red',
    'green',
    'blue',
    'yellow',
    'pink',
    'purple',
    'black',
    'gray'
]


class Route(JsonModel):
    game = ForeignKeyField(GameSession, backref='routes')

    lines_queue = TextField(default='[]')

    train_n = IntegerField()
    color = IntegerField()

    class Meta:
        json_fields = ['lines_queue']

    # ???? ?????????????????? peewee.ManyToMany ???????????? ?????? ?????? ???? ?????????????????? ???????????????????????????????????? ??????????
    @property
    def lines(self):
        if self.lines_queue.__class__.__name__ == 'str':
            self.lines_queue = json.loads(self.lines_queue)
        res = [Line.get_by_id(id) for id in self.lines_queue]
        self.lines_queue = json.dumps(self.lines_queue)
        return res


get_route_color = lambda pk: len(GameSession.get_by_id(pk).routes) % 7


# creating models
if __name__ == '__main__':
    connection.create_tables([GameData, GameSession, Line, Station, Route])