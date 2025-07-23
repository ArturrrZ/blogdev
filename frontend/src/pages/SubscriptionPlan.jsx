import React, {useState, useEffect, useContext} from 'react'
import { useNavigate } from 'react-router-dom'
import { Unstable_NumberInput as BaseNumberInput } from '@mui/base/Unstable_NumberInput';
import { Button } from '@mui/material';
import { styled } from '@mui/system';
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import api from '../api';
import { AuthContext } from '../AuthContext';
import TextField from '@mui/material/TextField';


const NumberInput = React.forwardRef(function CustomNumberInput(props, ref) {
  return (
    <BaseNumberInput
      slots={{
        root: StyledInputRoot,
        input: StyledInput,
        incrementButton: StyledButton,
        decrementButton: StyledButton,
      }}
      slotProps={{
        incrementButton: {
          children: <AddIcon fontSize="small" />,
          className: 'increment',
          type: "button",
        },
        decrementButton: {
          children: <RemoveIcon fontSize="small" />,
          type: "button",
        },
      }}
      {...props}
      ref={ref}
    />
  );
});



const blue = {
  100: '#daecff',
  200: '#b6daff',
  300: '#66b2ff',
  400: '#3399ff',
  500: '#007fff',
  600: '#0072e5',
  700: '#0059B2',
  800: '#004c99',
};

const grey = {
  50: '#F3F6F9',
  100: '#E5EAF2',
  200: '#DAE2ED',
  300: '#C7D0DD',
  400: '#B0B8C4',
  500: '#9DA8B7',
  600: '#6B7A90',
  700: '#434D5B',
  800: '#303740',
  900: '#1C2025',
};

const StyledInputRoot = styled('div')(
  ({ theme }) => `
  font-family: 'IBM Plex Sans', sans-serif;
  font-weight: 400;
  color: ${theme.palette.mode === 'dark' ? grey[300] : grey[500]};
  display: flex;
  flex-flow: row nowrap;
  justify-content: center;
  align-items: center;
`,
);

const StyledInput = styled('input')(
  ({ theme }) => `
  font-size: 0.875rem;
  font-family: inherit;
  font-weight: 400;
  line-height: 1.375;
  color: ${theme.palette.mode === 'dark' ? grey[300] : grey[900]};
  background: ${theme.palette.mode === 'dark' ? grey[900] : '#fff'};
  border: 1px solid ${theme.palette.mode === 'dark' ? grey[700] : grey[200]};
  box-shadow: 0 2px 4px ${
    theme.palette.mode === 'dark' ? 'rgba(0,0,0, 0.5)' : 'rgba(0,0,0, 0.05)'
  };
  border-radius: 8px;
  margin: 0 8px;
  padding: 10px 12px;
  outline: 0;
  min-width: 0;
  width: 4rem;
  text-align: center;

  &:hover {
    border-color: ${blue[400]};
  }

  &:focus {
    border-color: ${blue[400]};
    box-shadow: 0 0 0 3px ${theme.palette.mode === 'dark' ? blue[700] : blue[200]};
  }

  &:focus-visible {
    outline: 0;
  }
`,
);

const StyledButton = styled('button')(
  ({ theme }) => `
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.875rem;
  box-sizing: border-box;
  line-height: 1.5;
  border: 1px solid;
  border-radius: 999px;
  border-color: ${theme.palette.mode === 'dark' ? grey[800] : grey[200]};
  background: ${theme.palette.mode === 'dark' ? grey[900] : grey[50]};
  color: ${theme.palette.mode === 'dark' ? grey[200] : grey[900]};
  width: 32px;
  height: 32px;
  display: flex;
  flex-flow: row nowrap;
  justify-content: center;
  align-items: center;
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 120ms;

  &:hover {
    cursor: pointer;
    background: ${theme.palette.mode === 'dark' ? blue[700] : blue[500]};
    border-color: ${theme.palette.mode === 'dark' ? blue[500] : blue[400]};
    color: ${grey[50]};
  }

  &:focus-visible {
    outline: 0;
  }

  &.increment {
    order: 1;
  }
`,
);

function SubscriptionPlan(props) {
    const navigate = useNavigate();
    const {creator ,setCreator, user} = useContext(AuthContext);
    const username = user;
    const [loading, setLoading] = React.useState(true);
    const [price, setPrice] = React.useState(1);
    const [greeting_message, setGreetingMessage] = React.useState("");
    function handleSubmit(e){
        e.preventDefault()
        api.post('/api/creator/become/', {
            price: price,
            greeting_message: greeting_message
        })
        .then(res=>{
            setCreator(true)
            window.location.reload()
          })
        .catch(err=>{
            // for some reason err
            console.log(err)
        })
    }
    useEffect(()=>{
      if (creator) {
        navigate(`/user/${username}`)
      }
      else {setLoading(false)}
    }, [])
    if (loading) {
      return <div>Loading...</div>
    }
  return (
    <div>
      <form onSubmit={handleSubmit} className='subscription_plan'>
      <p>Type desired price for the subscription in $</p>
      <NumberInput aria-label="Quantity Input" min={1} max={99} value={price} onChange={(e, val)=>{setPrice(val)}} />
      <TextField
        required
        name="greeting_message"
        id="outlined-basic"
        label="Greeting message"
        variant="outlined"
        multiline
        minRows={4}
        value={greeting_message}
        onChange={(e)=>{setGreetingMessage(e.target.value)}}
      />
      <Button variant="contained" type='submit'>Create a subscription plan</Button>
      </form>
    </div>
  )
}

export default SubscriptionPlan
