# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, utils
from django.core.validators import RegexValidator
from django.utils import timezone
from utils import serpy
from utils.helper import classproperty
from utils.cachephobia import CacheManager, LonerBehavior, PrimitiveHerdBehavior, AdvancedHerdBehavior
from main.models.fields import SoftForeignKey
from main.models.base import ValidateModelMixin
from main.models import choices
from hashlib import sha1
import random


class UsersSerializer(serpy.Serializer):
    login = serpy.StrField()
    name = serpy.StrField()
    role = serpy.StrField()
    salt = serpy.StrField()
    password = serpy.StrField()


class Users(ValidateModelMixin):
    ROLES = (
        ('admin', 'Администратор'),
        ('user', 'Пользователь'),
    )

    login = models.CharField(primary_key=True, max_length=50,
                             validators=[RegexValidator('^[a-zA-Z0-9]*$')])
    name = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLES)
    salt = models.CharField(max_length=16)
    password = models.CharField(max_length=40)

    SERIALIZERS = {
        'all': (UsersSerializer, None),
        'default': (UsersSerializer,
                    ('login', 'name', 'role')),
    }

    @classmethod
    def add(cls, login, password, name, role):
        try:
            salt = ''.join(chr(random.randint(33, 126)) for i in range(16))
            hash = sha1(salt + str(password)).hexdigest()
            user = cls(login=login, salt=salt, password=hash, role=role, name=name)
            user.save()
            return True
        except utils.IntegrityError:
            return False

    @classmethod
    def verify(cls, login, password):
        try:
            user = cls.objects.get(login=login)
            hash = sha1(user.salt + str(password)).hexdigest()
            if hash == user.password:
                return user
            else:
                return None
        except Users.DoesNotExist:
            return None

    def __unicode__(self):
        return '[%s] %s (%s)' % (self.login, self.name, self.role)

    class Meta:
        db_table = 'users'


class StudentsSerializer(serpy.Serializer):
    id = serpy.IntField()
    lastname = serpy.StrField()
    firstname = serpy.StrField()
    phone = serpy.StrField()
    mail = serpy.StrField()
    birthday = serpy.DateField(null=True)
    debt = serpy.IntField()
    comment = serpy.StrField()
    status = serpy.StrField()
    create_time = serpy.DateField()
    creator = serpy.StrField()


class Students(ValidateModelMixin):
    STATUSES = (
        ('a', 'active'),
    )

    id = models.AutoField(primary_key=True)
    lastname = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50)
    phone = models.CharField(max_length=16, blank=True,
                             validators=[RegexValidator('^\+[0-9]*$')])
    mail = models.EmailField(max_length=80, blank=True)
    birthday = models.DateField(null=True, default=None, blank=True)
    debt = models.IntegerField(default=0)
    comment = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=1, choices=STATUSES, default='a')
    create_time = models.DateTimeField(auto_now_add=True)
    creator = models.CharField(max_length=50)

    objects = CacheManager(AdvancedHerdBehavior(where={'status': 'a'}))

    SERIALIZERS = {
        'all': (StudentsSerializer, None),
        'default': (StudentsSerializer,
                    ('id', 'lastname', 'firstname', 'phone', 'mail',
                     'birthday', 'debt', 'comment', 'create_time')),
        'basic': (StudentsSerializer,
                  ('id', 'lastname', 'firstname')),
        'search': (StudentsSerializer,
                   ('id', 'lastname', 'firstname', 'phone', 'comment')),
    }

    @classproperty
    def active(cls):
        return cls.objects.filter(status='a')

    def __unicode__(self):
        if self.id:
            return '[%d] %s %s <%s>' % (self.id, self.lastname,
                                        self.firstname, self.status)
        else:
            return '[NoID] %s %s <%s>' % (self.lastname, self.firstname,
                                          self.status)

    class Meta:
        db_table = 'students'


class TeachersSerializer(serpy.Serializer):
    id = serpy.IntField()
    lastname = serpy.StrField()
    firstname = serpy.StrField()
    middlename = serpy.StrField()
    phone = serpy.StrField()
    mail = serpy.StrField()
    birthday = serpy.DateField(null=True)
    comment = serpy.StrField()
    status = serpy.StrField()
    create_time = serpy.DateField()
    creator = serpy.StrField()


