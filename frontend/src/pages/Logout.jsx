import React, {useContext} from 'react'
import Button from '@mui/material/Button';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import { AuthContext } from '../AuthContext';


function Logout() {
    const {setAuthenticated, setCreator} = useContext(AuthContext);
    const [finish, setFinish] = React.useState(false);
    const navigate = useNavigate()
    function handleLogout(){
        api.delete("/api/accounts/login_logout/")
        .then(response=>{
            sessionStorage.clear()
            setFinish(true)
            setTimeout(()=>{
              setAuthenticated(false)
              setCreator(false)
              navigate("/login")}, 3000)
        })
        .catch(err=>{
            alert(err)
        })
    }

  return (
    <div className=''>
    {!finish&&<div className='logout'>
        <h3>Are you sure you want to log out?</h3>
        <Button variant="contained" size="large" onClick={handleLogout} sx={{marginBottom: '15px'}}>
            Yes
        </Button>  
        <Button variant="outlined" size="large" onClick={()=>{navigate("/")}}>
          No
        </Button></div>}
        {finish&&<Alert severity="success" className='logout'>You successfully logged out! Redirecting...</Alert>}        
    </div>
  )
}

export default Logout
