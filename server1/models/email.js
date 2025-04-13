import mongoose from "mongoose";

const emailSchema = new mongoose.Schema({
    type: String,
    from: String,
    to: String,
    subject: String,
    body: String,
    time: Number,
    read: Boolean,
    starred: Boolean
})

export const Email = mongoose.model('Email', emailSchema)