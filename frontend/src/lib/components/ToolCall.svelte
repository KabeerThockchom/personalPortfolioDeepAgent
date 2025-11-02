<script lang="ts">
	import type { ToolCallEvent, ToolResultEvent } from '$lib/types';

	export let toolCall: ToolCallEvent;
	export let toolResult: ToolResultEvent | undefined = undefined;
	export let isSubagent = false;

	let expanded = false;

	function getToolIcon(toolName: string): string {
		if (toolName === 'task') return '🚀';
		if (toolName.startsWith('get_stock') || toolName.includes('quote')) return '📊';
		if (toolName.startsWith('web_search')) return '🔍';
		if (toolName.startsWith('calculate')) return '🧮';
		if (toolName.startsWith('analyze')) return '📈';
		if (toolName.includes('file')) return '📁';
		if (toolName === 'write_todos') return '📋';
		return '🔧';
	}

	function formatValue(value: any, maxLength = 100): string {
		if (value === null || value === undefined) return 'null';

		const str = typeof value === 'string' ? value : JSON.stringify(value, null, 2);

		if (str.length <= maxLength) return str;
		return str.slice(0, maxLength) + '...';
	}

	function formatResult(result: any): { type: string; content: string } {
		if (typeof result === 'string') {
			try {
				const parsed = JSON.parse(result);
				return formatResult(parsed);
			} catch {
				return { type: 'text', content: result };
			}
		}

		if (typeof result === 'object' && result !== null) {
			// Check for common patterns
			if (result.success !== undefined) {
				return { type: 'status', content: JSON.stringify(result, null, 2) };
			}
			if (result.price || result.symbol) {
				return { type: 'stock', content: JSON.stringify(result, null, 2) };
			}
			if (result.data) {
				return { type: 'data', content: JSON.stringify(result, null, 2) };
			}
			return { type: 'json', content: JSON.stringify(result, null, 2) };
		}

		return { type: 'text', content: String(result) };
	}

	$: toolIcon = getToolIcon(toolCall.data.name);
	$: isTask = toolCall.data.name === 'task';
	$: resultFormatted = toolResult ? formatResult(toolResult.data.result) : null;
</script>

<div class="collapse collapse-arrow bg-base-200 border border-base-300" class:ml-4={isSubagent}>
	<input type="checkbox" bind:checked={expanded} />

	<div class="collapse-title">
		<div class="flex items-center gap-3">
			<!-- Icon & Name -->
			<div class="flex items-center gap-2">
				<span class="text-lg">{toolIcon}</span>
				<span class="font-mono text-sm font-medium">{toolCall.data.name}</span>
			</div>

			<!-- Status Badge -->
			{#if !toolResult}
				<span class="badge badge-warning badge-sm gap-1">
					<span class="loading loading-spinner loading-xs"></span>
					Running
				</span>
			{:else if toolResult.data.success}
				<span class="badge badge-success badge-sm">✓ Success</span>
			{:else}
				<span class="badge badge-error badge-sm">✗ Failed</span>
			{/if}

			<!-- Subagent indicator -->
			{#if isSubagent}
				<span class="badge badge-info badge-xs">subagent</span>
			{/if}

			<!-- Task special handling -->
			{#if isTask && toolCall.data.args.subagent_type}
				<span class="badge badge-primary badge-sm">
					{toolCall.data.args.subagent_type}
				</span>
			{/if}
		</div>
	</div>

	<div class="collapse-content">
		<!-- Arguments -->
		<div class="mb-4">
			<div class="text-xs font-semibold text-base-content/70 mb-2">Arguments:</div>
			<div class="bg-base-300 rounded-lg p-3 text-xs font-mono overflow-x-auto">
				{#if Object.keys(toolCall.data.args).length === 0}
					<span class="text-base-content/50">No arguments</span>
				{:else}
					<pre class="whitespace-pre-wrap">{JSON.stringify(toolCall.data.args, null, 2)}</pre>
				{/if}
			</div>
		</div>

		<!-- Result -->
		{#if toolResult}
			<div>
				<div class="text-xs font-semibold text-base-content/70 mb-2">Result:</div>

				{#if toolResult.data.error}
					<!-- Error -->
					<div class="alert alert-error text-sm">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<span>{toolResult.data.error}</span>
					</div>
				{:else if resultFormatted}
					<!-- Success -->
					<div class="bg-base-300 rounded-lg p-3 overflow-x-auto">
						{#if resultFormatted.type === 'stock'}
							<!-- Special stock formatting -->
							<div class="text-sm space-y-1">
								{@html resultFormatted.content
									.replace(/"(\w+)":/g, '<span class="text-primary font-semibold">$1:</span>')
									.replace(/\n/g, '<br/>')}
							</div>
						{:else if resultFormatted.type === 'json'}
							<pre class="text-xs font-mono whitespace-pre-wrap">{resultFormatted.content}</pre>
						{:else}
							<pre class="text-sm whitespace-pre-wrap">{resultFormatted.content}</pre>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>