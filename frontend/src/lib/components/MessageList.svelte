<script lang="ts">
	import { onMount, afterUpdate } from 'svelte';
	import { marked } from 'marked';
	import type { Message, StreamEvent, ToolCallEvent, ToolResultEvent } from '$lib/types';
	import ToolCall from './ToolCall.svelte';

	export let messages: Message[] = [];
	export let events: StreamEvent[] = [];

	let container: HTMLDivElement;
	let autoScroll = true;

	// Configure marked for better rendering
	marked.setOptions({
		breaks: true,
		gfm: true
	});

	// Auto-scroll to bottom when new messages arrive
	afterUpdate(() => {
		if (autoScroll && container) {
			container.scrollTop = container.scrollHeight;
		}
	});

	// Check if user has scrolled up (disable auto-scroll)
	function handleScroll() {
		if (!container) return;

		const { scrollTop, scrollHeight, clientHeight } = container;
		const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;

		autoScroll = isAtBottom;
	}

	// Group tool events by tool_call_id
	function getToolEvents(): Array<{ call: ToolCallEvent; result?: ToolResultEvent }> {
		const toolCalls = events.filter((e) => e.type === 'tool_call') as ToolCallEvent[];
		const toolResults = events.filter((e) => e.type === 'tool_result') as ToolResultEvent[];

		return toolCalls.map((call) => {
			const result = toolResults.find((r) => r.data.tool_call_id === call.data.tool_call_id);
			return { call, result };
		});
	}

	// Get current step event
	function getCurrentStep(): string | null {
		const stepEvents = events.filter((e) => e.type === 'step');
		if (stepEvents.length === 0) return null;

		const latest = stepEvents[stepEvents.length - 1];
		return (latest as any).data.friendly_name || null;
	}

	// Check if agent is executing
	$: isExecuting = events.some((e) => e.type === 'start') && !events.some((e) => e.type === 'complete' || e.type === 'error');
	$: toolEvents = getToolEvents();
	$: currentStep = getCurrentStep();
</script>

<div
	bind:this={container}
	on:scroll={handleScroll}
	class="flex-1 overflow-y-auto p-4 space-y-4"
>
	{#if messages.length === 0 && !isExecuting}
		<!-- Empty state -->
		<div class="flex flex-col items-center justify-center h-full text-center">
			<div class="text-6xl mb-4">💰</div>
			<h2 class="text-2xl font-bold mb-2">Welcome to Finance Agent!</h2>
			<p class="text-base-content/60 max-w-md">
				I can help you with portfolio analysis, stock research, retirement planning, and more.
				Ask me anything about your finances!
			</p>

			<!-- Example prompts -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6 max-w-2xl">
				<div class="card bg-base-200 shadow-sm hover:shadow-md transition-shadow">
					<div class="card-body p-4">
						<div class="text-2xl mb-2">📊</div>
						<p class="text-sm font-medium">Calculate my portfolio value</p>
					</div>
				</div>
				<div class="card bg-base-200 shadow-sm hover:shadow-md transition-shadow">
					<div class="card-body p-4">
						<div class="text-2xl mb-2">🔍</div>
						<p class="text-sm font-medium">Research NVDA stock</p>
					</div>
				</div>
				<div class="card bg-base-200 shadow-sm hover:shadow-md transition-shadow">
					<div class="card-body p-4">
						<div class="text-2xl mb-2">🎯</div>
						<p class="text-sm font-medium">Analyze my cash flow</p>
					</div>
				</div>
				<div class="card bg-base-200 shadow-sm hover:shadow-md transition-shadow">
					<div class="card-body p-4">
						<div class="text-2xl mb-2">📈</div>
						<p class="text-sm font-medium">Check my retirement progress</p>
					</div>
				</div>
			</div>
		</div>
	{:else}
		<!-- Messages -->
		{#each messages as message (message.id)}
			<div class="flex gap-3" class:justify-end={message.role === 'user'}>
				<!-- Avatar -->
				{#if message.role !== 'user'}
					<div class="avatar placeholder">
						<div class="bg-primary text-primary-content rounded-full w-8 h-8">
							<span class="text-lg">🤖</span>
						</div>
					</div>
				{/if}

				<!-- Message Content -->
				<div
					class="max-w-3xl"
					class:w-full={message.role === 'assistant'}
				>
					{#if message.role === 'user'}
						<!-- User message -->
						<div class="chat chat-end">
							<div class="chat-bubble chat-bubble-primary">
								{message.content}
							</div>
						</div>
					{:else if message.role === 'assistant'}
						<!-- Assistant message -->
						<div class="prose max-w-none">
							<div class="card bg-base-100 border border-base-300">
								<div class="card-body">
									<div class="markdown">
										{@html marked(message.content)}
									</div>
								</div>
							</div>
						</div>
					{:else if message.role === 'system'}
						<!-- System message -->
						<div class="alert alert-info">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							<span class="text-sm">{message.content}</span>
						</div>
					{/if}
				</div>

				<!-- User Avatar -->
				{#if message.role === 'user'}
					<div class="avatar placeholder">
						<div class="bg-neutral text-neutral-content rounded-full w-8 h-8">
							<span>👤</span>
						</div>
					</div>
				{/if}
			</div>
		{/each}

		<!-- Live Tool Calls -->
		{#if toolEvents.length > 0}
			<div class="space-y-2">
				<div class="text-sm font-semibold text-base-content/70 mb-2">
					🔧 Tool Executions
				</div>
				{#each toolEvents as { call, result } (call.data.tool_call_id)}
					<ToolCall toolCall={call} toolResult={result} isSubagent={call.data.is_subagent} />
				{/each}
			</div>
		{/if}

		<!-- Current Step Indicator -->
		{#if isExecuting && currentStep}
			<div class="flex items-center gap-2 text-sm text-base-content/70">
				<span class="loading loading-dots loading-sm"></span>
				<span>{currentStep}</span>
			</div>
		{/if}

		<!-- Typing Indicator -->
		{#if isExecuting}
			<div class="flex gap-3">
				<div class="avatar placeholder">
					<div class="bg-primary text-primary-content rounded-full w-8 h-8">
						<span class="text-lg">🤖</span>
					</div>
				</div>
				<div class="chat-bubble bg-base-200">
					<div class="flex gap-1">
						<span class="typing-dot w-2 h-2 bg-base-content/50 rounded-full"></span>
						<span class="typing-dot w-2 h-2 bg-base-content/50 rounded-full"></span>
						<span class="typing-dot w-2 h-2 bg-base-content/50 rounded-full"></span>
					</div>
				</div>
			</div>
		{/if}
	{/if}

	<!-- Scroll to bottom button -->
	{#if !autoScroll}
		<button
			class="btn btn-circle btn-sm btn-primary fixed bottom-24 right-8 shadow-lg"
			on:click={() => {
				autoScroll = true;
				container.scrollTop = container.scrollHeight;
			}}
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M19 14l-7 7m0 0l-7-7m7 7V3"
				/>
			</svg>
		</button>
	{/if}
</div>
