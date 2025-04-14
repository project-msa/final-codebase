import mongoose from 'mongoose' 

export const connectDB = (url) => {
    try {
        mongoose.connect(url).then(() => {
            console.log(`Connected to MongoDB successfully!`)
        })
    } catch (error) {
        console.error(`Error connecting to MongoDB`, error)
    }
}