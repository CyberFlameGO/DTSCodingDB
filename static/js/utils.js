export default class ResourceManager {
    // The methods in this class are designed to have one point return for readability purposes.
    // This is noted here to explain the redundant-looking code in the methods below.

    static getCookie(cname) {
        let name = cname + '=';
        let decodedCookie = decodeURIComponent(document.cookie);
        let ca = decodedCookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        return '';
    }

    static handleFormSubmission(formId, conflictMessage, token) {
        // added optional token parameter
        // This particular method has status codes hard-coded on purpose.
        const HTTP_409_CONFLICT = 409;
        const HTTP_303_SEE_OTHER = 303;
        // Store reference to "this" context
        const that = this;

        document
            .getElementById(formId)
            .addEventListener('submit', async function (e) {
                e.preventDefault();
                const form = this;
                try {
                    const headers = {}; // predefine headers object
                    if (token) {
                        // If the token exists, add authorization bearer header
                        headers.Authorization = `Bearer ${token}`;
                    }
                    const response = await that.sendRequest(
                        form.action,
                        'POST',
                        new FormData(form),
                        headers // passing headers to the sendRequest method
                    );
                    if (response.status === HTTP_409_CONFLICT) {
                        alert(conflictMessage);
                    } else if (response.status === HTTP_303_SEE_OTHER) {
                        const data = await response.json();
                        console.log(data);
                        const redirectUrl = await data['redirectUrl']; // jshint ignore:line
                        console.log(redirectUrl);
                        if (redirectUrl) {
                            window.location.href = redirectUrl;
                        }
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            });
    }

    static async sendRequest(url, httpMethod, body) {
        const options = {
            method: httpMethod,
            headers: {},
        };

        if (body instanceof FormData) {
            options.body = body;
        } else if (body) {
            options.body = JSON.stringify(body);
            options.headers['Content-Type'] = 'application/json';
        }

        return await fetch(url, options);
    }

    static async editResource(resourceId, resourceDetails, resourceURL, token) {
        // added token parameter
        let result = null;
        const url = `${resourceURL}/${resourceId}`;

        // define headers if token is available
        const headers = token ? {Authorization: `Bearer ${token}`} : null;

        try {
            result = await this.sendRequest(
                url,
                'PATCH',
                resourceDetails,
                headers
            ); // pass headers as a parameter
        } catch (error) {
            console.error('Error:', error);
        }
        return result;
    }

    static async deleteResource(resourceId, resourceURL, token) {
        // added token parameter
        let res = null;

        const url = `${resourceURL}/${resourceId}`;

        // define headers if token is available
        const headers = token ? {Authorization: `Bearer ${token}`} : null;

        try {
            res = await this.sendRequest(url, 'DELETE', null, headers); // pass headers as a parameter
        } catch (error) {
            console.error('Error:', error);
        }

        return res;
    }
}
