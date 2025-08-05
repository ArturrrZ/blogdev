import React, {useEffect, useState} from 'react'
import Dialog from '@mui/material/Dialog';


function MediaPost(props) {
    const {data} = props
    if (!data.image) return null;
    const [locked, setLocked] = React.useState(false)
    useEffect(() => {
        if (data.title === 'Locked Content') {
          setLocked(true);
        }
      }, []);
    console.log(data)
    const [open, setOpen] = React.useState(false)
  return (
    <span >
    {!locked&&
      <img
      className='post_media_img' 
      src={data.image}
      onClick={() => setOpen(true)}
      width={'200px'} height={'200px'} 
      />}
      {locked&&  
      <img
            width={'200px'}
            height={'200px'} 
            className='post_media_img' 
            src={data.image}
            alt='locked image'
            />}
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
    </span>
  )
}

export default MediaPost
