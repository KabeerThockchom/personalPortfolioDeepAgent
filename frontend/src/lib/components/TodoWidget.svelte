<script lang="ts">
	import type { Todo } from '$lib/types';

	export let todos: Todo[] = [];

	function getStatusIcon(status: string): string {
		switch (status) {
			case 'completed':
				return '✓';
			case 'in_progress':
				return '⏳';
			default:
				return '○';
		}
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'completed':
				return 'text-success';
			case 'in_progress':
				return 'text-warning';
			default:
				return 'text-base-content/50';
		}
	}

	$: completedCount = todos.filter((t) => t.status === 'completed').length;
	$: progressPercent = todos.length > 0 ? (completedCount / todos.length) * 100 : 0;
</script>

{#if todos.length > 0}
	<div class="card bg-base-200 shadow-sm">
		<div class="card-body p-4">
			<h3 class="card-title text-sm">📋 Tasks</h3>

			<!-- Progress bar -->
			<div class="flex items-center gap-2 text-xs text-base-content/60 mb-2">
				<progress class="progress progress-primary w-full h-2" value={progressPercent} max="100"></progress>
				<span>{completedCount}/{todos.length}</span>
			</div>

			<!-- Todo list -->
			<ul class="space-y-1">
				{#each todos as todo (todo.content)}
					<li class="flex items-start gap-2 text-sm">
						<span class="{getStatusColor(todo.status)} flex-shrink-0 mt-0.5">
							{getStatusIcon(todo.status)}
						</span>
						<span class:line-through={todo.status === 'completed'} class:opacity-60={todo.status === 'completed'}>
							{todo.content}
						</span>
						{#if todo.status === 'in_progress'}
							<span class="loading loading-spinner loading-xs ml-auto"></span>
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	</div>
{/if}
