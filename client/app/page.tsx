"use client"

import type React from "react"
import { useState } from "react";
 
import Sidebar from "@/components/Sidebar"
import Sent from "@/components/Sent";
import Inbox from "@/components/Inbox";
import Draft from "@/components/Draft";
import Compose from "@/components/Compose"

export const from = `${process.env.FROM}@${process.env.FROM}.com`
export const backendURL = process.env.API_URL

const Send = async (to: string, subject: string, body: string, type: string): Promise<void> => {
	if (!body) {
		body = " "
	}

	if (!subject) {
		subject = " "
	}

	const response = await fetch(`${backendURL}api/add`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			from: from,
			to: to,
			subject: subject,
			body: body,
			type: type
		})
	});
	
	if (!response.ok) {
		console.error("Failed to send:", await response.text());
	} else {
		console.log(response)
	}
};

export default function Home() {
	const [tab, setTab] = useState("inbox")

	let selectedTab = <Inbox />
	if (tab == "inbox") selectedTab = <Inbox />
	else if (tab == "sent") selectedTab = <Sent />
	else if (tab == "draft") selectedTab = <Draft />
	else if (tab == "compose") selectedTab = <Compose onBack={Send} clickBack={setTab}/>

	return (
		<main className="flex h-screen">
			<Sidebar onTabSelect={setTab}/>
			<div className="flex-1 p-8">
				{selectedTab}
			</div>
		</main>
	)
}
