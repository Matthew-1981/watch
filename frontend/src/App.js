import React, { useEffect, useState } from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import { BACKEND_URL } from './settings';
import axios from "axios";

function TopLine({global_watch, set_global_watch}) {

    // const tmp = (current_watch ? (<CycleSelectList />) : (<div></div>))

    return (
      <nav className="navbar navbar-expand-lg navbar-light bg-light">
        <a className="navbar-brand" href="#">Watch tracking</a>
        <WatchSelectList global_watch={global_watch} set_global_watch={set_global_watch} />
        {/*{tmp}*/}
      </nav>
    )
}

function WatchSelectList({global_watch, set_global_watch}) {
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
          {global_watch.watch ? global_watch.watch.name : "Select a watch"}
        </Dropdown.Toggle>

        <Dropdown.Menu>
          {data.map(item => (
            <WatchSelector watch={item}
                           global_watch={global_watch}
                           set_global_watch={set_global_watch} />
          ))}
        </Dropdown.Menu>
      </Dropdown>
    </nav>
  );
}

function WatchSelector({watch, global_watch, set_global_watch}) {
    const handleClick = () => {
      const max_cycle= Math.max(...watch.cycles);
      set_global_watch({watch: watch, cycle: max_cycle});
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

function Content({global_watch, set_global_watch}) {

    if (!global_watch.watch) {
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
                            <MeasurementList global_watch={global_watch} set_global_watch={set_global_watch}/>
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

function MeasurementList({global_watch, set_global_watch}) {
    const [data, setData] = useState(null);

    useEffect(() => {
        axios.get(BACKEND_URL + '/watch/' + global_watch.watch.id + '/' + global_watch.cycle + '/measurements')
            .then(response => {
                setData(response.data)
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }, [global_watch])

    const handleDelete = ({measurement_id}) => {
        axios.delete(BACKEND_URL + '/watch/' + global_watch.watch.id + '/' + global_watch.cycle + '/measurement/' + measurement_id)
            .then(response => {
                axios.get(BACKEND_URL + '/watch/' + global_watch.watch.id + '/' + global_watch.cycle + '/measurements')
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
    let [global_watch, set_global_watch] = useState({watch: null, cycle: null})

    return (
        <div>
            <TopLine global_watch={global_watch} set_global_watch={set_global_watch}/>
            <div style={{padding: '10px'}}>
                <Content global_watch={global_watch} set_global_watch={set_global_watch}/>
            </div>
        </div>
    )
}
