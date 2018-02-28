from django.db import transaction
from _generators import *
import inspect
import shelve
import os

from users.models import Users, Rewards, WaveRelations, UserSocials
from waves.models import Waves, Steps
from relations.models import UserRelations, Invites


class Shape(object):

    def __new__(cls):
        cls._generators = {}
        cls._meta = {}
        cls._rules = {}
        attrs = cls.__dict__
        for key, value in attrs.iteritems():
            if inspect.isfunction(value):
                if key.startswith('_rule'):
                    if key == '_rule':
                        cls._rules['_all'] = value
                    else:
                        cls._rules[key[6:]] = value
            else:
                parents = inspect.getmro(type(value))
                for parent in parents:
                    if parent == Generator:
                        cls._generators[key] = value

        meta = attrs.get('Meta', None)
        cls._meta['model'] = getattr(meta, 'model', None)
        cls._meta['unique'] = getattr(meta, 'unique', None)
        cls._meta['bonds'] = getattr(meta, 'bonds', None)

        return super(Shape, cls).__new__(cls)

    def __len__(self):
        return len(self._generators)

    def __getitem__(self, key):
        return self._generators[key]

    def __setitem__(self, key, value):
        self._generators[key] = value

    def __delitem__(self, key):
        del self._generators[key]

    def __iter__(self):
        return self._generators.iteritems()

    def __contains__(self, key):
        return key in self._generators

    def _generate(self, amount):
        result = []
        success_counter = all_counter = 0
        while(success_counter < amount and all_counter < amount * 1.2):
            all_counter += 1
            shape = {}
            try:
                for fieldname, generator in self:
                    shape[fieldname] = self._generate_field(fieldname,
                                                            generator)
            except:
                continue

            if '_all' in self._rules:
                status = self._rules['_all'](self, shape)
                if not status:
                    continue

            result.append(shape)
            success_counter += 1

        return result

    def _generate_field(self, fieldname, generator):
        if fieldname in self._rules:
            for _ in range(10):
                value = generator.generate()
                status = self._rules[fieldname](self, value)
                if status:
                    return value
            raise Exception('Too hard rules for this generator')
        else:
            return generator.generate()

    def _serialize(self, action, objects=[]):
        sf_key = self._meta['model'].__name__
        sf = shelve.open(os.path.join(os.path.dirname(__file__),
                                      'Generated.sr'))

        data = sf.get(sf_key, [])
        if action == 'add':
            ids = [x.pk for x in objects]
            data.append(ids)
            sf[sf_key] = data
        elif action == 'delete_last':
            if len(data):
                data.pop(-1)
                sf[sf_key] = data
        elif action == 'delete_all':
            sf[sf_key] = []

        sf.close()

    def _deserialize(self):
        sf_key = self._meta['model'].__name__
        sf = shelve.open(os.path.join(os.path.dirname(__file__),
                                      'Generated.sr'))
        data = sf.get(sf_key, [])
        sf.close()
        return data

    def _check_unique(self, objects):
        len_objects = len(objects)
        if self._meta['unique']:
            items = None
            if getattr(self, '_unique_items', None):
                items = self._unique_items
            else:
                fields = reduce(lambda x, y: list(x) + list(y),
                                self._meta['unique'])
                items = self._meta['model'].objects.all().values(*set(fields))
                items = list(items)
                self._unique_items = items

            for unique in self._meta['unique']:
                all_items = objects + items
                all_items = sorted(all_items,
                                   key=lambda x: [x[y] for y in unique])

                last_item = (None, None)
                for item in all_items:
                    cur_item = ''
                    for field in unique:
                        cur_item += str(item[field])
                    if cur_item == last_item[0]:
                        if last_item[1] in objects:
                            objects.remove(last_item[1])
                        elif item in objects:
                            objects.remove(cur_item)
                    last_item = (cur_item, item)

            if len(objects) == len_objects:
                return {'success': True}
            else:
                return {'success': False, 'amount': len_objects - len(objects)}

        return {'success': True}

    def delete_last(self):
        ids = self._deserialize()
        Model = self._meta['model']
        if len(ids):
            ids = set(ids[-1])
            amount = Model.objects.filter(id__in=ids).delete()[0]
            self._serialize('delete_last')
            return amount
        return 0

    def delete_all(self):
        ids = self._deserialize()
        Model = self._meta['model']
        if len(ids):
            ids = set(reduce(lambda x, y: x + y, ids))
            amount = Model.objects.filter(id__in=ids).delete()[0]
            self._serialize('delete_all')
            return amount
        return 0

    @transaction.atomic
    def create(self, amount=1):
        shapes = []
        for i in range(10):
            shapes += self._generate(amount)
            status = self._check_unique(shapes)
            if status['success']:
                break
            else:
                amount = status['amount']

        Model = self._meta['model']
        result = []
        if Model:
            for shape in shapes:
                result.append(Model.objects.create(**shape))
        self._serialize('add', result)
        return result


'''
Example:

class UsersShape(Shape):
    user_url = StrGenerator(min_len=30, max_len=30)
    name = WordsGenerator(amount=3, min_len=3, max_len=10, capital=True)
    country = ChoiceGenerator(choices=['Russia', 'USA', 'Germany',
                                       'Brazil', 'Argentina'])
    city = ChoiceGenerator(choices=['Moscow', 'Saint-Petersburg', 'Budapest',
                                    'New York'])
    gender = ChoiceGenerator(choices=['m', 'f'])
    birthday = DateGenerator()
    info = TextGenerator(min_len=30, max_len=160)
    avatar_exists = ChoiceGenerator(choices=[False])
    mail = WordsGenerator(min_len=8, max_len=15, pattern='<gen>@yandex.ru')
    likes = IntGenerator(min=0, max=10000)
    views = IntGenerator(min=0, max=100000)
    followers = IntGenerator(min=0, max=10000)
    subs = IntGenerator(min=0, max=100)
    url_counter = IntGenerator(min=0, max=1)
    notifications = IntGenerator(min=0, max=255)
    teacher = IntGenerator(min=1000, max=10000)


    def _rule(self, shape):
        if shape['likes'] > shape['views']:
            return False
        else:
            return True

    class Meta:
        model = Users
        unique = [['user_url'], ['mail']]
        bonds = {'teacher': (TeachersShape, 'id')}
'''