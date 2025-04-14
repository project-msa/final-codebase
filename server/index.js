import express, { json } from 'express'
import apiRoutes from './router/routes.js'
import { connectDB } from './controller/connect.js'
import cors from 'cors'

const app = express()

app.use(cors({
    origin: `http://${process.env.SERVER_IP}:${process.env.FRONTEND_PORT}`
}));
  
app.use(express.json())

const MongoDBUrl = "mongodb://localhost:27017/emails"
connectDB(MongoDBUrl)

app.use("/api", apiRoutes)

app.get('/', (req, res) => {
    res.json({
        "message": "hello"
    })
})

app.listen(process.env.EXPRESS_PORT, () => {
    console.log(`Listening on the port ${process.env.EXPRESS_PORT}`)
})
