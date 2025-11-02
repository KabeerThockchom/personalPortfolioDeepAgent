<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { createChat } from '$lib/api';
	import ChatSidebar from '$lib/components/ChatSidebar.svelte';

	let creating = false;

	async function handleNewChat() {
		if (creating) return;

		try {
			creating = true;
			const chat = await createChat(undefined, true);
			goto(`/chat/${chat.id}`);
		} catch (e) {
			console.error('Failed to create chat:', e);
			alert('Failed to create chat');
		} finally {
			creating = false;
		}
	}
</script>

<div class="flex h-screen">
	<!-- Sidebar -->
	<ChatSidebar />

	<!-- Main Area -->
	<div class="flex-1 flex flex-col items-center justify-center bg-base-100 p-8">
		<div class="text-center max-w-2xl">
			<div class="text-8xl mb-6">💰</div>
			<h1 class="text-4xl font-bold mb-4">Personal Finance Deep Agent</h1>
			<p class="text-lg text-base-content/70 mb-8">
				Your AI-powered financial assistant with real-time market data, comprehensive analysis,
				and expert guidance.
			</p>

			<button
				class="btn btn-primary btn-lg gap-2"
				on:click={handleNewChat}
				disabled={creating}
			>
				{#if creating}
					<span class="loading loading-spinner"></span>
					Creating...
				{:else}
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
					Start New Chat
				{/if}
			</button>

			<!-- Features -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-12">
				<div class="card bg-base-200">
					<div class="card-body">
						<h3 class="card-title text-base">📊 Real-Time Market Data</h3>
						<p class="text-sm text-base-content/70">
							Access live stock quotes, company fundamentals, and market news via Yahoo Finance API
						</p>
					</div>
				</div>

				<div class="card bg-base-200">
					<div class="card-body">
						<h3 class="card-title text-base">🤖 Multi-Agent System</h3>
						<p class="text-sm text-base-content/70">
							8 specialized subagents for portfolio analysis, research, planning, and optimization
						</p>
					</div>
				</div>

				<div class="card bg-base-200">
					<div class="card-body">
						<h3 class="card-title text-base">✅ Human-in-the-Loop</h3>
						<p class="text-sm text-base-content/70">
							Agent asks for approval before making portfolio modifications or complex operations
						</p>
					</div>
				</div>

				<div class="card bg-base-200">
					<div class="card-body">
						<h3 class="card-title text-base">📈 Deep Analysis</h3>
						<p class="text-sm text-base-content/70">
							Portfolio valuation, retirement planning, tax optimization, risk assessment, and more
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
