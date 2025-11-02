<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let disabled = false;
	export let placeholder = 'Ask about your finances...';

	let input = '';
	let textarea: HTMLTextAreaElement;

	const dispatch = createEventDispatcher<{ send: string }>();

	function handleSubmit() {
		const message = input.trim();
		if (!message || disabled) return;

		dispatch('send', message);
		input = '';

		// Reset textarea height
		if (textarea) {
			textarea.style.height = 'auto';
		}
	}

	function handleKeyDown(e: KeyboardEvent) {
		// Submit on Enter (without Shift)
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}

	function autoResize() {
		if (!textarea) return;

		textarea.style.height = 'auto';
		const newHeight = Math.min(textarea.scrollHeight, 200); // Max 200px
		textarea.style.height = `${newHeight}px`;
	}
</script>

<div class="border-t border-base-300 bg-base-100 p-4">
	<div class="max-w-4xl mx-auto">
		<div class="flex gap-2 items-end">
			<!-- Input -->
			<div class="flex-1 relative">
				<textarea
					bind:this={textarea}
					bind:value={input}
					on:input={autoResize}
					on:keydown={handleKeyDown}
					{placeholder}
					{disabled}
					rows="1"
					class="textarea textarea-bordered w-full resize-none overflow-y-auto"
					class:opacity-50={disabled}
					style="min-height: 48px; max-height: 200px;"
				/>

				<!-- Character count (optional) -->
				{#if input.length > 0}
					<div class="absolute bottom-2 right-2 text-xs text-base-content/40">
						{input.length}
					</div>
				{/if}
			</div>

			<!-- Send Button -->
			<button
				class="btn btn-primary btn-square"
				on:click={handleSubmit}
				{disabled}
				title="Send message (Enter)"
			>
				{#if disabled}
					<span class="loading loading-spinner loading-sm"></span>
				{:else}
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
							d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
						/>
					</svg>
				{/if}
			</button>
		</div>

		<!-- Hints -->
		<div class="text-xs text-base-content/50 mt-2 flex items-center justify-between">
			<span>
				<kbd class="kbd kbd-xs">Enter</kbd> to send, <kbd class="kbd kbd-xs">Shift</kbd> + <kbd class="kbd kbd-xs">Enter</kbd> for new line
			</span>
			{#if disabled}
				<span class="text-warning">Agent is thinking...</span>
			{/if}
		</div>
	</div>
</div>
