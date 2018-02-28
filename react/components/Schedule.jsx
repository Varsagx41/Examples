import React from 'react'
import autoBind from 'react-autobind'
import {ModalContainer, ModalDialog, Tabs, SubmitForm, DatePicker} from 'components/Common'
import {Input, Textarea, Submit, Choice, Select, Loading} from 'components/Inputs'
import {Fade} from 'components/Animation'
import {ScheduleStore} from 'stores/ScheduleStore'
import ScheduleActions from 'actions/ScheduleActions'
import ModalActions from 'actions/ModalActions'
import {PageData, URLS} from 'api.js'
import Validate from 'validation.js'
import Report from 'report'
import Moment from 'moment'
import Plurals from 'smart-plurals'


const Plur = Plurals.Plurals.getRule('ru')

function minutesToString(minutes) {
    return Moment.unix(minutes*60).utc().format('HH:mm')
}

function stringToMinutes(text) {
    var date = Moment(text, 'HH:mm')
    return date.hours()*60 + date.minutes()
}

function stringToDate(text) {
    return Moment(text, 'HH:mm').toDate()
}

function minutesToDate(minutes) {
    return stringToDate(minutesToString(minutes))
}

@SubmitForm
class RoutineCreateForm extends React.PureComponent {
    store = ScheduleStore;
    static options = {
        create: {
            action: ScheduleActions.routines.create.bind(ScheduleActions.routines),
            btnText: 'Создать занятие',
        },
        update: {
            action: ScheduleActions.routines.update.bind(ScheduleActions.routines),
            btnText: 'Сохранить',
        },
        validators: {
            comment: {
                optional: undefined,
            },
            time_start: {
                required: {error: "Это обязательное поле"},
                regex: {error: "Неправильный формат времени", args: [/^\d{2}:\d{2}$/]},
            },
            time_end: {
                required: {error: "Это обязательное поле"},
                regex: {error: "Неправильный формат времени", args: [/^\d{2}:\d{2}$/]},
            },
            __all__: function(data, errors) {
                var time_start = stringToMinutes(data.time_start)
                var time_end = stringToMinutes(data.time_end)
                if (time_start == time_end)
                    errors.time_start = 'Вневременное занятие?'
                else if (time_end < time_start)
                    errors.time_start = 'Временной парадокс'
                else if (time_end - time_start <= 15)
                    errors.time_start = 'Слишком быстротечное занятие'
            },
        },
    }
    weekdays = [
        {label: 'Понедельник', value: 0},
        {label: 'Вторник', value: 1},
        {label: 'Среда', value: 2},
        {label: 'Четверг', value: 3},
        {label: 'Пятница', value: 4},
        {label: 'Суббота', value: 5},
        {label: 'Воскресенье', value: 6},
    ]
    halls = [
        {label: 'Синий', value: 'blue'},
        {label: 'Зеленый', value: 'green'},
        {label: 'Пилонный', value: 'pylon'},
        {label: 'Оранжевый', value: 'orange'},
        {label: 'Суперновый', value: 'supernova'},
        {label: 'Большой', value: 'big'},
        {label: 'Домик', value: 'house'},
    ]
    types = {
        'Тип': [
            {value: 'common', label: 'Обычный', input_attr: {className: 'radio-button'}},
            {value: 'mini', label: 'Мини', input_attr: {className: 'radio-button'}},
            {value: 'lease', label: 'Аренда', input_attr: {className: 'radio-button'}},
            {value: 'repetition', label: 'Репетиция', input_attr: {className: 'radio-button'}},
        ]
    };

    static defaultProps = {
        data: {},
        errors: {},
        logbooks: {},
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    getLogbookChoices(logbooks) {
        var choices = []
        for (var id in logbooks) {
            var logbook = logbooks[id]
            var title = `${logbook.course} - ${logbook.teacher.lastname}`
            title += logbook.info ? ` - ${logbook.info}` : ''
            choices.push({label: title, value: id})
        }
        return choices;
    }
    render() {
        var {data, errors, logbooks} = this.props
        const dateOptions = {
            dateFormat: ' ',
            timepicker: true,
            minutesStep: 5,
            classes: 'only-timepicker',
            onSelect(fd, data, obj) {
                obj.el.value = obj.el.value.trim()
            },
        }

        return (
            <div className="row">
                <Select wrapperClass="small-12" name="weekday" value={data.weekday} label="День недели" items={this.weekdays} />
                <Select wrapperClass="small-12" name="hall" value={data.hall} label="Зал" items={this.halls} />
                <div className="small-12 time-select">
                    <label>Время</label> 
                    <DatePicker onlyInput={true} className="time-input" options={dateOptions} name="time_start" label="Время" error={errors.time_start} value={data.time_start} />
                    <div><div className="icon-minus"></div></div>
                    <DatePicker onlyInput={true} className="time-input-second" options={dateOptions} name="time_end" error={errors.time_end} value={data.time_end} />
                    {errors.time_start || errors.time_end ? <div className="input-error">{errors.time_start || errors.time_end}</div> : undefined}
                </div>
                <div className="small-12">
                    <Choice name="type" value={data.type || 'common'} label="Тип" items={this.types} className="radio-group-type" error={errors.type} />
                </div>
                <Select wrapperClass="small-12" name="logbook_id" value={data.logbook_id} label="Ведомость" items={this.getLogbookChoices(logbooks)} />
                <Textarea wrapperClass="small-12" name="comment" rows="5" label="Комментарий" maxLength="255" error={errors.comment} value={data.comment} />
            </div>
        );
    }
};


class Lesson extends React.PureComponent {
    store = ScheduleStore;
    clicks = 0;
    timer = undefined;
    DELAY = 200;

