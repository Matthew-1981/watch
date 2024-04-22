import React, { useEffect, useState } from "react";
import Dropdown from 'react-bootstrap/Dropdown';
import { BACKEND_URL } from './settings';
import { BackendApi } from "./backendapi";
import axios from "axios";

const backendApi = new BackendApi(BACKEND_URL);

function WatchSelect() {
  const [data, setData] = useState([]);
  let current_watch = useState(null);

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
          {current_watch ? current_watch : "Select a watch"}
        </Dropdown.Toggle>

        <Dropdown.Menu>
          {data.map(item =>
          {return (<Dropdown.Item href="#/action-1">{item.name}</Dropdown.Item>)})
          }
        </Dropdown.Menu>
      </Dropdown>
    </nav>
  );
}

function TopLine() {
return (
  <nav className="navbar navbar-expand-lg navbar-light bg-light">
    <a className="navbar-brand" href="#">My Website</a>
    <WatchSelect />
  </nav>
)
}

function App() {
  return (<div><TopLine/></div>)
}

export default App;
