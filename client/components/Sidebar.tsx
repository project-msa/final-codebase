type Props = {
	onTabSelect: (tab: String) => void
}

const Sidebar = ({ onTabSelect }: Props) => {
  return (
		<aside className="w-64 p-6">
			<h2 className="text-2xl font-bold mb-6">Mail Client</h2>
			<nav>
				<button onClick={() => onTabSelect("inbox")} className="block text-left w-full py-2">
					Inbox
				</button>
				<button onClick={() => onTabSelect("sent")} className="block text-left w-full py-2">
					Sent
				</button>
				<button onClick={() => onTabSelect("draft")} className="block text-left w-full py-2">
					Draft
				</button>
				<button onClick={() => onTabSelect("compose")} className="block text-left w-full py-2">
					Compose
				</button>
			</nav>
		</aside>
  	)
}

export default Sidebar

