<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { ApprovalRequest, ApprovalDecision } from '$lib/types';

	export let requests: ApprovalRequest[] = [];
	export let open = false;

	const dispatch = createEventDispatcher<{ approve: ApprovalDecision[]; reject: void }>();

	let currentIndex = 0;
	let decisions: ApprovalDecision[] = [];

	$: currentRequest = requests[currentIndex];
	$: isLast = currentIndex === requests.length - 1;

	function handleApprove() {
		decisions[currentIndex] = { type: 'approve' };

		if (isLast) {
			dispatch('approve', decisions);
			reset();
		} else {
			currentIndex++;
		}
	}

	function handleReject() {
		decisions[currentIndex] = { type: 'reject' };

		if (isLast) {
			dispatch('approve', decisions);
			reset();
		} else {
			currentIndex++;
		}
	}

	function handleCancel() {
		dispatch('reject');
		reset();
	}

	function reset() {
		currentIndex = 0;
		decisions = [];
		open = false;
	}
</script>

{#if open && currentRequest}
	<div class="modal modal-open">
		<div class="modal-box max-w-2xl">
			<h3 class="font-bold text-lg flex items-center gap-2">
				⚠️ Approval Required
				{#if requests.length > 1}
					<span class="badge badge-sm">{currentIndex + 1} of {requests.length}</span>
				{/if}
			</h3>

			<div class="py-4">
				<!-- Tool name -->
				<div class="mb-3">
					<div class="text-sm font-semibold text-base-content/70 mb-1">Tool:</div>
					<div class="badge badge-primary">{currentRequest.action_request.name}</div>
				</div>

				<!-- Description -->
				{#if currentRequest.action_request.description}
					<div class="mb-3">
						<div class="text-sm font-semibold text-base-content/70 mb-1">Description:</div>
						<p class="text-sm">{currentRequest.action_request.description}</p>
					</div>
				{/if}

				<!-- Arguments -->
				<div>
					<div class="text-sm font-semibold text-base-content/70 mb-1">Arguments:</div>
					<div class="bg-base-200 rounded-lg p-3 max-h-60 overflow-y-auto">
						<pre class="text-xs">{JSON.stringify(currentRequest.action_request.args, null, 2)}</pre>
					</div>
				</div>
			</div>

			<div class="modal-action">
				<button class="btn btn-ghost" on:click={handleCancel}>Cancel All</button>
				<button class="btn btn-error" on:click={handleReject}>
					Reject{#if !isLast} & Continue{/if}
				</button>
				<button class="btn btn-success" on:click={handleApprove}>
					Approve{#if !isLast} & Continue{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
