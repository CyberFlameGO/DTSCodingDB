export default class ResourceManager {
    // The methods in this class are designed to have one point return for readability purposes.
    // This is noted here to explain the redundant-looking code in the methods below.

    // This method gets user cookies
    // Adapted from https://www.w3schools.com/js/js_cookies.asp
    static getCookie(cname) {
        // cname is the name of the cookie
        let name = cname + '=';
        let decodedCookie = decodeURIComponent(document.cookie);
        // Split cookie string into an array of cookie strings - in the program only one cookie is used
        // but this is a general method that can be used for multiple cookies (useful for extending the program)
        let ca = decodedCookie.split(';');
        // Loop through the array of cookie strings
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            // If the cookie string contains the name of the cookie, return the cookie value
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        // If the cookie is not found, return an empty string
        return '';
    }

    static handleFormSubmission(formId, conflictMessage, token) {
        /**
         * This method handles error codes unlike regular HTML forms
         * @param {string} formId - The id of the form to be submitted
         * @param {string} conflictMessage - The message to be displayed when a conflict occurs
         * @param {string} token - The token to be used for authorization
         */
        // This particular method has status codes hard-coded on purpose.
        const HTTP_409_CONFLICT = 409;
        const HTTP_303_SEE_OTHER = 303;
        // Store reference to "this" context
        const that = this;

        document
            .getElementById(formId)
            .addEventListener('submit', async function (e) {
                e.preventDefault(); // prevent default form submission behaviour
                const form = this;
                try {
                    const headers = {}; // predefine headers object
                    if (token) {
                        // If the token exists, add authorization bearer header
                        headers.Authorization = `Bearer ${token}`;
                    }
                    // Send request to the URL specified in the form action attribute
                    const response = await that.sendRequest(
                        form.action,
                        'POST',
                        new FormData(form),
                        headers // passing headers to the sendRequest method
                    );
                    // Handle response
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

    static async sendRequest(url, httpMethod, body, headers) {
        /**
         * This method sends a request to the specified URL
         * @param {string} url - The URL to send the request to
         * @param {string} httpMethod - The HTTP method to be used
         * @param {object} body - The body of the request
         * @param {object} headers - The headers of the request
         */
        const options = {
            method: httpMethod,
            headers: headers,
        };
        // If the body is a FormData object, set the body to the FormData object
        if (body instanceof FormData) {
            options.body = body;
        } else if (body) {
            // If the body is not a FormData object, stringify the body and set the Content-Type header
            options.body = JSON.stringify(body);
            options.headers['Content-Type'] = 'application/json';
        }
        return await fetch(url, options);
    }

    static async editResource(resourceId, resourceDetails, resourceURL, token) {
        /**
         * This method edits a resource
         * @param {string} resourceId - The id of the resource to be edited
         * @param {object} resourceDetails - The details of the resource to be edited
         * @param {string} resourceURL - The URL of the resource to be edited
         * @param {string} token - The token to be used for authorization
         */
        let result = null;
        const url = `${resourceURL}/${resourceId}`;

        // define headers if token is available
        const headers = token ? { Authorization: `Bearer ${token}` } : null;

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
        /**
         * This method deletes a resource
         * @param {string} resourceId - The id of the resource to be deleted
         * @param {string} resourceURL - The URL of the resource to be deleted
         * @param {string} token - The token to be used for authorization
         */
        // added token parameter
        let res = null;

        const url = `${resourceURL}/${resourceId}`;

        // define headers if token is available
        const headers = token ? { Authorization: `Bearer ${token}` } : null;

        try {
            res = await this.sendRequest(url, 'DELETE', null, headers); // pass headers as a parameter
        } catch (error) {
            console.error('Error:', error);
        }

        return res;
    }
}
