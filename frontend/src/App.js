import React, { useEffect, useState } from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import { BACKEND_URL } from './settings';
import axios from "axios";
import useGlobalState, { createGlobalState } from "./globalstate";

let current_watch_global= createGlobalState(null);
let current_cycle_global= createGlobalState(null);

function TopLine() {
return (
  <nav className="navbar navbar-expand-lg navbar-light bg-light">
    <a className="navbar-brand" href="#">Watch tracking</a>
    <WatchSelectList />
  </nav>
)
}

function WatchSelectList() {
  const [data, setData] = useState([]);
  let [current_watch, use_current_watch] = useGlobalState(current_watch_global);

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
          {current_watch ? current_watch.name : "Select a watch"}
        </Dropdown.Toggle>

        <Dropdown.Menu>
          {data.map(item => (
            <WatchSelector watch={item} />
          ))}
        </Dropdown.Menu>
      </Dropdown>
    </nav>
  );
}

function WatchSelector({watch}) {
    let [current_watch, use_current_watch] = useGlobalState(current_watch_global);
    let [current_cycle, use_current_cycle] = useGlobalState(current_cycle_global);

    const handleClick = () => {
      use_current_watch(watch);
      const max_cycle= Math.max(...watch.cycles);
      use_current_cycle(max_cycle);
    }

  return (
    <Dropdown.Item onClick={handleClick}>
      {watch.name}
    </Dropdown.Item>
  );
}

// ========================================

function Content() {
    let [current_watch, use_current_watch] = useGlobalState(current_watch_global);

    if (!current_watch) {
        return <div>Please select a watch</div>;
    }

    return (
        <div>
            <MeasurementList />
        </div>
    );
}

function MeasurementList() {
    let [current_cycle, use_current_cycle] = useGlobalState(current_cycle_global);
    let [current_watch, use_current_watch] = useGlobalState(current_watch_global);
    const [data, setData] = useState(null);

    useEffect(() => {
        axios.get(BACKEND_URL + '/watch/' + current_watch.id + '/' + current_cycle + '/measurements')
            .then(response => {
                setData(response.data)
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [current_watch, current_cycle]);

    return (
        <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            <table className="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Datetime</th>
                        <th>Value</th>
                        <th>Diff</th>
                    </tr>
                </thead>
                <tbody>
                    {data && data.map((item, index) => (
                        <tr key={index}>
                            <td>{item.id}</td>
                            <td>{item.datetime}</td>
                            <td>{item.value}</td>
                            <td>{item.diff}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function App() {
  return (<div><TopLine/><Content/></div>)
}

export default App;
