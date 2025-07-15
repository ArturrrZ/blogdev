import React, {useState} from 'react'
import IconButton from '@mui/material/IconButton';
import MarkEmailUnreadIcon from '@mui/icons-material/MarkEmailUnread';
import { Typography } from '@mui/material';
import api from '../api';

function MarkEmailUnreadIconButton(props) {
    const [isHovered, setIsHovered] = useState(false);
    function sendUnreadRequest(){
        props.sendUnreadRequest()
    }
  return (
    <IconButton 
    color="default" 
    size='small' 
    aria-label="mark email unread" 
    onMouseEnter={()=>{setIsHovered(true)}} 
    onMouseLeave={()=>{setIsHovered(false)}}
    onClick={sendUnreadRequest}
    >
          <MarkEmailUnreadIcon />
          {isHovered&&
          <Typography 
          sx={{position: 'absolute', marginTop: '60px', fontSize: '10px', backgroundColor: '#000000', padding:'2px', borderRadius:'4px', color: 'white', width:'50px'}}
          >unread</Typography>}
    </IconButton>
  )
}

export default MarkEmailUnreadIconButton
