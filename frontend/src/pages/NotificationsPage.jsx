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
function NotificationsPage() {
    const {notifications, setNotifications} = useContext(AuthContext);
    const [notificationsData, setNotificationsData] = useState([])
    const [allNotificationsData, setAllNotificationsData] = useState([])
    const [allCount, setAllCount] = useState(0)
    const [page, setPage] = useState(1)
    const [paginated, setPaginated] = useState([])
    const [all, setAll] = useState(false)
    const pagesMarkedRead = useRef([])
    const [value, setValue] = useState('1');
    const handleChange = (event, newValue) => {
      setValue(newValue)
      if (newValue === '2') {
        setAll(true)
        changePage(1, false)
      } else {
        setAll(false)
        changePage(1, true)
      }
      
    }

    function changePage(pageNum = 1, unreadNotif = true){
      const arrayToSlice = unreadNotif ? notificationsData : allNotificationsData;
      let sliceStart, sliceEnd;
      sliceStart = (pageNum - 1) * 10;
      sliceEnd = (pageNum) * 10;
      let currentPageNotifications = arrayToSlice.slice(sliceStart, sliceEnd);
      setPaginated(currentPageNotifications);
      setPage(pageNum);

      if (!all && !pagesMarkedRead.current.includes(pageNum)) {
        // mark as read from pagination 
        const ids = currentPageNotifications.map(not => not.id);
        api.put("/api/notifications/mark-read/", {
          "ids": ids
         })
        .then((res) => {
          console.log(res.data)
          pagesMarkedRead.current.push(pageNum);
          console.log(pagesMarkedRead.current)
        })
        .catch(err=>{console.error("Error: ", err)})
      }
    }

    useEffect(()=>{
      api.get("/api/notifications/all/?only_count=false&read_all=true")
      .then(res=>{
        console.log(res.data)
        setNotificationsData(res.data.unread_notifications)
        setAllNotificationsData(res.data.all_notifications)
        setAllCount(res.data.count)
      })
    }, [])

    useEffect(() => {
      if (notificationsData.length > 0) {
      changePage();
      }
      }, [notificationsData]);

    const totalUnreadPages = Math.ceil(notificationsData.length / 10);
    const totalAllPages = Math.ceil(allNotificationsData.length / 10);
  return (
    <div>
      <Box sx={{display: 'flex', flexDirection: 'column', margin: '0px 200px'}}>
      <TabContext value={value}>
        <Box sx={{ width:"100%",display: 'flex', flexDirection:'row', justifyContent: 'space-evenly', borderBottom: 1, borderColor: 'divider' , backgroundColor: 'white', borderRadius: '15px 15px 0px 0px'}}>
          <TabList onChange={handleChange} aria-label="lab API tabs example" >
            <Tab label="Unread" value="1" />
            <Tab label="All notifications" value="2" />
          </TabList>
        </Box>

        <TabPanel value="1" sx={{padding: "0px 0px"}}>
          Unread: 
          <Stack spacing={5} direction='column'>
          {paginated.map((not)=>{return <pre>{JSON.stringify(not)}</pre>})}
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
        All:
         <Stack spacing={5}>
              {paginated.map(not => (
                <pre key={not.id}>{JSON.stringify(not,)}</pre>
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
        </TabPanel>
      </TabContext>
      </Box>
    </div>
  )
}

export default NotificationsPage
