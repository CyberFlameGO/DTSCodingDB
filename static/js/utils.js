export default class ResourceManager {

    static async sendRequest(url, httpMethod, body) {
        const options = {
            method: httpMethod,
            headers: {}
        };

        if (body) {
            options.body = JSON.stringify(body);
            options.headers["Content-Type"] = "application/json";
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            throw response;
        }
        return await response.json();
    }

    static async editResource(resourceId, resourceDetails, resourceURL) {
        const url = `${resourceURL}/${resourceId}`;
        try {
            await this.sendRequest(url, 'PATCH', resourceDetails);
            location.reload();
        } catch (error) {
            console.error('Error:', error);
        }
    }

    static async deleteResource(resourceId, resourceURL) {
        const url = `${resourceURL}/${resourceId}`;
        try {
            await this.sendRequest(url, 'DELETE');
            location.reload();
        } catch (error) {
            console.error('Error:', error);
        }
    }
}
