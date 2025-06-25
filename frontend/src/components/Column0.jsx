import React from 'react'
import YouTubeIcon from '@mui/icons-material/YouTube';
import IconButton from '@mui/material/IconButton';
import InstagramIcon from '@mui/icons-material/Instagram';
import { Button } from '@mui/material';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import { useNavigate } from 'react-router-dom';
import api from '../api';

// import CloudUploadIcon from '@mui/icons-material/CloudUpload';

// const VisuallyHiddenInput = styled('input')({
//   clip: 'rect(0 0 0 0)',
//   clipPath: 'inset(50%)',
//   height: 1,
//   overflow: 'hidden',
//   position: 'absolute',
//   bottom: 0,
//   left: 0,
//   whiteSpace: 'nowrap',
//   width: 1,
// });
// <Button
//       component="label"
//       role={undefined}
//       variant="contained"
//       tabIndex={-1}
//       startIcon={<CloudUploadIcon />}
//     >
//       Upload files
//       <VisuallyHiddenInput
//         type="file"
//         onChange={(event) => console.log(event.target.files)}
//         multiple
//       />
//     </Button>
function Column0(props) {
    const {data} = props;
    const navigate = useNavigate()
    function handleFollowClick(){
      api.post("/api/subscribe/", {
        username: data.profile.username
      })
      .then(res=>{
        console.log(res.data)
        window.open(res.data.checkout_url, "_blank");
      })
      .catch(err=>{console.log(err)})
    }
  return (
    <div className='column0'>
        <img className="profile-pic" alt='profile picture' src={data.profile.profile_picture}/>
        <p className='profile_username'>@{data.profile.username}</p>
        <p className='profile_sub_total'>{data.profile.subscribers}</p>
        <p className='profile_sub' >subscribers</p>
        {data.is_subscribed
        ?<Button disabled className='profile_button' variant="outlined" startIcon={<CheckBoxIcon/>}>Following</Button>
        :(data.my_page?<Button onClick={()=>{navigate('/creator/edit/')}} className='profile_button' variant="contained">Edit Profile</Button>:<Button onClick={handleFollowClick} className='profile_button' variant="contained">Follow</Button>)}
        <div>
          {data.profile.youtube?
          <IconButton  size='large' onClick={()=>{window.open(data.profile.youtube)}}>
              <YouTubeIcon sx={{color: 'red'}} />
          </IconButton>
          :<IconButton  size='large'>
              <YouTubeIcon sx={{color: 'gray'}} />
          </IconButton>}
          {data.profile.instagram?
          <IconButton size='large' onClick={()=>{window.open(data.profile.instagram)}}>
              <InstagramIcon sx={{color:'red'}}/>
          </IconButton>
          :<IconButton size='large'>
              <InstagramIcon sx={{color:'gray'}}/>
          </IconButton>}
        </div>
      </div>
  )
}

export default Column0
