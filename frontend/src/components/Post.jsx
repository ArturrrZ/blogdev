import React, {useState, useEffect} from 'react'
import "../styles/post.css"
import IconButton from '@mui/material/IconButton';
import FavoriteIcon from '@mui/icons-material/Favorite';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import { Divider } from '@mui/material';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ReportIcon from '@mui/icons-material/Report';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import api from "../api";
import Alert from '@mui/material/Alert';
import { useNavigate } from 'react-router-dom';
import Dialog from '@mui/material/Dialog';


function Post(props) {
  const [locked, setLocked] = useState(false);
  useEffect(() => {
    if (data.title === 'Locked Content') {
      setLocked(true);
    }
  }, []); 
  const navigate = useNavigate();
    const {data, myPage, setIsAtLeastOneDeleted} = props
    // console.log(data)
    const [showList, setShowList] = React.useState(false);
    const [deleted, setDeleted] = React.useState(false);
    // useState 
  const dateStringFromBackend = data.created_at;
  const dateObject = new Date(dateStringFromBackend);
  const formattedDate = dateObject.toLocaleDateString(); // "12/29/2023" (US format)
  const formattedDateTime = dateObject.toLocaleString();
  const deletePost = () => {  
    const confirmDelete = window.confirm("Are you sure you want to delete this post?"); 
    if (confirmDelete) { 
      api.delete(`/api/creator/posts/${data.id}/`) 
      .then(function(res) { 
        setDeleted(true); 
        setIsAtLeastOneDeleted(true)  
        console.log('Post deleted successfully');}) 
      .catch(err => { alert("An error occurred while deleting the post"); 
          console.error(err); }); } }
  const [isLiked, setIsLiked] = useState(data.is_liked);      
  const [likes, setLikes] = useState(data.likes);      
  const handleLikeClick = ()=>{
    api.put(`/api/posts/report_like/${data.id}/`)
    .then(res=>{
      setIsLiked(!isLiked);
      setLikes(res.data.likes_count)
    })
    .catch(err=>{console.log(err)})
    // setLikes
  }
  const [isReported, setIsReported] = useState(data.is_reported);
  const handleReportClick = ()=>{
    api.post(`/api/posts/report_like/${data.id}/`)
    .then(res=>{
      // setIsReported(!isLiked);
      console.log('reported!')
      setIsReported(true);
    })
    .catch(err=>{console.log(err)})
  }    
   // open an image on the full screen
   const [open, setOpen] = useState(false);
  // if post is locked
  
  return (
    !deleted?(
    <div className='post' style={{visibility:deleted?"hidden":"visible"}}>
      <div className='post_top_part'>
      <div className='post_top_left'>{data.title}</div>
      <div className='post_top_right'>
      {!locked&&<IconButton onClick={()=>{setShowList(!showList)}}><MoreHorizIcon/></IconButton>}
      {showList&&<Box className="post_list" sx={{ width: '100%', maxWidth: 200, boxShadow:3, bgcolor: 'background.paper' }}>
      <nav aria-label="main mailbox folders">
        <List>
        {!myPage &&<ListItem disablePadding>
            <ListItemButton disabled={isReported} onClick={handleReportClick}>
              <ListItemIcon>
                <ReportIcon />
              </ListItemIcon>
              <ListItemText primary="Report" />
            </ListItemButton>
          </ListItem>}
          {myPage&&<ListItem disablePadding>
            <ListItemButton onClick={()=>{navigate(`/post/edit/${data.id}/`)}}>
              <ListItemIcon>
                <EditIcon />
              </ListItemIcon>
              <ListItemText primary="Edit" />
            </ListItemButton>
          </ListItem>}
          {myPage&&<ListItem disablePadding>
            <ListItemButton onClick={deletePost}>
              <ListItemIcon>
                <DeleteIcon />
              </ListItemIcon>
              <ListItemText primary="Delete" />
            </ListItemButton>
          </ListItem>}
        </List>
      </nav>
      </Box>}
      </div>
      </div>
      <div className='post_body'>{data.body}</div>
      {!locked&&<img 
      className='post_img' 
      src={data.image}
      onClick={() => setOpen(true)}   
      />}
      {locked&&(data.image && 
      <img 
      className='post_img' 
      src={import.meta.env.VITE_API_URL + data.image}
      alt='locked image'
      />)}
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <img 
          src={data.image} 
          alt="Full View" 
          style={{ width: '100%', height: 'auto' }} 
          onClick={() => setOpen(false)}
        />
      </Dialog>
      <Divider sx={{margin: "10px 15px"}}/>
      <div className='post_info'>
      <div className='post_info_left_side'>
      {!locked&&
      <IconButton onClick={handleLikeClick}>
          {isLiked
          ?<FavoriteIcon sx={{color: 'red'}} fontSize="small"/>
          :<FavoriteBorderIcon fontSize="small"/>
          }
          <div className='post_likes'>{likes}</div>
        </IconButton>}

      </div>
      <div className='post_info_right_side'>
        {formattedDateTime}
      </div>
           
      </div>
    {isReported&&<Alert severity="warning">Thanks for your feedback</Alert>
    }  
    </div>
  )
  :<Alert variant="filled" severity="success">
  You successfully deleted the post
</Alert>
  )
}

export default Post
