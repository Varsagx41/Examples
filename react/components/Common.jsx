import React from 'react'
import autoBind from 'react-autobind'
import PropTypes from 'prop-types'
import ModalActions from 'actions/ModalActions'
import {RootStore} from 'stores/RootStore'
import {Submit} from 'components/Inputs'
import MicroEvent from "microevent"
import Validate from 'validation.js'



class TabButton extends React.PureComponent {

    constructor(props) {
        super(props)
        autoBind(this)
    }

    handleClick() {
        TabsStore.trigger("change-tab", this.props.name);
    }
    render() {
        return (
            <li
                className={"tab" + (this.props.active ? " active" : "")}
                onClick={this.handleClick}
            >{this.props.children}</li>
        );
    }
};

class TabButtons extends React.PureComponent {
    static propTypes = {
        tabs: PropTypes.arrayOf(
            PropTypes.shape({
                name: PropTypes.oneOfType([
                    PropTypes.string,
                    PropTypes.number,
                ]).isRequired,
                title: PropTypes.string.isRequired,
            })
        ).isRequired,
        tabsClass: PropTypes.string,
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    render() {
        var tabs = [];
        var {value} = this.props;
        this.props.tabs.map(function(tab){
            tabs.push(<TabButton name={tab.name} key={tab.name}
                           active={value == tab.name ? true : false}>
                      {tab.title}</TabButton>);
        });

        return (
            <ul className={this.props.tabsClass}>
                {tabs}
            </ul>
        );
    }
};

class Tabs extends React.PureComponent {
    static propTypes = {
        tabs: PropTypes.arrayOf(
            PropTypes.shape({
                name: PropTypes.oneOfType([
                    PropTypes.string,
                    PropTypes.number,
                ]).isRequired,
                title: PropTypes.string.isRequired,
                node: PropTypes.node.isRequired,
            })
        ).isRequired,
        defaultTab: PropTypes.oneOfType([
            PropTypes.string,
            PropTypes.number,
        ]),
        tabsClass: PropTypes.string,
    }
    state = this.getInitialState()
    getInitialState() {
        const tab = this.props.defaultTab === undefined ? this.props.tabs[0].name : this.props.defaultTab
        return {
            tab: tab,
            node: this.getNode(tab),
            loading: false,
            error: false,
        }
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    changeTab(tab) {
        this.setState({
            tab: tab,
            node: this.getNode(tab),
            error: false,
        });
    }
    getNode(tab) {
        var len = this.props.tabs.length;
        for(var i=0; i<len; i++)
            if(tab === this.props.tabs[i].name)
                return this.props.tabs[i].node;
        return undefined;
    }
    changeLoading(flag) {
        this.setState({loading: flag});
    }
    changeError(tab) {
        if(tab == this.state.tab)
            this.setState({error: true, loading: false});
    }
    componentWillMount() {
        TabsStore.bind('change-tab', this.changeTab);
        TabsStore.bind('loading', this.changeLoading);
        TabsStore.bind('error', this.changeError);
    }
    componentWillUnmount() {
        TabsStore.unbind('change-tab', this.changeTab);
        TabsStore.unbind('loading', this.changeLoading);
        TabsStore.unbind('error', this.changeError);
    }
    render() {
        return (
            <div>
                <TabButtons value={this.state.tab} tabs={this.props.tabs} tabsClass={this.props.tabsClass} />
                {this.state.node}
            </div>
        );
    }
};


class Collapse extends React.PureComponent {

    constructor(props) {
        super(props)
        autoBind(this)
    }

    handleOpen() {
        $(this.bodyElement).slideToggle(350);
    }
    render() {
        var {headerClass, children} = this.props;
        var header = children[0];
        var body = children[1];

        return (
            <div className="collapse-wrapper">
                <div className={headerClass} onClick={this.handleOpen}>
                    {header}
                </div>

                <div className="callout small" ref={(el) => { this.bodyElement = el; }}>
                    {body}
                </div>
            </div>
        );
    }
};

class DatePicker extends React.PureComponent {
    static defaultProps = {
        options: {},
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    componentDidMount() {
        var {options, value} = this.props;
        var datepicker = $(this.element).datepicker(options).data('datepicker')

        if (value) {
            datepicker.selectDate(this.props.value)
            datepicker.date = this.props.value
        }
    }
    render() {
        var { name, label, error, wrapperClass, onlyInput, options, value, ...other } = this.props;
        var input = <input type="text" className={!!error ? 'error' : undefined} id={"id_" + name} name={name}
                ref={(el) => this.element = el} {...other} />

        if (onlyInput)
            return input;
        else
            return (
                <div className={!!wrapperClass ? wrapperClass : "field"}>
                    {label && <label htmlFor={"id_" + name}>{label}</label>}
                    {input}
                    {!!error ? <div className="input-error">{error}</div> : undefined}
                </div>
            );
    }
};


const SubmitForm = WrappedComponent => class SubmitForm extends React.PureComponent {
    // static options = {
    //     create: {
    //         action: ScheduleActions.routines.create.bind(ScheduleActions.routines),
    //         btnText: 'Создать занятие',
    //     },
    //     update: {
    //         action: ScheduleActions.routines.update.bind(ScheduleActions.routines),
    //         btnText: 'Сохранить',
    //     },
    //     validators: {},
    //     transforms: {
    //         weekday: weekday => weekday + 100,
    //         __all__: data => data.comment = `${data.time_start} _-_ ${data.time_end}`,
    //     },
    // }
    // finalizeData(data) {
    //     data.student_id = this.props.student_id
    //     return data
    // }

    state = this.getInitialState()
    getInitialState() {
        var options = WrappedComponent.options
        if (!options.create) options.create = {}
        if (!options.update) options.update = {}

        var data = this.props.data || {}
        var mode = data.id ? 'update': 'create'

        return {
            data: data,
            errors: {},
            mode: mode,
            options: options,
        };
    }

    constructor(props) {
        super(props)
        autoBind(this)
    }

    transform(data, transforms) {
        for (var field in data)
            if (transforms[field])
                data[field] = transforms[field](data[field])

        if (transforms.__all__)
            transforms.__all__(data)

        return data
    }
    handleSubmit(event) {
        event.preventDefault()
        var {options} = this.state
        var {validators, transforms} = options
        var createAction = options.create.action
        var updateAction = options.update.action
        var data = $(this.formEl).serializeObject()
        var result = Validate(data, validators)

        if(result.status) {
            this.setState({errors: {}})
            if (transforms) data = this.transform(data, transforms)
            if (this.wrappedEl.finalizeData) data = this.wrappedEl.finalizeData(data)
            
            if (this.state.mode == 'update') {
                if (this.state.data.id)
                    data.id = this.state.data.id
                updateAction(data)
            }
            else {
                createAction(data)
            }
        }
        else {
            this.setState({errors: result.errors})
        }
    }
    render() {
        var {options, mode} = this.state

        return (
            <form ref={(form) => this.formEl = form} acceptCharset="UTF-8" noValidate onSubmit={this.handleSubmit}>
                <WrappedComponent ref={(el) => this.wrappedEl = el} {...this.props} />
                <div className="row">
                    <fieldset className="small-12">
                        <Submit className="button expanded">{mode == 'create' ? options.create.btnText : options.update.btnText}</Submit>
                    </fieldset>
                </div>
            </form>
        );
    }
};

export {
    Tabs,
    Collapse,
    DatePicker,
    SubmitForm,
}