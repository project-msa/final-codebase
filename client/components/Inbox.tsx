"use client"

import { useState, useEffect } from "react"
import { format } from "date-fns"
import { ArrowLeft, Star, StarOff, Trash2, Archive, Reply, ReplyAll, Forward } from "lucide-react"
import { AnimatePresence, motion } from "framer-motion"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

import { from, backendURL } from "@/app/page"

interface Email {
  id: string
  from: {
    name: string
    email: string
    avatar: string
  }
  to: string
  subject: string
  body: string
  timestamp: string
  read: boolean
  starred: boolean
}

let mockEmails: Email[] = []

const EmailItem = ({
  email,
  onClick,
}: {
  email: Email
  onClick: () => void
}) => {
  return (
    <div
      onClick={onClick}
      className={`p-4 border-b border-border cursor-pointer transition-colors hover:bg-secondary/50 group ${!email.read ? "bg-secondary/30" : ""}`}
    >
      <div className="flex items-center gap-3">
        <Avatar className="h-10 w-10 border border-border">
          <AvatarImage src={email.from.avatar} alt={email.from.name} />
          <AvatarFallback className="bg-secondary text-secondary-foreground">
            {email.from.name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-center">
            <h3 className={`text-sm truncate ${!email.read ? "font-semibold text-primary" : "text-foreground"}`}>
              {email.from.name}
            </h3>
            <span className="text-xs text-muted-foreground hidden group-hover:block">
              {format(new Date(parseInt(email.timestamp) * 1000).getTime(), "MMM d, h:mm a")}
            </span>
          </div>
          <p className={`text-sm truncate ${!email.read ? "text-foreground" : "text-muted-foreground"}`}>
            {email.subject}
          </p>
          <p className="text-xs text-muted-foreground truncate">{email.body.split("\n")[0]}</p>
        </div>
        <div className="text-xs text-muted-foreground whitespace-nowrap">{format(new Date(parseInt(email.timestamp) * 1000).getTime(), "MMM d")}</div>
        {email.starred && <Star className="h-4 w-4 fill-yellow-500 text-yellow-500 shrink-0" />}
      </div>
    </div>
  )
}

const EmailReader = ({
	email,
	onClose,
	onToggleStar,
}: {
	email: Email
	onClose: () => void
	onToggleStar: () => void
}) => {
  return (
    <div className="flex flex-col h-full bg-background">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={onClose} className="hover:bg-secondary">
            <ArrowLeft className="h-5 w-5" />
            <span className="sr-only">Back</span>
          </Button>
          <h2 className="text-xl font-semibold text-foreground">{email.subject}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={onToggleStar} className="hover:bg-secondary">
            {email.starred ? (
              <Star className="h-5 w-5 fill-yellow-500 text-yellow-500" />
            ) : (
              <StarOff className="h-5 w-5" />
            )}
            <span className="sr-only">{email.starred ? "Unstar" : "Star"}</span>
          </Button>
          <Button variant="ghost" size="icon" className="hover:bg-secondary">
            <Archive className="h-5 w-5" />
            <span className="sr-only">Archive</span>
          </Button>
          <Button variant="ghost" size="icon" className="hover:bg-secondary text-destructive hover:text-destructive">
            <Trash2 className="h-5 w-5" />
            <span className="sr-only">Delete</span>
          </Button>
        </div>
      </div>

      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 border border-border">
              <AvatarImage src={email.from.avatar} alt={email.from.name} />
              <AvatarFallback className="bg-secondary text-secondary-foreground">
                {email.from.name.charAt(0)}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-foreground">{email.from.name}</span>
                <span className="text-sm text-muted-foreground">&lt;{email.from.email}&gt;</span>
              </div>
              <div className="text-sm text-muted-foreground">To: {email.to}</div>
            </div>
          </div>
          <div className="text-sm text-muted-foreground">{format(new Date(parseInt(email.timestamp) * 1000).getTime(), "MMM d, yyyy h:mm a")}</div>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="whitespace-pre-wrap text-foreground">{email.body}</div>
      </ScrollArea>

      <div className="p-4 border-t border-border flex gap-2">
        <Button variant="outline" size="sm" className="border-border hover:bg-secondary hover:text-foreground">
          <Reply className="h-4 w-4 mr-2" />
          Reply
        </Button>
        <Button variant="outline" size="sm" className="border-border hover:bg-secondary hover:text-foreground">
          <ReplyAll className="h-4 w-4 mr-2" />
          Reply All
        </Button>
        <Button variant="outline" size="sm" className="border-border hover:bg-secondary hover:text-foreground">
          <Forward className="h-4 w-4 mr-2" />
          Forward
        </Button>
      </div>
    </div>
  )
}

const Inbox = () => {
  const [emails, setEmails] = useState<Email[]>(mockEmails)
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [isReading, setIsReading] = useState(false)

  const handleEmailClick = (email: Email) => {
    // Mark as read
    setEmails(emails.map((e) => (e.id === email.id ? { ...e, read: true } : e)))

    setSelectedEmail(email)
    setIsReading(true)
  }

  const handleClose = () => {
    setIsReading(false)
  }

  const handleToggleStar = () => {
    if (!selectedEmail) return

    // Toggle star status
    const updatedEmails = emails.map((email) =>
      email.id === selectedEmail.id ? { ...email, starred: !email.starred } : email,
    )

    setEmails(updatedEmails)
    setSelectedEmail({
      ...selectedEmail,
      starred: !selectedEmail.starred,
    })
  }

	useEffect(() => {
		// Polling function
		const pollServer = async () => {
			try {
				const response = await fetch(`${backendURL}api/fetch/Inbox`, {
					method: "GET",
					headers: {
					"Content-Type": "application/json"
					}
				});
				if (!response.ok) {
					throw new Error('Network response was not ok');
				}
				const data = await response.json();
		
				let new_inbox: Email[] = []
				for (let inbox = 0; inbox < data.length; inbox++) {
					let entry = data[inbox]
					let new_entry: Email = {
						"id": (inbox + 1).toString(),
						"from": {
							"name": entry.from.split('@')[0],
							"email": entry.from,
							"avatar": "/placeholder.svg?height=40&width=40"
						},
						"to": "Me",
						"subject": entry.subject,
						"body": entry.body,
						"timestamp": entry.time,
						"read": entry.read,
						"starred": entry.starred
					}
		
					new_inbox.push(new_entry)
				}
			
				const sorted_inbox = [...new_inbox].sort((a: Email, b: Email) => {
					const timeA = new Date(a.timestamp).getTime();
					const timeB = new Date(b.timestamp).getTime();
					return timeB - timeA;
				});
				
				mockEmails = sorted_inbox;
				setEmails(sorted_inbox);
			} catch (error) {
			console.error('Error fetching inbox emails:', error);
			}
		};
	
		// Initial fetch
		pollServer();
	
		// Set up polling interval (every 1 second)
		const intervalId = setInterval(pollServer, 1000);
	
		// Clean up interval on component unmount
		return () => clearInterval(intervalId);
	}, []);

  return (
    <div className="flex flex-col h-full border border-border rounded-lg overflow-hidden bg-card text-card-foreground">
      <AnimatePresence mode="wait">
        {isReading && selectedEmail ? (
          <motion.div
            key="reader"
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            transition={{ type: "tween", duration: 0.3 }}
            className="absolute inset-0 bg-background z-10 h-full"
          >
            <EmailReader email={selectedEmail} onClose={handleClose} onToggleStar={handleToggleStar} />
          </motion.div>
        ) : (
          <motion.div key="inbox" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="text-xl font-semibold text-foreground">Inbox</h2>
              <div className="text-sm text-muted-foreground">{emails.filter((e) => !e.read).length} unread</div>
            </div>
            <ScrollArea className="flex-1">
              <div className="divide-y divide-border">
                {emails.map((email) => (
                  <EmailItem key={email.id} email={email} onClick={() => handleEmailClick(email)} />
                ))}
              </div>
            </ScrollArea>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Inbox