    static defaultProps = {
        logbook: {teacher: {}},
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    componentDidMount() {
        this.controlClicks()
    }

    controlClicks() {
        var that = this;
        $(this.element).on('contextmenu', function(){
            return false;
        });
        $(this.element).mouseup(function(e) {
            if(e.target == that.crossElement)
                return;
            if (e.button == 0)
            {
                that.clicks++;
                if (that.clicks == 1)
                {
                    that.timer = setTimeout(function() {
                        console.log('CLICK')
                        that.clicks = 0;

                    }.bind(that), that.DELAY);
                }
                else
                {
                    clearTimeout(that.timer);
                    that.clicks = 0;
                    console.log('DOUBLE CLICK')
                }
            }
            if(e.button == 2)
            {
                console.log('RIGHT CLICK')
            }
        });
    }

    handleDelete(event) {
        event.stopPropagation()

        var buttons = {
            'Удалить': () => {
                ScheduleActions.routines.delete(this.props.data.id)
            },
            'Отменить': undefined,
        }
        ModalActions.show(
            <ModalDialog header="Удалить занятие"
                         message="Вы уверены, что хотите удалить занятие?"
                         posClass="large-5 medium-8 small-10"
                         buttons={buttons} />
        )
    }

    render() {
        var {data, logbook, rows, booking} = this.props

        return (
            <td className={`lesson ${logbook.level}-level`} rowSpan={rows} ref={(div) => this.element = div}>
                <div className="icon-cancel" onClick={this.handleDelete} ref={(cross) => this.crossElement = cross}></div>
                {booking !== undefined && <div className="booking">{booking}</div>}
                <div>
                    <div className="style">{logbook.course || 'Unknown'}</div>
                    {rows > 1 && <div className="teacher">{`(${logbook.teacher.lastname})` || '(Unknown)'}</div>}
                    {rows > 1 && <div className="time">{`${data.time_start}-${data.time_end}`}</div>}
                </div>
            </td>
        );
    }
};


class Schedule extends React.PureComponent{
    store = ScheduleStore;
    static defaultProps = {
        openTime: '00:00',
        closeTime: '23:59',
        interval: 60,
        logbooks: {},
    }
    state = {
        data: undefined,
        schedule: undefined,
        weekday: this.props.weekday,
        loading: false,
        error: false,
    }
    halls = {
        blue: 'Синий',
        green: 'Зеленый',
        pylon: 'Пилонный',
        orange: 'Оранжевый',
        supernova: 'Суперновый',
        big: 'Большой',
        house: 'Домик',
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    componentWillMount() {
        this.store.bind('routines-get-success', this.getScheduleSuccess)
        this.store.bind('routines-get-fail', this.getScheduleFail)
        this.store.bind('routine-create-success', this.fullUpdate)
        this.store.bind('routine-create-fail', this.createLessonFail)
        this.store.bind('routine-delete-success', this.fullUpdate)
        this.store.bind('routine-delete-fail', this.createLessonFail)
    }
    componentWillUnmount() {
        this.store.unbind('routines-get-success', this.getScheduleSuccess)
        this.store.unbind('routines-get-fail', this.getScheduleFail)
        this.store.unbind('routine-create-success', this.fullUpdate)
        this.store.unbind('routine-create-fail', this.createLessonFail)
        this.store.unbind('routine-delete-success', this.fullUpdate)
        this.store.unbind('routine-delete-fail', this.createLessonFail)
    }
    componentDidMount() {
        var {weekday} = this.state

        var storeData = this.store.routines[weekday]
        if (storeData) {
            this.fullUpdate()
        }
        else {
            this.setState({loading: true, error: false})
            var promise = ScheduleActions.routines.get(weekday)
        }
    }

    fullUpdate() {
        var schedule = this.initSchedule()
        var data = this.store.routines[this.state.weekday]
        for (var key in data)
            this.addLesson(data[key], schedule)

        this.setState({
            data: data,
            schedule: schedule,
            loading: false,
            error: false,
        });
    }
    getScheduleSuccess(data) {
        if (data.weekday == this.state.weekday) {
            this.fullUpdate()
        }
    }
    getScheduleFail() {
        this.setState({
            loading: false,
            error: true,
        })
    }
    createLessonFail() {
        Report.red('Что-то пошло не так...')
    }

    initSchedule() {
        var {weekday, openTime, closeTime, interval} = this.props
        openTime = stringToMinutes(openTime)
        closeTime = stringToMinutes(closeTime)

        var schedule = {}
        for(var hall in this.halls) {
            schedule[hall] = {}
            var current = openTime
            while (current <= closeTime) {
                schedule[hall][current] = <td key={hall + current} onDoubleClick={this.handleCreate.bind(this, hall, minutesToDate(current), minutesToDate(current + 60))} />
                current += interval
            }
            if (current - interval < closeTime)
                schedule[hall][closeTime] = <td key={hall + closeTime} onDoubleClick={this.handleCreate.bind(this, hall, minutesToDate(current - interval), minutesToDate(closeTime))} />
        }

        return schedule
    }
    findNearestTime(time, times, interval) {
        for (var i = 0; i < times.length; i++) {
            if (times[i] == time)
                return times[i]

            if (times[i] > time) {
                if (times[i] - time > interval / 2)
                    return times[i - 1]
                else
                    return times[i]
            }
        }
    }
    addLesson(lesson, local_schedule) {
        var schedule = local_schedule || this.state.schedule
        var {interval, logbooks} = this.props
        var time_start = stringToMinutes(lesson.time_start)
        var time_end = stringToMinutes(lesson.time_end)
        var logbook = logbooks[lesson.logbook_id] || {teacher: {}}
        var column = schedule[lesson.hall]

        var times = Object.keys(column).sort((a,b) => a - b)
        var row_start = this.findNearestTime(time_start, times, interval)
        var row_end = this.findNearestTime(time_end, times, interval)

        if (row_start && row_end) {
            var rows = times.indexOf(row_end) - times.indexOf(row_start)
            if (rows > 0) {
                var el = <Lesson data={lesson} logbook={logbook} rows={rows} key={'les'+lesson.id} />
                column[row_start] = el
                var ind = times.indexOf(row_start)
                for (var i = 1; i < rows; i++) {
                    var key = times[ind + i]
                    if (key)
                        column[key] = undefined
                }

            }          
        }
    }
    handleCreate(hall, time_start, time_end) {
        var data = {
            weekday: this.props.weekday,
            hall: hall,
            time_start: time_start,
            time_end: time_end,
        }

        const modalModes = {
            store: this.store,
            success: {
                events: ['routine-create-success', 'routine-update-success'],
            },
            fail: {
                events: ['routine-create-fail', 'routine-update-fail'],
            },
        }

        ModalActions.show(
            <ModalContainer header="Новое занятие" posClass="large-5 medium-8 small-10" modes={modalModes}>
                <RoutineCreateForm data={data} logbooks={this.props.logbooks} />
            </ModalContainer>
        );
    }

    render() {
        var {schedule, loading, error} = this.state
        var halls = this.halls

        if (schedule) {
            var body = []
            for (var time in schedule[Object.keys(schedule)[0]]) {
                var row = [<td key={"time" + time}>{minutesToString(time)}</td>]
                for (var hall in schedule) {
                    var column = schedule[hall]
                    row.push(schedule[hall][time])
                }
                body.push(
                    <tr key={"row" + time}>
                        {row}
                    </tr>
                )
            }

            var table = (
                <table className="schedule">
                    <colgroup>
                        <col width="65px" />
                        <col width="1*" />
                        <col width="1*" />
                        <col width="1*" />
                        <col width="1*" />
                        <col width="1*" />
                        <col width="1*" />
                        <col width="1*" />
                    </colgroup>

                    <tbody>
                        <tr>
                            <th></th>
                            {Object.keys(halls).map(function(name) {
                                return <th key={"clm_"+name}>{halls[name]}</th>
                            })}
                        </tr>
                        {body}
                    </tbody>
                </table>
            );
        }

        return (
            <div className="small-12 columns">
                {!loading && !error && table}
                {loading && <div className='loading-area-large'><Loading /></div>}
                {error && <div className='loading-error'>Не удалось получить список занятий</div>}
            </div>
        );
    }
};


class RoutinesPage extends React.PureComponent {
    store = ScheduleStore;

    constructor(props) {
        super(props)
        autoBind(this)
    }

    assocLogbooks(logbooks, teachers) {
        for (var logbook_id in logbooks) {
            var logbook = logbooks[logbook_id]
            logbook.teacher = teachers[logbook.teacher_id]
        }
    }

    getTabs(openTime, closeTime, interval, logbooks) {
        const weekday = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        var tabs = []
        for(var i = 0; i < 7; i++) {
            tabs.push({name: i, title: weekday[i], node: <Schedule weekday={i} openTime={openTime} closeTime={closeTime} interval={interval} logbooks={logbooks} key={'sch'+i} />})
        }
        return tabs
    }

    render() {
        var teachers = PageData.content('teachers')
        var logbooks = PageData.content('logbooks')
        this.assocLogbooks(logbooks, teachers)
        var tabs = this.getTabs('09:00', '21:00', 30, logbooks)
        var weekday = Moment().weekday()

        return (
            <div className="row">
                <Tabs tabs={tabs} defaultTab={weekday} tabsClass="schedule-days small-12 columns" />
            </div>
        );
    }
};


export {
    RoutinesPage,
}