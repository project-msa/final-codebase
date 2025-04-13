import { Email } from "../models/email.js";

const SMTPClientURL = `http://${process.env.SERVER_IP}:${process.env.FLASK_PORT}/send`

export const addEmail = async (req, res) => {
    try {
        const { from, to, subject, body, type } = req.body;

        if (!from || !to || !subject) {
            return res.status(500).json({
                error: "Either the 'from', 'to' or the 'subject' field is empty"
            })
        }        

        const time = Math.floor(Date.now() / 1000)

        const entry = new Email({
            type: type,
            from: from,
            to: to,
            subject: subject,
            body: body,
            time: time,
            read: false,
            starred: false
        })

        await entry.save()

        const response = await fetch(SMTPClientURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"   
            }, 
            body: JSON.stringify({
                from: from,
                to: to,
                subject: subject,
                body: body
            })
        })

        console.log(`Email added to the sent emails ${response}`)
        return res.status(200).json({
            message: `Email has been sent successfully: ${response}`
        })

    } catch (error) {
        console.error(`Error while sending email: `, error)
        return res.status(500).json({
            error: `Internal Server Error`
        })
    }
}

export const modifyEmail = async (req, res) => {

}

export const fetchEmail = async (req, res) => {
    const type = req.params.type

    try {
        const emails = await Email.find({ type: type });
        return res.json(emails);

    } catch (err) {
        return res.status(500).json({ error: 'Server error', details: err });
    }
}
