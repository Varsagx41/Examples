import Update from 'immutability-helper'
import Dispatcher from "../dispatcher/Dispatcher"
import MicroEvent from "microevent"
import {PeopleConstants, LogbookConstants} from "../Constants.jsx"
import Moment from "moment"


var PeopleStore = {
    student: {},
    teacher: {},
    subs: [],
    teacherLogbooks: [],
    teacherLessons: {},

    deleteSub: function(id) {
        var index = undefined
        for (var key in this.subs) {
            if (this.subs[key].id == id) {
                index = key
                break;
            }
        }

        if(index)
            this.subs = Update(this.subs, {$splice: [[index, 1]]});
    },

    addSub: function(sub) {
        if (!sub.visits) sub.visits = [];
        if (!sub.records) sub.records = [];
        this.subs = Update(this.subs, {$push: [sub]});
    },

    updateSub: function(data) {
        var index = undefined;
        for (var key in this.subs) {
            if (this.subs[key].id === data.id) {
                index = key
                break
            }
        }

        if (index) {
            this.subs = Update(this.subs, {[index]: {$merge: data}});
        }
    },

    teacherLessonsSort: function(lessons) {
        lessons.sort(function(a, b) {
            if (a.date === b.date)
                return a.time_start > b.time_start;
            else
                return a.date - b.date;
        });
        return lessons;
    },
}

MicroEvent.mixin(PeopleStore);

Dispatcher.register(function(payload){

    switch(payload.actionType) {
        case PeopleConstants.STUDENT_CREATE_SUCCESS:
            var student = payload.data;
            if (payload.response.data)
                student = $.extend(payload.data, payload.response.data);

            PeopleStore.student = Update(PeopleStore.student, {$merge: student});
            PeopleStore.trigger("student-create-success", student, payload.response);
            break;
        case PeopleConstants.STUDENT_CREATE_FAIL:
            PeopleStore.trigger("student-create-fail", payload.response);
            break;

        case PeopleConstants.TEACHER_CREATE_SUCCESS:
            var teacher = payload.data;
            if (payload.response.data)
                teacher = $.extend(payload.data, payload.response.data);

            PeopleStore.teacher = Update(PeopleStore.teacher, {$merge: teacher});
            PeopleStore.trigger("teacher-create-success", teacher, payload.response);
            break;
        case PeopleConstants.TEACHER_CREATE_FAIL:
            PeopleStore.trigger("teacher-create-fail", payload.response);
            break;
        case PeopleConstants.TEACHER_LESSONS_GET_SUCCESS:
            if (!PeopleStore.teacherLessons[payload.data.year])
                PeopleStore.teacherLessons[payload.data.year] = {};

            var lessons = PeopleStore.teacherLessonsSort(payload.response.data);
            PeopleStore.teacherLessons[payload.data.year][payload.data.month] = lessons;
            PeopleStore.trigger("teacher-lessons-get-success", payload.data, payload.response);
            break;
        case PeopleConstants.TEACHER_LESSONS_GET_FAIL:
            PeopleStore.trigger("teacher-lessons-get-fail", payload.response);
            break;

        case PeopleConstants.SUBSCRIPTION_ADD_SUCCESS:
            PeopleStore.addSub(payload.response.data);
            PeopleStore.trigger("subscription-add-success", payload.data, payload.response);
            break;
        case PeopleConstants.SUBSCRIPTION_ADD_FAIL:
            PeopleStore.trigger("subscription-add-fail", payload.response);
            break;

        case PeopleConstants.SUBSCRIPTION_UPDATE_SUCCESS:
            PeopleStore.updateSub(payload.data);
            PeopleStore.trigger("subscription-update-success", payload.data, payload.response);
            break;
        case PeopleConstants.SUBSCRIPTION_UPDATE_FAIL:
            PeopleStore.trigger("subscription-update-fail", payload.response);
            break;

        case PeopleConstants.SUBSCRIPTION_DELETE_SUCCESS:
            PeopleStore.deleteSub(payload.data.id);
            PeopleStore.trigger("subscription-delete-success", payload.data, payload.response);
            break;
        case PeopleConstants.SUBSCRIPTION_DELETE_FAIL:
            PeopleStore.trigger("subscription-delete-fail", payload.response);
            break;

        case LogbookConstants.LOGBOOK_CREATE_SUCCESS:
            PeopleStore.teacherLogbooks = Update(PeopleStore.teacherLogbooks, {$push: [payload.response.data]});
            PeopleStore.trigger("logbook-create-success", payload.data, payload.response);
            break;
        case LogbookConstants.LOGBOOK_CREATE_FAIL:
            PeopleStore.trigger("logbook-create-fail", payload.response);
            break;

        case LogbookConstants.VISIT_UNMARK_SUCCESS:
            PeopleStore.trigger("visit-unmark-success", payload.data, payload.response);
            break;
        case LogbookConstants.VISIT_UNMARK_FAIL:
            PeopleStore.trigger("visit-unmark-fail", payload.response);
            break;
    }

    return true;
});


export { PeopleStore }
