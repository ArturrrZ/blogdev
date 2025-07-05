import React, {useContext, useEffect, useState} from 'react'
import { AuthContext } from '../AuthContext'

function NotificationsPage() {
    const {notifications, setNotifications} = useContext(AuthContext);
    const [someState, setSomeState] = useState(false);
    // console.log("changed")
    useEffect(()=>{
        setNotifications(0);
        console.log("cleared notificaitons")
    }, [])
    useEffect(()=>{
        console.log("changed state")
    }, [someState])
  return (
    <div>
      notifications
      <button onClick={()=>{setSomeState(!someState)}}>{someState&&"un"}change state</button>
    </div>
  )
}

export default NotificationsPage
