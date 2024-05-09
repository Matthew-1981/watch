import React, {useEffect, useState} from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import Modal from 'react-bootstrap/Modal';
import {BACKEND_URL} from './settings';
import axios from "axios";

export default function App() {
    let [global_watch, set_global_watch] = useState(null)
    let [global_cycle, set_global_cycle] = useState(null)

    let global_state = {
        global_watch: global_watch,
        set_global_watch: set_global_watch,
        global_cycle: global_cycle,
        set_global_cycle: set_global_cycle
    }

    return (
        <div>
            <TopLine global_state={global_state}/>
            <div style={{padding: '10px'}}>
                {<Content global_state={global_state}/>}
            </div>
        </div>
    )
}

// ========================================

function TopLine({global_state}) {

    const tmp = (global_state.global_watch ? (<CycleSelectList global_state={global_state} />) : (<div></div>))

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <a className="navbar-brand" href="#">Watch tracking</a>
            <WatchSelectList global_state={global_state} />
            {tmp}
        </nav>
    )
}

function WatchSelectList({global_state}) {
    const [data, setData] = useState([]);
    const [showAddWatchMenu, setShowAddWatchMenu] = useState(false);

    useEffect(() => {
        axios.get(BACKEND_URL + '/watchlist')
            .then(response => {
                setData(response.data);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [showAddWatchMenu]);

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <Dropdown>
                <Dropdown.Toggle variant="success" id="dropdown-basic">
                    {global_state.global_watch ? global_state.global_watch.name : "Select a watch"}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                    {data.map(item => (
                        <WatchSelector watch={item}
                                       global_state={global_state} />
                    ))}
                    <Dropdown.Divider/>
                    <Dropdown.Item onClick={() => setShowAddWatchMenu(true)}>
                        Add new watch
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
            {showAddWatchMenu && <AddWatchMenu global_state={global_state}
                                               showAddWatchMenu={showAddWatchMenu}
                                               setShowAddWatchMenu={setShowAddWatchMenu}/>}
        </nav>
    );
}

function AddWatchMenu({global_state, showAddWatchMenu, setShowAddWatchMenu}) {

    const addWatch = ({watch_name}) => {
        axios.post(BACKEND_URL + '/watchlist', {name: watch_name})
            .then()
            .catch(error => {
                console.error('Error creating data:', error);
            })
    }

    return (
        <Modal show={showAddWatchMenu} onHide={() => setShowAddWatchMenu(false)}>
            <Modal.Header closeButton>
                <Modal.Title>Add Watch</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <input type="text" id="watch_name"/>
            </Modal.Body>
            <Modal.Footer>
                <button onClick={() => {
                    addWatch({watch_name: document.getElementById('watch_name').value})
                    setShowAddWatchMenu(false)
                }}>
                    Add watch
                </button>
            </Modal.Footer>
        </Modal>
    )
}

function WatchSelector({watch, global_state}) {
    const handleClick = () => {
        global_state.set_global_watch(watch)
        const max_cycle = (watch.cycles.length > 0 ? Math.max(...watch.cycles) : 0)
        global_state.set_global_cycle(max_cycle);
    }

    return (
        <Dropdown.Item onClick={handleClick}>
            {watch.name}
        </Dropdown.Item>
    );
}

function CycleSelectList({global_state}) {
    const [data, setData] = useState([]);

    useEffect(() => {
        let tmp = global_state.global_watch.cycles
        if (tmp.length === 0)
            tmp = [0]
        tmp.sort((a, b) => parseFloat(a) - parseFloat(b));
        setData(tmp)
    }, [global_state.global_watch, global_state.set_global_cycle])

    const onClickCreateNewCycle = () => {
        let new_cycle = 0
        if (data.length > 0)
            new_cycle = Math.max(...data) + 1
        global_state.set_global_cycle(new_cycle)
        global_state.global_watch.cycles.push(new_cycle)
    }

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light" style={{marginLeft: '15px'}}>
            <Dropdown>
                <Dropdown.Toggle variant="success" id="dropdown-basic">
                    {global_state.global_cycle !== null ? global_state.global_cycle : "Select cycle"}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                    {data.map(item => (
                        <CycleSelector cycle={item} global_state={global_state} />
                    ))}
                    <Dropdown.Divider/>
                    <Dropdown.Item onClick={onClickCreateNewCycle}>
                        Create new cycle
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </nav>
    );
}

function CycleSelector({cycle, global_state}) {
    const handleClick = () => {
        global_state.set_global_cycle(cycle)
    }

    return (
        <Dropdown.Item onClick={handleClick}>
            {cycle}
        </Dropdown.Item>
    );
}

// ========================================

function Content({global_state}) {

    if (!global_state.global_watch) {
        return (
            <div className="vh-100 d-flex justify-content-center align-items-center">
                <div className="display-4">Please select a watch</div>
            </div>
        );
    }

    return (
        <div>
            <div style={{overflow: 'auto', textAlign: 'left'}}>
                <table style={{width: '100%'}}>
                    <tbody>
                    <tr>
                        <td style={{width: '50%', paddingRight: '20px'}}>
                            <MeasurementList global_state={global_state} />
                        </td>
                        <td>
                            <div style={{width: '100px', height: '100px', backgroundColor: 'red'}}></div>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function MeasurementList({global_state}) {
    const [data, setData] = useState(null);

    useEffect(() => {
        axios.get(BACKEND_URL + '/measurements/' + global_state.global_watch.id + '/' + global_state.global_cycle)
            .then(response => {
                setData(response.data)
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [global_state.global_watch, global_state.global_cycle])

    const handleDelete = ({measurement_id}) => {
        axios.delete(BACKEND_URL + '/measurements/' + measurement_id)
            .then(response => {
                axios.get(BACKEND_URL + '/measurements/' + global_state.global_watch.id + '/' + global_state.global_cycle)
                    .then(response => {
                        setData(response.data)
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                    });
            })
            .catch(error => {
                console.error('Error deleting data:', error);
            });
    }

    const handleCreate = ({datetime, value}) => {
        const str_datetime = datetime.toISOString().slice(0, 19).replace('T', ' ')
        axios.post(BACKEND_URL + '/measurements/' + global_state.global_watch.id + '/' + global_state.global_cycle, {
            datetime: str_datetime,
            measure: parseFloat(value)
        })
            .then(response => {
                axios.get(BACKEND_URL + '/measurements/' + global_state.global_watch.id + '/' + global_state.global_cycle)
                    .then(response => {
                        setData(response.data)
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                    });
            })
            .catch(error => {
                console.error('Error creating data:', error);
            });
    }

    return (
        <div>
            <div style={{maxHeight: '80vh', overflow: 'auto'}}>
                <table className="table">
                    <thead>
                    <tr>
                        <th>Time Stamp</th>
                        <th>Measure</th>
                        <th>Delta</th>
                        <th></th>
                    </tr>
                    </thead>
                    <tbody>
                    {data && data.map((item, index) => (
                        <tr key={index}>
                            <td>{item.datetime}</td>
                            <td>{item.measure}</td>
                            <td>{item.difference}</td>
                            <td>
                                <button onClick={() => handleDelete({measurement_id: item.log_id})}>Delete</button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
            <table>
                <tbody>
                <tr>
                    <td>
                        <input type="number" id="value"/>
                    </td>
                    <td>
                        <button onClick={() => handleCreate({
                            datetime: new Date(),
                            value: document.getElementById('value').value
                        })}>Create
                        </button>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    );
}
