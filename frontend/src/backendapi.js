import axios from "axios";


export class BackendApi {
    constructor(base_url) {
        this.base_url = base_url;
    }

    async get_data(endpoint) {
        const response = await axios.get(this.base_url + endpoint);
        return response.data;
    }
}
