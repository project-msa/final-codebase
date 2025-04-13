import express from "express";
import {
    fetchEmail,
    addEmail,
    modifyEmail
} from '../controller/accessDB.js'

const router = express.Router()

router.get("/fetch/:type", fetchEmail)
router.post("/add", addEmail)
router.post("/modify", modifyEmail)

export default router