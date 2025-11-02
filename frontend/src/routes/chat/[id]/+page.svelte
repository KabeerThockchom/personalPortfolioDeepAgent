<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { getChat } from '$lib/api';
	import { wsManager } from '$lib/websocket';
	import type { Message, Todo, StreamEvent, ApprovalRequestEvent } from '$lib/types';
	import ChatSidebar from '$lib/components/ChatSidebar.svelte';
	import MessageList from '$lib/components/MessageList.svelte';
	import MessageInput from '$lib/components/MessageInput.svelte';
	import ApprovalModal from '$lib/components/ApprovalModal.svelte';
	import TodoWidget from '$lib/components/TodoWidget.svelte';

	// State
	let messages: Message[] = [];
	let todos: Todo[] = [];
	let sessionId: string = '';
	let chatTitle: string = '';
	let loading = true;
	let error: string | null = null;

	// Approval modal state
	let approvalModalOpen = false;
	let pendingApprovalRequests: any[] = [];

	// WebSocket
	$: chatId = $page.params.id;
	$: wsStore = wsManager.getOrCreate(chatId);
	$: wsState = $wsStore;
	$: events = $wsState.events;
	$: isExecuting = $wsState.isExecuting;

	// Load chat history
	onMount(async () => {
		await loadChat();
	});

	// Cleanup WebSocket on destroy
	onDestroy(() => {
		wsManager.disconnect(chatId);
	});

	async function loadChat() {
		try {
			loading = true;
			error = null;

			const chat = await getChat(chatId);
			messages = chat.messages;
			todos = chat.todos;
			sessionId = chat.session_id;
			chatTitle = chat.title;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load chat';
			console.error('Failed to load chat:', e);
		} finally {
			loading = false;
		}
	}

	function handleSendMessage(event: CustomEvent<string>) {
		const content = event.detail;

		// Add user message to UI immediately
		const userMessage: Message = {
			id: `temp-${Date.now()}`,
			role: 'user',
			content,
			created_at: new Date().toISOString()
		};
		messages = [...messages, userMessage];

		// Send to backend
		$wsStore.sendMessage(content, sessionId, true);
	}

	// Handle WebSocket events
	$: {
		// Process events
		if (events.length > 0) {
			const latestEvent = events[events.length - 1];

			// Update todos
			if (latestEvent.type === 'todo_update') {
				todos = latestEvent.data.todos;
			}

			// Handle completion
			if (latestEvent.type === 'complete') {
				const aiMessage = latestEvent.data.message;
				// Only add if not already in messages
				if (!messages.some((m) => m.id === aiMessage.id)) {
					messages = [...messages, aiMessage];
				}
			}

			// Handle approval request
			if (latestEvent.type === 'approval_request') {
				const approvalEvent = latestEvent as ApprovalRequestEvent;
				pendingApprovalRequests = approvalEvent.data.requests;
				approvalModalOpen = true;
			}

			// Handle errors
			if (latestEvent.type === 'error') {
				console.error('Agent error:', latestEvent.data.error);
				error = latestEvent.data.error;
			}
		}
	}

	function handleApprove(event: CustomEvent) {
		const decisions = event.detail;
		$wsStore.sendApprovalResponse(decisions);
		approvalModalOpen = false;
		pendingApprovalRequests = [];
	}

	function handleReject() {
		// Send all reject decisions
		const decisions = pendingApprovalRequests.map(() => ({ type: 'reject' as const }));
		$wsStore.sendApprovalResponse(decisions);
		approvalModalOpen = false;
		pendingApprovalRequests = [];
	}
</script>

<div class="flex h-screen">
	<!-- Sidebar -->
	<ChatSidebar />

	<!-- Main Chat Area -->
	<div class="flex-1 flex flex-col">
		<!-- Header -->
		<div class="border-b border-base-300 px-6 py-4 bg-base-100">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-xl font-bold">{chatTitle || 'Chat'}</h1>
					{#if sessionId}
						<p class="text-xs text-base-content/50">Session: {sessionId.slice(0, 8)}...</p>
					{/if}
				</div>

				<!-- Connection Status -->
				<div class="flex items-center gap-2">
					{#if $wsState.connected}
						<div class="badge badge-success badge-sm gap-1">
							<span class="w-2 h-2 rounded-full bg-success-content"></span>
							Connected
						</div>
					{:else}
						<div class="badge badge-error badge-sm gap-1">
							<span class="w-2 h-2 rounded-full bg-error-content"></span>
							Disconnected
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Content -->
		{#if loading}
			<div class="flex-1 flex items-center justify-center">
				<span class="loading loading-spinner loading-lg"></span>
			</div>
		{:else if error}
			<div class="flex-1 flex items-center justify-center">
				<div class="text-center">
					<div class="text-error text-xl mb-4">⚠️ {error}</div>
					<button class="btn btn-primary" on:click={loadChat}>Retry</button>
				</div>
			</div>
		{:else}
			<div class="flex-1 flex overflow-hidden">
				<!-- Messages -->
				<div class="flex-1 flex flex-col">
					<MessageList {messages} {events} />
					<MessageInput on:send={handleSendMessage} disabled={isExecuting} />
				</div>

				<!-- Right Sidebar (Todos) -->
				{#if todos.length > 0}
					<div class="w-80 border-l border-base-300 p-4 overflow-y-auto bg-base-100">
						<TodoWidget {todos} />
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Approval Modal -->
	<ApprovalModal
		bind:open={approvalModalOpen}
		requests={pendingApprovalRequests}
		on:approve={handleApprove}
		on:reject={handleReject}
	/>
</div>
