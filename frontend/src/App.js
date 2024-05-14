import React, {useEffect, useState} from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import Modal from 'react-bootstrap/Modal';
import axios from "axios";
import Plotly from 'plotly.js-dist';

import './App.css';

// settings
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

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
        <div style={{width: "100vw", height: "100vh"}}>
            <TopLine global_state={global_state}/>
            <div style={{padding: '15px'}}>
                {<Content global_state={global_state}/>}
            </div>
        </div>
    )
}

// ========================================

function TopLine({global_state}) {

    const tmp = (global_state.global_watch ? (<CycleSelectList global_state={global_state}/>) : (<div></div>))

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <a className="navbar-brand" href="#" style={{paddingLeft: "10px"}}>Watch tracking</a>
            <WatchSelectList global_state={global_state}/>
            {tmp}
        </nav>
    )
}

function WatchSelectList({global_state}) {
    const [data, setData] = useState([]);
    const [showAddWatchMenu, setShowAddWatchMenu] = useState(false);
    const [showDeleteWatchMenu, setShowDeleteWatchMenu] = useState(false);

    useEffect(() => {
        axios.get(BACKEND_URL + '/watchlist')
            .then(response => {
                setData(response.data);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [showAddWatchMenu, showDeleteWatchMenu]);

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <Dropdown>
                <Dropdown.Toggle variant="success" id="dropdown-basic">
                    {global_state.global_watch ? global_state.global_watch.name : "Select a watch"}
                </Dropdown.Toggle>

                <Dropdown.Menu style={{maxHeight: "40vh", overflowY: "auto"}}>
                    {data.map(item => (
                        <WatchSelector watch={item}
                                       global_state={global_state}/>
                    ))}
                    <Dropdown.Divider/>
                    <Dropdown.Item onClick={() => setShowAddWatchMenu(true)}>
                        Add new watch
                    </Dropdown.Item>
                    <Dropdown.Item onClick={() => setShowDeleteWatchMenu(true)}>
                        Delete watch
                    </Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
            {showAddWatchMenu && <AddWatchMenu global_state={global_state}
                                               showAddWatchMenu={showAddWatchMenu}
                                               setShowAddWatchMenu={setShowAddWatchMenu}/>}
            {showDeleteWatchMenu && <DeleteWatchMenu global_state={global_state}
                                                     watch_list={data}
                                                     showDeleteWatchMenu={showDeleteWatchMenu}
                                                     setShowDeleteWatchMenu={setShowDeleteWatchMenu}/>}
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
                <input type="text" id="watch_name" style={{width: "100%"}}/>
            </Modal.Body>
            <Modal.Footer>
                <button className="createButton" onClick={() => {
                    const to_be_added = document.getElementById('watch_name').value
                    if (to_be_added !== "") {
                        addWatch({watch_name: to_be_added})
                        setShowAddWatchMenu(false)
                    }
                }}>
                    Add watch
                </button>
            </Modal.Footer>
        </Modal>
    )
}

function DeleteWatchMenu({global_state, watch_list, showDeleteWatchMenu, setShowDeleteWatchMenu}) {

    const onClickDelete = (watch) => {
        axios.delete(BACKEND_URL + '/watchlist/' + watch.id)
            .then(
                () => {
                    if (global_state.global_watch && global_state.global_watch.id === watch.id) {
                        global_state.set_global_watch(null)
                        global_state.set_global_cycle(null)
                    }
                }
            )
            .catch(error => {
                console.error('Error deleting data:', error);
            })
    }

    return (
        <Modal show={showDeleteWatchMenu} onHide={() => setShowDeleteWatchMenu(false)}>
            <Modal.Header closeButton>
                <Modal.Title>Delete Watch</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <table className="table">
                    <tbody>
                    {watch_list.map((watch, index) => (
                        <tr key={index}>
                            <td>{watch.name}</td>
                            <td>
                                <button className="deleteButton" onClick={() => {
                                    onClickDelete(watch);
                                    setShowDeleteWatchMenu(false)
                                }}>Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </Modal.Body>
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

                <Dropdown.Menu style={{maxHeight: "40vh", overflowY: "auto"}}>
                    {data.map(item => (
                        <CycleSelector cycle={item} global_state={global_state}/>
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

    const [data, setData] = useState(null);

    useEffect(() => {
        if (global_state.global_watch !== null && global_state.global_cycle !== null) {
            axios.get(BACKEND_URL + '/measurements/' + global_state.global_watch.id + '/' + global_state.global_cycle)
                .then(response => {
                    setData(response.data)
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                });
        }
    }, [global_state.global_watch, global_state.global_cycle])

    if (global_state.global_watch === null) {

        return (
            <div className="d-flex justify-content-center align-items-center" style={{height: "80vh"}}>
                <div className="display-4">Please select a watch</div>
            </div>
        );
    } else {

        return (
            <div>
                <div style={{overflow: 'auto', textAlign: 'left'}}>
                    <table style={{width: '100%'}}>
                        <tbody>
                        <tr>
                            <td style={{width: '50%', paddingRight: '20px'}}>
                                <MeasurementList global_state={global_state} data={data} setData={setData}/>
                            </td>
                            <td>
                                <div style={{overflowY: "auto", height: "80vh"}}>
                                    <MeasurementPlot global_state={global_state} data={data} setData={setData}/>
                                    <StatsView global_state={global_state} measurement_data={data}
                                               set_measurement_data={setData}/>
                                </div>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        )
    }
}

function StatsView({global_state, measurement_data, set_measurement_data}) {
    let [data, setData] = useState(null);

    useEffect(() => {
        axios.get(BACKEND_URL + '/stats/' + global_state.global_watch.id + '/' + global_state.global_cycle)
            .then(response => {
                setData(response.data)
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [global_state.global_watch, global_state.global_cycle, measurement_data])

    return (
        <div>
            <table className="table">
                <thead>
                <tr>
                    <th>Stat</th>
                    <th>Value</th>
                </tr>
                </thead>
                <tbody>
                {data && Object.keys(data).map((key, index) => (
                    <tr key={index}>
                        <td>{key}</td>
                        <td>{data[key]}</td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}

function MeasurementList({global_state, data, setData}) {

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
        if (typeof value === 'string') {
            try {
                value = parseFloat(value)
            } catch (error) {
                return
            }
        }
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
                        <th style={{position: "sticky", top: "0"}}>Time Stamp</th>
                        <th style={{position: "sticky", top: "0"}}>Measure</th>
                        <th style={{position: "sticky", top: "0"}}>Delta</th>
                        <th style={{position: "sticky", top: "0"}}></th>
                    </tr>
                    </thead>
                    <tbody>
                    {data && data.map((item, index) => (
                        <tr key={index}>
                            <td>{item.datetime}</td>
                            <td>{item.measure}</td>
                            <td>{item.difference}</td>
                            <td>
                                <button className="deleteButton"
                                        onClick={() => handleDelete({measurement_id: item.log_id})}>Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
            <table>
                <tbody>
                <tr>
                    <td style={{paddingRight: "10px"}}>
                        <input type="text" id="value"/>
                    </td>
                    <td>
                        <button className="createButton" onClick={() => handleCreate({
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

function MeasurementPlot({global_state, data, setData}) {

    useEffect(() => {
        if (data) {
            let x = data.map(item => item.datetime)
            let y = data.map(item => item.measure)
            let trace1 = {
                x: x,
                y: y,
                mode: 'lines',
                name: 'interpolated'
            };
            let trace2 = {
                x: x,
                y: y,
                mode: 'markers',
                name: 'measured',
                marker: {
                    size: 10
                }
            };
            let plotData = [trace1, trace2];
            Plotly.newPlot('plot', plotData, {margin: {t: 0}})
        }
    }, [data])

    return (
        <div id="plot"></div>
    );
}
