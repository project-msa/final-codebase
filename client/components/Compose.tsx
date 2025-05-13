"use client"

import { useState } from "react"
import { ArrowLeft, Send, Paperclip, X } from "lucide-react"
import { motion } from "framer-motion"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface ComposeProps {
	onBack: (to: string, subject: string, body: string, type: string) => Promise<void>,
	clickBack: (tab: String) => void
}
  
const Compose = ({ onBack, clickBack }: ComposeProps) => {
	const [to, setTo] = useState("")
	const [subject, setSubject] = useState("")
	const [body, setBody] = useState("")
	const [attachments, setAttachments] = useState<string[]>([])
	const [isSending, setIsSending] = useState(false)
	const [showModal, setShowModal] = useState(false)
	const [errorMessage, setErrorMessage] = useState("")

	// Email validation regex
	// Allows only lowercase letters, numbers, dots, underscores, hyphens before @
	// Requires exactly one @
	// Domain part must have at least one dot
	// Only lowercase letters, numbers, dots, hyphens allowed in domain
	const emailRegex = /^[a-z0-9._-]+@[a-z0-9.-]+\.[a-z]{2,}$/

	const validateEmail = (email: string): { isValid: boolean; message: string } => {
		if (!email.trim()) {
			return { isValid: false, message: "Email address is required" }
		}

		if (email.includes(" ")) {
			return { isValid: false, message: "Email address cannot contain spaces" }
		}

		// if (email !== email.toLowerCase()) {
		// 	return { isValid: false, message: "Email address must be lowercase" }
		// }

		if ((email.match(/@/g) || []).length !== 1) {
			return { isValid: false, message: "Email address must contain exactly one @ symbol" }
		}

		// if (!emailRegex.test(email)) {
		// 	return {
		// 		isValid: false,
		// 		message: "Invalid email format. Please use format: recipient@example.com with lowercase letters only",
		// 	}
		// }

		return { isValid: true, message: "" }
	}

	const handleSend = () => {
		if (!to) {
			alert("Please specify at least one recipient")
			return
		}

		const emailValidation = validateEmail(to)

		if (!emailValidation.isValid) {
			setErrorMessage(emailValidation.message)
			setShowModal(true)
			return
		}

		setIsSending(true)

		// Simulate sending email
		setTimeout(() => {
			onBack(to, subject, body, "Sent")
			console.log(to, subject, body)
			setIsSending(false)
			setTo("")
			setSubject("")
			setBody("")
			setAttachments([])
		}, 1500)
	}

	const handleAddAttachment = () => {
		// This would normally open a file picker
		// For demo purposes, we'll just add a fake attachment
		setAttachments([...attachments, `Attachment ${attachments.length + 1}.pdf`])
	}

	const handleRemoveAttachment = (index: number) => {
		setAttachments(attachments.filter((_, i) => i !== index))
	}

	const saveTheDraftEmail = () => {
		if (!to) {
			alert("Please specify at least one recipient")
			return
		}

		const emailValidation = validateEmail(to)

		if (!emailValidation.isValid) {
			setErrorMessage(emailValidation.message)
			setShowModal(true)
			return
		}

		if (to) {
			onBack(to, subject, body, "Draft")
			console.log(to, subject, body)
			setIsSending(false)
			setTo("")
			setSubject("")
			setBody("")
			setAttachments([])
		}
		clickBack("draft")
	}

	const handleEmailBlur = () => {
		if (to.trim() === "") return
	
		const emailValidation = validateEmail(to)
		if (!emailValidation.isValid) {
			setErrorMessage(emailValidation.message)
			setShowModal(true)
		}
	}
	
	return (
		<>
		<motion.div
			initial={{ opacity: 0 }}
			animate={{ opacity: 1 }}
			exit={{ opacity: 0 }}
			className="flex flex-col h-full border border-border rounded-lg overflow-hidden bg-card text-card-foreground"
		>
			<div className="flex items-center justify-between p-4 border-b border-border">
				<div className="flex items-center gap-2">
				<Button variant="ghost" onBlur={handleEmailBlur} onClick={saveTheDraftEmail} size="icon" className="hover:bg-secondary">
					<ArrowLeft className="h-5 w-5" />
					<span className="sr-only">Back</span>
				</Button>
				<h2 className="text-xl font-semibold text-foreground">New Message</h2>
				</div>
			</div>

			<div className="flex-1 p-4 flex flex-col gap-4 overflow-auto">
				<div className="space-y-2">
				<Label htmlFor="to">To</Label>
				<Input
					id="to"
					placeholder="recipient@example.com"
					value={to}
					onChange={(e) => setTo(e.target.value)}
					className="bg-background border-border focus-visible:ring-primary"
				/>
				</div>

				<div className="space-y-2">
				<Label htmlFor="subject">Subject</Label>
				<Input
					id="subject"
					placeholder="Subject"
					value={subject}
					onChange={(e) => setSubject(e.target.value)}
					className="bg-background border-border focus-visible:ring-primary"
				/>
				</div>

				<div className="space-y-2 flex-1">
					<Label htmlFor="body">Message</Label>
					<Textarea
						id="body"
						placeholder="Write your message here..."
						value={body}
						onChange={(e) => setBody(e.target.value)}
						className="min-h-[200px] flex-1 bg-background border-border focus-visible:ring-primary resize-none h-full"
					/>
				</div>

				{attachments.length > 0 && (
					<div className="space-y-2">
						<Label>Attachments</Label>
						<div className="flex flex-wrap gap-2">
						{attachments.map((attachment, index) => (
							<div key={index} className="flex items-center gap-2 bg-secondary/50 px-3 py-1.5 rounded-md">
							<Paperclip className="h-4 w-4 text-muted-foreground" />
							<span className="text-sm">{attachment}</span>
							<Button
								variant="ghost"
								size="icon"
								className="h-5 w-5 rounded-full hover:bg-destructive/10 hover:text-destructive"
								onClick={() => handleRemoveAttachment(index)}
							>
								<X className="h-3 w-3" />
								<span className="sr-only">Remove</span>
							</Button>
							</div>
						))}
						</div>
					</div>
				)}

				<Button
					variant="outline"
					size="sm"
					className="w-fit border-border hover:bg-secondary hover:text-foreground"
					onClick={handleAddAttachment}
				>
					<Paperclip className="h-4 w-4 mr-2" />
					Attach File
				</Button>
			</div>

			<div className="p-4 border-t border-border flex justify-between">
				<Button variant="outline" onBlur={handleEmailBlur} onClick={saveTheDraftEmail} className="border-border hover:bg-secondary hover:text-foreground">
					<ArrowLeft className="h-4 w-4 mr-2" />
					Back
				</Button>
				<Button
				onBlur={handleEmailBlur}
				onClick={handleSend}
				disabled={isSending || !to || !subject || !body}
				className={isSending ? "opacity-70 cursor-not-allowed" : ""}
				>
				{isSending ? (
					"Sending..."
				) : (
					<>
					<Send className="h-4 w-4 mr-2" />
					Send Email
					</>
				)}
				</Button>
			</div>
		</motion.div>

		<Dialog open={showModal} onOpenChange={setShowModal}>
		<DialogContent className="sm:max-w-md bg-card border border-border">
		<DialogHeader className="flex justify-between items-start">
			<div>
			<DialogTitle className="text-foreground">Invalid Email Address</DialogTitle>
			<DialogDescription className="text-muted-foreground mt-1">
				Please correct the email address before sending.
			</DialogDescription>
			</div>
			<Button
			variant="ghost"
			size="icon"
			onClick={() => setShowModal(false)}
			className="h-8 w-8 p-0 rounded-full absolute right-4 top-4 hover:bg-secondary"
			>
			{/* <X className="h-4 w-4" /> */}
			<span className="sr-only">Close</span>
			</Button>
		</DialogHeader>
		<div className="p-1 text-foreground">
			<p className="mb-2">The following issue was detected:</p>
			<div className="bg-secondary/50 p-3 rounded-md text-sm">{errorMessage}</div>
			<p className="mt-4 text-sm text-muted-foreground">
			Email addresses should be in the format: recipient@example.com and contain only lowercase letters.
			</p>
		</div>
		</DialogContent>
		</Dialog>

		</>
	)
}

export default Compose

