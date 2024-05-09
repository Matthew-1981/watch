import React, {useEffect, useState} from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import {BACKEND_URL} from './settings';
import axios from "axios";

export default function App() {
    let [global_watch, set_global_watch] = useState(null)
    let [global_cycle, set_global_cycle] = useState(null)

    return (
        <div>
            <TopLine global_watch={global_watch} set_global_watch={set_global_watch} global_cycle={global_cycle}
                     set_global_cycle={set_global_cycle}/>
            <div style={{padding: '10px'}}>
                {<Content global_watch={global_watch} set_global_watch={set_global_watch} global_cycle={global_cycle}
                          set_global_cycle={set_global_cycle}/>}
            </div>
        </div>
    )
}

// ========================================

function TopLine({global_watch, set_global_watch, global_cycle, set_global_cycle}) {

    const tmp = (global_watch ? (<CycleSelectList global_watch={global_watch}
                                                  set_global_watch={set_global_watch}
                                                  global_cycle={global_cycle}
                                                  set_global_cycle={set_global_cycle}/>) : (<div></div>))

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <a className="navbar-brand" href="#">Watch tracking</a>
            <WatchSelectList global_watch={global_watch} set_global_watch={set_global_watch} global_cycle={global_cycle}
                             set_global_cycle={set_global_cycle}/>
            {tmp}
        </nav>
    )
}

function WatchSelectList({global_watch, set_global_watch, global_cycle, set_global_cycle}) {
    const [data, setData] = useState([]);

    useEffect(() => {
        axios.get(BACKEND_URL + '/watchlist')
            .then(response => {
                setData(response.data);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, []);

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <Dropdown>
                <Dropdown.Toggle variant="success" id="dropdown-basic">
                    {global_watch ? global_watch.name : "Select a watch"}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                    {data.map(item => (
                        <WatchSelector watch={item}
                                       global_watch={global_watch}
                                       set_global_watch={set_global_watch}
                                       global_cycle={global_cycle}
                                       set_global_cycle={set_global_cycle}/>
                    ))}
                </Dropdown.Menu>
            </Dropdown>
        </nav>
    );
}

function WatchSelector({watch, global_watch, set_global_watch, global_cycle, set_global_cycle}) {
    const handleClick = () => {
        set_global_watch(watch)
        const max_cycle = Math.max(...watch.cycles);
        set_global_cycle(max_cycle);
    }

    return (
        <Dropdown.Item onClick={handleClick}>
            {watch.name}
        </Dropdown.Item>
    );
}

function CycleSelectList({global_watch, set_global_watch, global_cycle, set_global_cycle}) {
    const [data, setData] = useState([]);

    useEffect(() => {
        const tmp = global_watch.cycles
        tmp.sort((a, b) => parseFloat(a) - parseFloat(b));
        setData(tmp)
    })

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light" style={{marginLeft: '15px'}}>
            <Dropdown>
                <Dropdown.Toggle variant="success" id="dropdown-basic">
                    {global_cycle ? global_cycle : "Select cycle"}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                    {data.map(item => (
                        <CycleSelector cycle={item}
                                       global_watch={global_watch}
                                       set_global_watch={set_global_watch}
                                       global_cycle={global_cycle}
                                       set_global_cycle={set_global_cycle}/>
                    ))}
                </Dropdown.Menu>
            </Dropdown>
        </nav>
    );
}

function CycleSelector({cycle, global_watch, set_global_watch, global_cycle, set_global_cycle}) {
    const handleClick = () => {
        set_global_cycle(cycle)
    }

    return (
        <Dropdown.Item onClick={handleClick}>
            {cycle}
        </Dropdown.Item>
    );
}

// ========================================

function Content({global_watch, set_global_watch, global_cycle, set_global_cycle}) {

    if (!global_watch) {
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
                            <MeasurementList global_watch={global_watch}
                                             set_global_watch={set_global_watch}
                                             global_cycle={global_cycle}
                                             set_global_cycle={set_global_cycle}/>
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

function MeasurementList({global_watch, set_global_watch, global_cycle, set_global_cycle}) {
    const [data, setData] = useState(null);

    useEffect(() => {
        axios.get(BACKEND_URL + '/measurements/' + global_watch.id + '/' + global_cycle)
            .then(response => {
                setData(response.data)
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [global_watch, global_cycle])

    const handleDelete = ({measurement_id}) => {
        axios.delete(BACKEND_URL + '/watch/' + global_watch.id + '/' + global_cycle + '/measurement/' + measurement_id)
            .then(response => {
                axios.get(BACKEND_URL + '/watch/' + global_watch.id + '/' + global_cycle + '/measurements')
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
        axios.post(BACKEND_URL + '/watch/' + global_watch.id + '/' + global_cycle + '/measurement', {
            datetime: str_datetime,
            value: value
        })
            .then(response => {
                axios.get(BACKEND_URL + '/watch/' + global_watch.id + '/' + global_cycle + '/measurements')
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
                                <button onClick={() => handleDelete({measurement_id: item.id})}>Delete</button>
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
