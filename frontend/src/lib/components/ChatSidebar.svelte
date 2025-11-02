<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { listChats, createChat, updateChat, deleteChat, searchChats } from '$lib/api';
	import type { Chat } from '$lib/types';

	// State
	let chats: Chat[] = [];
	let loading = true;
	let searchQuery = '';
	let showArchived = false;
	let error: string | null = null;

	// Get current chat ID from URL
	$: currentChatId = $page.params.id;

	// Load chats on mount
	onMount(async () => {
		await loadChats();
	});

	async function loadChats() {
		try {
			loading = true;
			error = null;
			const response = await listChats(showArchived);
			chats = response.chats;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load chats';
			console.error('Failed to load chats:', e);
		} finally {
			loading = false;
		}
	}

	async function handleNewChat() {
		try {
			const chat = await createChat(undefined, true);
			chats = [chat, ...chats];
			goto(`/chat/${chat.id}`);
		} catch (e) {
			console.error('Failed to create chat:', e);
			alert('Failed to create chat');
		}
	}

	async function handleSearch() {
		if (!searchQuery.trim()) {
			await loadChats();
			return;
		}

		try {
			loading = true;
			const response = await searchChats(searchQuery);
			chats = response.chats;
		} catch (e) {
			console.error('Failed to search:', e);
		} finally {
			loading = false;
		}
	}

	async function togglePin(chat: Chat) {
		try {
			await updateChat(chat.id, { pinned: !chat.pinned });
			await loadChats();
		} catch (e) {
			console.error('Failed to pin chat:', e);
		}
	}

	async function handleDelete(chat: Chat) {
		if (!confirm('Are you sure you want to delete this chat?')) return;

		try {
			await deleteChat(chat.id);
			chats = chats.filter((c) => c.id !== chat.id);

			if (currentChatId === chat.id) {
				goto('/');
			}
		} catch (e) {
			console.error('Failed to delete chat:', e);
			alert('Failed to delete chat');
		}
	}

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);

		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		if (diffDays < 7) return `${diffDays}d ago`;

		return date.toLocaleDateString();
	}
</script>

<div class="flex flex-col h-screen bg-base-200 border-r border-base-300 w-80">
	<!-- Header -->
	<div class="p-4 border-b border-base-300">
		<div class="flex items-center justify-between mb-3">
			<h1 class="text-xl font-bold flex items-center gap-2">
				<span class="text-2xl">💰</span>
				Finance Agent
			</h1>
		</div>

		<!-- New Chat Button -->
		<button class="btn btn-primary btn-block gap-2" on:click={handleNewChat}>
			<svg
				class="w-5 h-5"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 4v16m8-8H4"
				/>
			</svg>
			New Chat
		</button>

		<!-- Search -->
		<div class="mt-3">
			<div class="join w-full">
				<input
					type="text"
					class="input input-bordered input-sm join-item flex-1"
					placeholder="Search chats..."
					bind:value={searchQuery}
					on:keydown={(e) => e.key === 'Enter' && handleSearch()}
				/>
				<button class="btn btn-sm join-item" on:click={handleSearch}>
					<svg
						class="w-4 h-4"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
				</button>
			</div>
		</div>

		<!-- Toggle Archived -->
		<label class="label cursor-pointer justify-start gap-2 mt-2">
			<input
				type="checkbox"
				class="toggle toggle-sm"
				bind:checked={showArchived}
				on:change={loadChats}
			/>
			<span class="label-text text-xs">Show archived</span>
		</label>
	</div>

	<!-- Chat List -->
	<div class="flex-1 overflow-y-auto">
		{#if loading}
			<div class="flex items-center justify-center h-32">
				<span class="loading loading-spinner loading-md"></span>
			</div>
		{:else if error}
			<div class="p-4 text-error text-sm">
				{error}
				<button class="btn btn-xs btn-ghost mt-2" on:click={loadChats}>Retry</button>
			</div>
		{:else if chats.length === 0}
			<div class="p-4 text-center text-base-content/60 text-sm">
				{searchQuery ? 'No chats found' : 'No chats yet. Create one to get started!'}
			</div>
		{:else}
			<div class="menu p-2 gap-1">
				{#each chats as chat (chat.id)}
					<div class="relative group">
						<a
							href="/chat/{chat.id}"
							class="flex flex-col gap-1 p-3 rounded-lg hover:bg-base-300 transition-colors {currentChatId ===
							chat.id
								? 'bg-primary/10 border border-primary/20'
								: 'bg-base-100'}"
						>
							<!-- Title & Pin -->
							<div class="flex items-start justify-between gap-2">
								<span class="font-medium text-sm line-clamp-1 flex-1">
									{chat.title}
								</span>
								{#if chat.pinned}
									<svg
										class="w-4 h-4 text-warning flex-shrink-0"
										fill="currentColor"
										viewBox="0 0 20 20"
									>
										<path
											d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6z"
										/>
									</svg>
								{/if}
							</div>

							<!-- Preview -->
							{#if chat.preview}
								<p class="text-xs text-base-content/60 line-clamp-2">
									{chat.preview}
								</p>
							{/if}

							<!-- Meta -->
							<div class="flex items-center justify-between text-xs text-base-content/50">
								<span>{chat.message_count} messages</span>
								<span>{formatDate(chat.updated_at)}</span>
							</div>
						</a>

						<!-- Actions (show on hover) -->
						<div
							class="absolute top-2 right-2 hidden group-hover:flex gap-1 bg-base-200 rounded-lg p-1 shadow-lg"
						>
							<button
								class="btn btn-xs btn-ghost"
								title={chat.pinned ? 'Unpin' : 'Pin'}
								on:click={(e) => {
									e.preventDefault();
									togglePin(chat);
								}}
							>
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
									/>
								</svg>
							</button>

							<button
								class="btn btn-xs btn-ghost text-error"
								title="Delete"
								on:click={(e) => {
									e.preventDefault();
									handleDelete(chat);
								}}
							>
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
									/>
								</svg>
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Footer -->
	<div class="p-4 border-t border-base-300">
		<div class="flex items-center justify-between text-xs text-base-content/60">
			<span>{chats.length} chats</span>
			<button class="link link-hover" on:click={loadChats}>Refresh</button>
		</div>
	</div>
</div>
