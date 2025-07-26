import React, {useState, useEffect} from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'
import { useNavigate } from 'react-router-dom'
import ProfileNotSubscribed from '../components/ProfileNotSubscribed'
import ProfileSubscribed from '../components/ProfileSubscribed'
import Creator from '../components/Creator'
import NotCreator from '../components/NotCreator'
import NotCreatorMypage from '../components/NotCreatorMypage'



function Profile() {
    const {username} = useParams()
    const baseURLback = import.meta.env.VITE_API_URL
    const [loading, setLoading] = useState(true)
    const [data, setData] = useState({})
    const navigate =  useNavigate()
    useEffect(()=>{
        setLoading(true)
        api.get(`/api/profile/${username}/`)
        .then(res=>{
            setData(res.data)
            console.log(res.data)
            //   src={data.profile.background_image || defaultImageUrl}

        })
        .catch(err=>{
            console.log(err)
            navigate("/404")
        })
        .finally(()=>{setLoading(false)})
    },[username])
    return (
        <div>
            {loading?<p>Loading data...</p>:
            <div>
                <div className='prof_top_part'>
                <img height={'250px'} width={"100%"} alt='platform background picture or profile bg pic(later on)' 
                src={baseURLback + data.background_image}
                />
                </div>
                {data.profile.is_creator
                ?
                <div>
                {/* MAIN PAGE OF A CREATOR AFTER LOADING */}
                   {data.my_page?(<Creator data={data}/>):(
                    data.is_subscribed?<ProfileSubscribed data={data}/>:<ProfileNotSubscribed data={data}/>
                   )} 
                </div>
                     
                :(data.my_page?(<NotCreatorMypage />):<NotCreator username={username} />)
                }
            </div>
            }
        </div>
    )}

export default Profile
