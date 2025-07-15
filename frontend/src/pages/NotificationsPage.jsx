import React, {useContext, useEffect, useState, useRef} from 'react'
import { AuthContext } from '../AuthContext'
import api from '../api';
import Pagination from '@mui/material/Pagination';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import TabContext from '@mui/lab/TabContext';
import TabList from '@mui/lab/TabList';
import TabPanel from '@mui/lab/TabPanel';
import {useNavigate} from "react-router-dom"
import Button from '@mui/material/Button';
import { Typography } from '@mui/material';
import Notification from '../components/Notification'

function NotificationsPage() {
  const [loading, setLoading] = useState(true);
    async function fetchNotifications(touchUnreadUseEffect = true){
      setLoading(true)
      try {
         const res = await api.get("/api/notifications/all/?only_count=false&read_all=true")
         setAllNotificationsData(res.data.all_notifications)
        if (touchUnreadUseEffect) {setNotificationsData(res.data.unread_notifications)}
        setAllCount(res.data.count)
        setUnreadCount(res.data.unread_notifications.length)
      }
      catch(err){
        console.error(err)
      }
      
    }
    const {notifications, setNotifications} = useContext(AuthContext);
    const [notificationsData, setNotificationsData] = useState([])
    const [allNotificationsData, setAllNotificationsData] = useState([])
    const [allCount, setAllCount] = useState(0)
    const [unreadCount, setUnreadCount] = useState(0)
    const [page, setPage] = useState(1)
    const [paginated, setPaginated] = useState([])
    const [all, setAll] = useState(false)
    const pagesMarkedRead = useRef([])
    const [value, setValue] = useState('1');
     const handleChange = async (event, newValue) => {
      setValue(newValue);
      setAll(newValue === '2');
      await fetchNotifications(); // обновим данные
      };



    function changePage(pageNum = 1, unreadNotif = true){
      const arrayToSlice = unreadNotif ? notificationsData : allNotificationsData;
      let sliceStart, sliceEnd;
      sliceStart = (pageNum - 1) * 10;
      sliceEnd = (pageNum) * 10;
      let currentPageNotifications = arrayToSlice.slice(sliceStart, sliceEnd);
      setPaginated(currentPageNotifications);
      setPage(pageNum);

      // if (!all && !pagesMarkedRead.current.includes(pageNum)) {
      //   // mark as read from pagination 
      //   const ids = currentPageNotifications.map(not => not.id);
      //   api.put("/api/notifications/mark-read/", {
      //     "ids": ids
      //    })
      //   .then((res) => {
      //     console.log(res.data)
      //     pagesMarkedRead.current.push(pageNum);
      //     console.log(pagesMarkedRead.current)
      //   })
      //   .catch(err=>{console.error("Error: ", err)})
      // }
    }
    function markAllread(){
      let result = window.confirm("Are you sure you want to proceed?");
      if (result) {
        console.log("mark all read")
      }
    }
    useEffect(()=>{
      fetchNotifications()
    }, [])

    useEffect(() => {
      if (value === '1' && notificationsData.length > 0) {
        changePage(1, true);
      } else if (value === '2' && allNotificationsData.length > 0) {
       changePage(1, false);
     }
     setLoading(false)
      }, [notificationsData, allNotificationsData]);


    const totalUnreadPages = Math.ceil(notificationsData.length / 10);
    const totalAllPages = Math.ceil(allNotificationsData.length / 10);
  return (<Box>
    
    
      <Box sx={{display: 'flex', flexDirection: 'column', margin: '0px 200px'}}>
      <TabContext value={value}>
        <Box sx={{ width:"100%",display: 'flex', flexDirection:'row', justifyContent: 'space-evenly', borderBottom: 5, borderColor: 'divider' , backgroundColor: 'white', borderRadius: '15px 15px 0px 0px'}}>
          <TabList onChange={handleChange} aria-label="lab API tabs example" >
            <Tab label="Unread" value="1" />
            <Tab label="All notifications" value="2" />
          </TabList>
        </Box>
        {loading?<p>loading</p>:<Box>
        <TabPanel value="1" sx={{padding: "0px 0px",}}>
          <Stack spacing={2} direction='column'>
          {paginated.map((not)=>{return <Notification key={not.id} data={not} all={true}  />})}
          </Stack>
          {totalUnreadPages > 1 && (
              <Pagination
                count={totalUnreadPages}
                page={page}
                onChange={(e, val) => changePage(val, true)}
                color="primary"
                showFirstButton
                showLastButton
              />
            )}
        </TabPanel>

        <TabPanel value="2" sx={{padding: "0px 0px"}}>
        <Box sx={{display: 'flex', justifyContent: 'space-between', margin: '15px 0px'}}>
          <Box>
            <Typography>All notifications count: {allCount}</Typography>
            <Typography>Unread notifications: {unreadCount}</Typography>
            </Box>
          <Box>
            <Button variant="contained" onClick={markAllread} sx={{height: '100%'}}>Mark all read</Button>  
          </Box>
        </Box>
  
         <Stack spacing={2}>
              {paginated.map(not => (
                <Notification key={not.id} data={not} all={all} />
              ))}
            </Stack>      
        {totalAllPages > 1 && (
              <Pagination
                count={totalAllPages}
                page={page}
                onChange={(e, val) => changePage(val, false)}
                color="secondary"
                showFirstButton
                showLastButton
              />
            )}
        </TabPanel></Box>
        }
      </TabContext>
      </Box>
    
    </Box>
  )
}

export default NotificationsPage
