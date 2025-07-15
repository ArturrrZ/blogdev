import React, {useState} from 'react'
import IconButton from '@mui/material/IconButton';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';
import { Typography } from '@mui/material';
import api from '../api';

function MarkEmailReadIconButton(props) {
    const [isHovered, setIsHovered] = useState(false);
    function sendReadRequest(){
        props.sendReadRequest()
    }
  return (
    <IconButton 
    color="primary" 
    size='small' 
    aria-label="mark email read" 
    onMouseEnter={()=>{setIsHovered(true)}} 
    onMouseLeave={()=>{setIsHovered(false)}}
    onClick={sendReadRequest}
    >
    
          <MarkEmailReadIcon />
          {isHovered&&
          <Typography 
          sx={{position: 'absolute', marginTop: '60px', fontSize: '10px', backgroundColor: '#000000', padding:'2px', borderRadius:'4px', color: 'white', width:'50px'}}
          >mark as read</Typography>}
    </IconButton>
  )
}

export default MarkEmailReadIconButton
