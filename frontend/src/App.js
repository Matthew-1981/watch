import React, { useEffect, useState } from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import { BACKEND_URL } from './settings';
import axios from "axios";
import useGlobalState, { createGlobalState } from "./globalstate";

let current_watch_global= createGlobalState(null);
let current_cycle_global= createGlobalState(null);

function TopLine() {
    let [current_watch, use_current_watch] = useGlobalState(current_watch_global);

    // const tmp = (current_watch ? (<CycleSelectList />) : (<div></div>))

    return (
      <nav className="navbar navbar-expand-lg navbar-light bg-light">
        <a className="navbar-brand" href="#">Watch tracking</a>
        <WatchSelectList />
        {/*{tmp}*/}
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
//
// function CycleSelectList() {
//   const [data, setData] = useState([]);
//   let [current_watch, use_current_watch] = useGlobalState(current_watch_global);
//   let [current_cycle, use_current_cycle] = useGlobalState(current_cycle_global);
//
//   const cycles = [...current_watch.cycles]
//   setData(cycles.sort())
//
//   return (
//     <nav className="navbar navbar-expand-lg navbar-light bg-light">
//       <Dropdown>
//         <Dropdown.Toggle variant="success" id="dropdown-basic">
//           {current_cycle}
//         </Dropdown.Toggle>
//           <Dropdown.Menu>
//               {data.map(item => (
//                 <CycleSelector cycle={item} />
//               ))}
//         </Dropdown.Menu>
//       </Dropdown>
//     </nav>
//   );
// }
//
// function CycleSelector({cycle}) {
//     let [current_cycle, use_current_cycle] = useGlobalState(current_cycle_global);
//
//     const handleClick = () => {
//       use_current_cycle(cycle);
//     }
//
//   return (
//     <Dropdown.Item onClick={handleClick}>
//       {cycle}
//     </Dropdown.Item>
//   );
// }

// ========================================

function Content() {
    let [current_watch, use_current_watch] = useGlobalState(current_watch_global);

    if (!current_watch) {
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
                        <td style={{width: '50%', paddingRight: '20px'}}><MeasurementList/></td>
                        <td><div style={{width: '100px', height: '100px', backgroundColor: 'red'}}></div></td>
                    </tr>
                    </tbody>
                </table>
            </div>
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

    const handleDelete = ({measurement_id}) => {
        axios.delete(BACKEND_URL + '/watch/' + current_watch.id + '/' + current_cycle + '/measurement/' + measurement_id)
            .then(response => {
                axios.get(BACKEND_URL + '/watch/' + current_watch.id + '/' + current_cycle + '/measurements')
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

    return (
        <div style={{ maxHeight: '300px', overflow: 'auto' }}>
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
                            <td>{item.value}</td>
                            <td>{item.diff}</td>
                            <td><button onClick={() => handleDelete({measurement_id: item.id})}>Delete</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// ========================================

export default function App() {
  return (<div><TopLine/><div style={{padding: '10px'}}><Content/></div></div>)
}
