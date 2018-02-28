from django.core.exceptions import ValidationError
from api.views import SmartAPIView
from utils.validator import Required, Coerce, NotEmpty, Range, In
from people.models import Users, Students, Teachers, Subscriptions, SubTypes
from logbooks.models import Visits
from schedule.models import Lessons
from api.response import APIResponse
from main import session
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class AuthAPI(SmartAPIView):

    permission_classes = ()
    rules = {
        'POST': {
            'login': (Required, NotEmpty(), Coerce(str)),
            'password': (Required, NotEmpty(), Coerce(str)),
        }
    }

    def post(self, request, format=None):
        login = request.prepared['login']
        password = request.prepared['password']

        user = Users.verify(login, password)
        if user is not None:
            session.init(request.session, user)
            return APIResponse(code=200)
        else:
            return APIResponse(code=404)

    def delete(self, request, format=None):
        if request.authorized:
            request.session.flush()
            return APIResponse(code=200)
        else:
            return APIResponse(code=405)


class StudentAPI(SmartAPIView):

    rules = {
        'GET': {
            'id': (Required, NotEmpty(), Coerce(int)),
        },
        'POST': {
            'lastname': (Required, NotEmpty(), Coerce(unicode)),
            'firstname': (Required, NotEmpty(), Coerce(unicode)),
            'phone': (Coerce(str, if_none='')),
            'mail': (Coerce(str, if_none='')),
            'birthday': (Coerce(datetime, if_blank=None)),
            'debt': (Coerce(int, 0, 0)),
            'comment': (Coerce(unicode, if_none='')),
        },
        'PUT': {
            'id': (Required, NotEmpty(), Coerce(int)),
            'lastname': (NotEmpty(), Coerce(unicode)),
            'firstname': (NotEmpty(), Coerce(unicode)),
            'phone': (Coerce(str, if_none='')),
            'mail': (Coerce(str, if_none='')),
            'birthday': (Coerce(datetime, if_blank=None)),
            'debt': (Coerce(int, 0, 0)),
            'comment': (Coerce(unicode, if_none='')),
        },
    }

    def get(self, request, format=None):
        id = request.prepared['id']

        try:
            student = Students.active.get(pk=id)
        except Students.DoesNotExist as ex:
            return APIResponse(code=404, error=ex)
        else:
            serialized = student.serialize()
            return APIResponse(data=serialized, code=200)

    def post(self, request, format=None):
        try:
            student = Students(**request.prepared)
            student.creator = request.session['name']
            student.save()
            return APIResponse(code=200, data={'id': student.id})
        except ValidationError as ex:
            return APIResponse(code=400, error=ex)

    def put(self, request, format=None):
        data = request.prepared
        qs = Students.active.filter(pk=data['id'])
        del data['id']

        try:
            count = Students.update(qs, **data)
        except ValidationError as ex:
            return APIResponse(code=400, error=ex)
        else:
            if count > 0:
                return APIResponse(code=200)
            else:
                return APIResponse(code=404)


class StudentsAPI(SmartAPIView):

    def get(self, request, format=None):
        students = Students.get_all(serializer='search')
        return APIResponse(data=students.values(), code=200)