class Teachers(ValidateModelMixin):
    STATUSES = (
        ('a', 'active'),
    )

    id = models.AutoField(primary_key=True)
    lastname = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50)
    middlename = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=16, blank=True,
                             validators=[RegexValidator('^\+[0-9]*$')])
    mail = models.EmailField(max_length=80, blank=True)
    birthday = models.DateField(null=True, default=None, blank=True)
    comment = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=1, choices=STATUSES, default='a')
    create_time = models.DateTimeField(auto_now_add=True)
    creator = models.CharField(max_length=50)

    objects = CacheManager(AdvancedHerdBehavior(where={'status': 'a'}))

    SERIALIZERS = {
        'all': (TeachersSerializer, None),
        'default': (TeachersSerializer,
                    ('id', 'lastname', 'firstname', 'middlename', 'phone',
                     'mail', 'birthday', 'comment', 'create_time')),
        'basic': (TeachersSerializer,
                  ('id', 'lastname', 'firstname', 'middlename')),
        'search': (TeachersSerializer,
                   ('id', 'lastname', 'firstname', 'middlename', 'phone')),
    }

    @classproperty
    def active(cls):
        return cls.objects.filter(status='a')

    def __unicode__(self):
        if self.id:
            return '[%d] %s %s <%s>' % (self.id, self.lastname,
                                        self.firstname, self.status)
        else:
            return '[NoID] %s %s <%s>' % (self.lastname, self.firstname,
                                          self.status)

    class Meta:
        db_table = 'teachers'


class SubscriptionsSerializer(serpy.Serializer):
    id = serpy.IntField()
    student_id = serpy.IntField()
    mode = serpy.StrField()
    lessons_visited = serpy.IntField()
    lessons_total = serpy.IntField()
    date_start = serpy.DateField()
    date_end = serpy.DateField()
    changes_left = serpy.IntField()
    status = serpy.StrField()
    status_date = serpy.DateField()
    create_time = serpy.DateField()
    creator = serpy.StrField()


class Subscriptions(ValidateModelMixin):
    STATUSES = (
        ('a', 'active'),
        ('r', 'archived'),
        ('f', 'frozen'),
        ('d', 'deleted'),
    )

    MODES = choices.MODES

    id = models.AutoField(primary_key=True)
    student = SoftForeignKey(Students, related_name='subscriptions')
    mode = models.CharField(max_length=20, choices=MODES)
    lessons_visited = models.IntegerField(default=0)
    lessons_total = models.IntegerField()
    date_start = models.DateField()
    date_end = models.DateField()
    changes_left = models.IntegerField()
    status = models.CharField(max_length=1, choices=STATUSES, default='a')
    status_date = models.DateTimeField(default=timezone.now)
    create_time = models.DateTimeField(auto_now_add=True)
    creator = models.CharField(max_length=50)

    SERIALIZERS = {
        'all': (SubscriptionsSerializer, None),
        'default': (SubscriptionsSerializer,
                    ('id', 'mode', 'lessons_visited', 'lessons_total',
                     'date_start', 'date_end', 'changes_left', 'status',
                     'status_date')),
    }

    @classproperty
    def active(cls):
        return cls.objects.filter(status__in=('a', 'f'))

    @classproperty
    def archived(cls):
        return cls.objects.filter(status='r')

    def __unicode__(self):
        if self.id:
            return '[%d] {S: %s} %d/%d (%s)-(%s) <%s>' % (
                self.id, self.student_id, self.lessons_visited,
                self.lessons_total, self.date_start, self.date_end, self.status
            )
        else:
            return '[NoID] {S: %s} %d/%d (%s)-(%s) <%s>' % (
                self.student_id, self.lessons_visited, self.lessons_total,
                self.date_start, self.date_end, self.status
            )

    class Meta:
        db_table = 'subscriptions'


class SubTypesSerializer(serpy.Serializer):
    id = serpy.IntField()
    mode = serpy.StrField()
    lessons = serpy.IntField()
    months = serpy.IntField()
    changes = serpy.IntField()


class SubTypes(ValidateModelMixin):
    MODES = choices.MODES

    id = models.AutoField(primary_key=True)
    mode = models.CharField(max_length=20, choices=MODES)
    lessons = models.IntegerField()
    months = models.IntegerField()
    changes = models.IntegerField()

    objects = CacheManager(PrimitiveHerdBehavior())

    SERIALIZERS = {
        'all': (SubTypesSerializer, None),
        'default': (SubTypesSerializer, None),
    }

    def __unicode__(self):
        if self.id:
            return '[%d] %s {l: %d, m: %d, c: %d}' % (
                self.id, self.mode, self.lessons, self.months, self.changes
            )
        else:
            return '[NoID] %s {l: %d, m: %d, c: %d}' % (
                self.mode, self.lessons, self.months, self.changes
            )

    class Meta:
        db_table = 'subtypes'
