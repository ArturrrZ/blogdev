import axios from "axios"
async function updateAccessToken() {
    try {
        const res = await api.get("/api/accounts/refresh_token/")
        return true
    }
    catch (err) {
        console.error("Failed to refresh access token: ", err)
        return false
    } 
}

const baseURLback = import.meta.env.VITE_API_URL
const baseURLfront = import.meta.env.VITE_APP_URL

const api = axios.create({
    baseURL: baseURLback,
    withCredentials: true,
})

api.interceptors.response.use(function (response) {
    // Any status code that lie within the range of 2xx cause this function to trigger
    // Do something with response data
    // console.log("message from interceptors")
    return response;
  }, async function (error) {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    // Do something with response error
    console.log("error from interceptor")
    console.log(error)
    console.log(error.response)
    if (error.response.status === 401) {
        const updatedToken = await updateAccessToken();
        if (updatedToken) {
            try {
                console.log("Retrying original request")
                return api.request(error.config); // Retrying original request
            } catch (retryError) {
                console.error("Retry failed: ", retryError);
                return Promise.reject(retryError);
            }
        }
        else {
            console.log("Refresh token is expired!")
            sessionStorage.clear()
            window.location.href = `${baseURLfront}login`
            return
        }    
    }
    return Promise.reject(error);
  });


export default api