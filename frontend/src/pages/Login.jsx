import React, {useState, useContext} from 'react'
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import api from '../api';
import {useNavigate} from "react-router-dom"
import "../styles/login.css"
import { AuthContext } from '../AuthContext';

function Login() {
    const {setAuthenticated, setCreator, setUser} = useContext(AuthContext);
    const navigate = useNavigate()
    const [login, setLogin] = useState("")
    function handleLoginChange(e){
        setLogin(e.target.value)
    }
    const [password, setPassword] = useState("")
    function handlePasswordChange(e){
        setPassword(e.target.value)
    }
    function handleSubmit(e){
        e.preventDefault()
        api.post("/api/accounts/login_logout/",{
            username: login,
            password: password
        })
        .then(response=>{
            console.log(response.data)
            sessionStorage.setItem("access_token_expiration", response.data.expiration)
            setAuthenticated(true)
            setUser(response.data.username)
            // console.log(response.data)
            if (response.data.is_creator) {
                setCreator(true);
            }
            
            navigate("/")
        })
        .catch(err=>{
            setErr(true);
            setTimeout(()=>{setErr(false)}, 3000)
            console.error(err)})
    }
    const [err, setErr] = useState(false)
  return (
    <div className='loginPage'>
        <form onSubmit={handleSubmit}>
            <TextField 
            error={err}
            id="standard-basic" 
            label="Username" 
            value={login}
            onChange={handleLoginChange}
            required    
            /><br/>
            <TextField
            id="outlined-password-input"
            error={err}
            label="Password"
            type="password"
            value={password}
            onChange={handlePasswordChange}
            required
            /><br/>
            {err&&<p style={{color:'red'}}>Invalid Credentials</p>}
            <Button variant="contained" type='submit'>Login</Button>
        </form>
    </div>
  )
}

export default Login
