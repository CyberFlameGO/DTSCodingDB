export default class ResourceManager {
    // The methods in this class are designed to have one point return for readability purposes.
    // This is noted here to explain the redundant-looking code in the methods below.

    static async sendRequest(url, httpMethod, body) {
        const options = {
            method: httpMethod,
            headers: {},
        };

        if (body) {
            options.body = JSON.stringify(body);
            options.headers['Content-Type'] = 'application/json';
        }

        return await fetch(url, options);
    }

    static async editResource(resourceId, resourceDetails, resourceURL) {
        let result = null;
        const url = `${resourceURL}/${resourceId}`;
        try {
            result = await this.sendRequest(url, 'PATCH', resourceDetails);
        } catch (error) {
            console.error('Error:', error);
        }
        return result;
    }

    static async deleteResource(resourceId, resourceURL) {
        let res = null;

        const url = `${resourceURL}/${resourceId}`;
        try {
            res = await this.sendRequest(url, 'DELETE');
        } catch (error) {
            console.error('Error:', error);
        }

        return res;
    }
}