class TeacherAPI(SmartAPIView):

    rules = {
        'GET': {
            'id': (Required, NotEmpty(), Coerce(int)),
        },
        'POST': {
            'lastname': (Required, NotEmpty(), Coerce(unicode)),
            'firstname': (Required, NotEmpty(), Coerce(unicode)),
            'middlename': (Required, NotEmpty(), Coerce(unicode)),
            'phone': (Coerce(str, if_none='')),
            'mail': (Coerce(str, if_none='')),
            'birthday': (Coerce(datetime, if_blank=None)),
            'comment': (Coerce(unicode, if_none='')),
        },
        'PUT': {
            'id': (Required, NotEmpty(), Coerce(int)),
            'lastname': (NotEmpty(), Coerce(unicode)),
            'firstname': (NotEmpty(), Coerce(unicode)),
            'middlename': (NotEmpty(), Coerce(unicode)),
            'phone': (Coerce(str, if_none='')),
            'mail': (Coerce(str, if_none='')),
            'birthday': (Coerce(datetime, if_blank=None)),
            'comment': (Coerce(unicode, if_none='')),
        },
    }

    def get(self, request, format=None):
        id = request.prepared['id']

        try:
            teacher = Teachers.active.get(pk=id)
        except Teachers.DoesNotExist as ex:
            return APIResponse(code=404, error=ex)
        else:
            serialized = teacher.serialize()
            return APIResponse(data=serialized, code=200)

    def post(self, request, format=None):
        try:
            teacher = Teachers(**request.prepared)
            teacher.creator = request.session['name']
            teacher.save()
            return APIResponse(code=200, data={'id': teacher.id})
        except ValidationError as ex:
            return APIResponse(code=400, error=ex)

    def put(self, request, format=None):
        data = request.prepared
        qs = Teachers.active.filter(pk=data['id'])
        del data['id']

        try:
            count = Teachers.update(qs, **data)
        except ValidationError as ex:
            return APIResponse(code=400, error=ex)
        else:
            if count > 0:
                return APIResponse(code=200)
            else:
                return APIResponse(code=404)


class TeacherLessonsAPI(SmartAPIView):

    rules = {
        'GET': {
            'teacher_id': (Required, NotEmpty(), Coerce(int)),
            'year': (Required, NotEmpty(), Coerce(int), Range(1000, 3000)),
            'month': (Required, NotEmpty(), Coerce(int), Range(0, 11)),
        },
    }

    def get(self, request, format=None):
        teacher_id = request.prepared['teacher_id']
        year = request.prepared['year']
        month = request.prepared['month'] + 1

        lessons = Lessons.active.filter(teacher=teacher_id,
                                        date__year=year,
                                        date__month=month)
        lessons = lessons.serialize('basic', extra_fields=['logbook_id'])
        Visits.get_reverse_related(lessons, 'lesson_id', 'default', many=True, extra_fields=['student_id'])
        visits = [x for y in lessons for x in y['visits']]
        Visits.get_related(visits, related={'student': 'basic'}, many=True)
        return APIResponse(data=lessons, code=200)


class SubscriptionAPI(SmartAPIView):

    rules = {
        'POST': {
            'student_id': (Required, NotEmpty(), Coerce(int)),
            'subtype': (Required, NotEmpty(), Coerce(int)),
        },
        'DELETE': {
            'id': (Required, NotEmpty(), Coerce(int)),
        },
        'PUT': {
            'id': (Required, NotEmpty(), Coerce(int)),
            'date_start': (Coerce(datetime, if_blank=None)),
            'date_end': (Coerce(datetime, if_blank=None)),
            'changes_left': (Coerce(int, 0, 0)),
            'status': (Coerce(str, if_none=''), In(['a', 'f'])),
        },
    }

    def post(self, request, format=None):
        data = request.prepared
        subtype = SubTypes.get(data['subtype'])
        if subtype is not None:
            try:
                datenow = datetime.now()

                sub = Subscriptions()
                sub.student_id = data['student_id']
                sub.mode = subtype['mode']
                sub.lessons_total = subtype['lessons']
                sub.date_start = datenow
                sub.date_end = datenow + relativedelta(months=subtype['months'])
                sub.changes_left = subtype['changes']
                sub.creator = request.session['name']
                sub.save()
                return APIResponse(code=200, data=sub.serialize())
            except ValidationError as ex:
                return APIResponse(code=400, error=ex)
        else:
            return APIResponse(code=404)

    def put(self, request, format=None):
        data = request.prepared
        qs = Subscriptions.active.filter(pk=data['id'])
        del data['id']
        if 'status' in data:
            data['status_date'] = timezone.now()

        try:
            count = Subscriptions.update(qs, **data)
        except ValidationError as ex:
            return APIResponse(code=400, error=ex)
        else:
            if count > 0:
                return APIResponse(code=200)
            else:
                return APIResponse(code=404)

    def delete(self, request, format=None):
        id = request.prepared['id']
        Subscriptions.objects.filter(pk=id).update(status='d', status_date=timezone.now())
        return APIResponse(code=200)
