import React, {useState} from 'react'
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import { useNavigate } from 'react-router-dom';
import { Typography } from '@mui/material/';
import IconButton from '@mui/material/IconButton';
import MarkEmailReadIconButton from './MarkEmailReadIconButton';
import MarkEmailUnreadIconButton from './MarkEmailUnreadIconButton';
import api from '../api';
function Notification(props) {

    const is_mobile = window.innerWidth < 1025;
    const [isHovered, setIsHovered] = useState(false);
    const {data, all, setAllCount} = props
    const [isRead, setIsRead] = useState(data.is_read)
    function sendReadRequest(){
        api.put("/api/notifications/mark-read/", {
          "ids": [data.id],
          "mark_read": true
        })
        .then(res=>{
          setIsRead(true)
        })
        .catch(err=>{console.error(err)})
    }
    function sendUnreadRequest(){
      api.put("/api/notifications/mark-read/", {
          "ids": [data.id],
          "mark_read": false
        })
        .then(res=>{
          setIsRead(false)
        })
        .catch(err=>{console.error(err)})
    }

    const [fromuser, setFromUser] = useState(data.fromuser)
    const navigate = useNavigate();
    function getColorBycategory(category){
      switch (category){
        case "like": return "secondary";
        case "subscription": return "success";
        case "comment": return "info";
        case "other": return "warning";
      }
    }

  return (
    <Box 
    onMouseEnter={()=>{if (all){setIsHovered(true)}}} 
    onMouseLeave={()=>{if (all) {setIsHovered(false)}}}
    onClick={()=>{
      if (is_mobile && all) {setIsHovered(!isHovered)}
      }}
    sx={{border:'1px solid rgba(0, 0, 0, 0.37)',
    backgroundColor: isRead?"#eeeeee":"#FFFFFF",
    borderRadius:'15px', padding: '5px', display: 'flex', 
    alignItems:'center', justifyContent:'space-between',
    flexWrap: 'wrap',
    minWidth: '100px',
    height: '40px',
    '&:hover': {
    boxShadow: !isRead && '0 0 1px rgba(0, 0, 0, 0.6)', // glow эффект
    transform: isRead ? 'scale(1.0)': 'scale(1.01)', // лёгкое увеличение
  }}}>
      <Box sx={{ display: 'flex', alignItems:'center'}}>
      {fromuser&&
      <Chip
        sx={{
            '&:hover':{
                cursor:'pointer'
            }
        }}
        onClick={()=>{navigate(`/user/${fromuser.username}`)}}
        avatar={<Avatar alt={fromuser.username} src="/static/images/avatar/1.jpg" />}
        label={fromuser.username}
        variant="outlined"
      />}
      <Typography sx={{marginLeft:"10px"}}>{data.message}</Typography>
      </Box>

      {isHovered
      ?
      <Box className="right-side actions" sx={{ display: 'flex', alignItems:'center'}}>
        {isRead
        ?<MarkEmailUnreadIconButton sendUnreadRequest={sendUnreadRequest}/>
        :<MarkEmailReadIconButton sendReadRequest={sendReadRequest} />
        }
        
      </Box>
      :
      <Box className="right-side" sx={{ display: 'flex', alignItems:'center'}}>
        <Chip
          variant="contained"
          color={getColorBycategory(data.category)}
          label={data.category}
          size="small"
        />
        <Typography sx={{color:"#808080", margin: '0px 5px'}} fontSize={12}>{new Date(data.timestamp).toLocaleString()}</Typography>
      </Box>}     
    </Box>
  )
}

export default Notification
