import Dispatcher from "dispatcher/Dispatcher"
import {PeopleConstants} from "Constants.jsx"
import {API} from "api.js"


var PeopleActions = {
    student: {
        create: function(data) {
            var promise = API.student.create(data);
            promise.done(this._createSuccess.bind(this, data));
            promise.fail(this._createFail);
            return promise;
        },
        update: function(data) {
            var promise = API.student.update(data);
            promise.done(this._createSuccess.bind(this, data));
            promise.fail(this._createFail);
            return promise;
        },
        _createSuccess: function(data, response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.STUDENT_CREATE_SUCCESS,
                data: data,
                response: response,
            });
        },
        _createFail: function(response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.STUDENT_CREATE_FAIL,
                response: response,
            });
        },
    },

    teacher: {
        create: function(data) {
            var promise = API.teacher.create(data);
            promise.done(this._createSuccess.bind(this, data));
            promise.fail(this._createFail);
            return promise;
        },
        update: function(data) {
            var promise = API.teacher.update(data);
            promise.done(this._createSuccess.bind(this, data));
            promise.fail(this._createFail);
            return promise;
        },
        _createSuccess: function(data, response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.TEACHER_CREATE_SUCCESS,
                data: data,
                response: response,
            });
        },
        _createFail: function(response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.TEACHER_CREATE_FAIL,
                response: response,
            });
        },

        lessons: function(data) {
            var promise = API.teacher.lessons(data);
            promise.done(this._lessonsSuccess.bind(this, data));
            promise.fail(this._lessonsFail);
            return promise;
        },
        _lessonsSuccess: function(data, response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.TEACHER_LESSONS_GET_SUCCESS,
                data: data,
                response: response,
            });
        },
        _lessonsFail: function(response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.TEACHER_LESSONS_GET_FAIL,
                response: response,
            });
        },
    },

    subscription: {
        add: function(data) {
            var promise = API.subscription.create(data);
            promise.done(this._addSuccess.bind(this, data));
            promise.fail(this._addFail);
            return promise;
        },
        _addSuccess: function(data, response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.SUBSCRIPTION_ADD_SUCCESS,
                data: data,
                response: response,
            });
        },
        _addFail: function(response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.SUBSCRIPTION_ADD_FAIL,
                response: response,
            });
        },

        update: function(data) {
            var promise = API.subscription.update(data);
            promise.done(this._updateSuccess.bind(this, data));
            promise.fail(this._updateFail);
            return promise;
        },
        _updateSuccess: function(data, response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.SUBSCRIPTION_UPDATE_SUCCESS,
                data: data,
                response: response,
            });
        },
        _updateFail: function(response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.SUBSCRIPTION_UPDATE_FAIL,
                response: response,
            });
        },

        delete: function(id) {
            var data = {id: id};
            var promise = API.subscription.delete(data);
            promise.done(this._deleteSuccess.bind(this, data));
            promise.fail(this._deleteFail);
            return promise;
        },
        _deleteSuccess: function(data, response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.SUBSCRIPTION_DELETE_SUCCESS,
                data: data,
                response: response,
            });
        },
        _deleteFail: function(response) {
            Dispatcher.dispatch({
                actionType: PeopleConstants.SUBSCRIPTION_DELETE_FAIL,
                response: response,
            });
        },

        freeze: function(id) {
            return this.update({id: id, status: 'f'})
        },

        unfreeze: function(id) {
            return this.update({id: id, status: 'a'})
        },
    },
};


export default PeopleActions