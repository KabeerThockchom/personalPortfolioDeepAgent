/**
 * WebSocket store for real-time agent streaming
 */

import { writable, get } from 'svelte/store';
import type { StreamEvent, ApprovalDecision } from './types';

const WS_BASE = 'ws://localhost:8000/ws';

interface WebSocketState {
	connected: boolean;
	events: StreamEvent[];
	error: string | null;
	isExecuting: boolean;
}

// ============================================================================
// WebSocket Store
// ============================================================================

function createWebSocketStore(chatId: string) {
	const { subscribe, set, update } = writable<WebSocketState>({
		connected: false,
		events: [],
		error: null,
		isExecuting: false
	});

	let ws: WebSocket | null = null;
	let reconnectAttempts = 0;
	const maxReconnectAttempts = 5;

	// Connect to WebSocket
	function connect() {
		if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
			return; // Already connected or connecting
		}

		try {
			ws = new WebSocket(`${WS_BASE}/${chatId}`);

			ws.onopen = () => {
				console.log('✅ WebSocket connected');
				reconnectAttempts = 0;
				update((state) => ({ ...state, connected: true, error: null }));
			};

			ws.onmessage = (event) => {
				try {
					const data: StreamEvent = JSON.parse(event.data);

					update((state) => {
						// Track execution state
						let isExecuting = state.isExecuting;
						if (data.type === 'start') {
							isExecuting = true;
						} else if (data.type === 'complete' || data.type === 'error') {
							isExecuting = false;
						}

						return {
							...state,
							events: [...state.events, data],
							isExecuting
						};
					});
				} catch (error) {
					console.error('Failed to parse WebSocket message:', error);
				}
			};

			ws.onerror = (error) => {
				console.error('❌ WebSocket error:', error);
				update((state) => ({ ...state, error: 'Connection error' }));
			};

			ws.onclose = () => {
				console.log('🔌 WebSocket disconnected');
				update((state) => ({ ...state, connected: false }));

				// Attempt to reconnect
				if (reconnectAttempts < maxReconnectAttempts) {
					reconnectAttempts++;
					console.log(`Reconnecting... (attempt ${reconnectAttempts})`);
					setTimeout(connect, 2000 * reconnectAttempts);
				}
			};
		} catch (error) {
			console.error('Failed to create WebSocket:', error);
			update((state) => ({ ...state, error: 'Failed to connect' }));
		}
	}

	// Send message to agent
	function sendMessage(content: string, sessionId: string, enableHitl = true) {
		if (!ws || ws.readyState !== WebSocket.OPEN) {
			console.error('WebSocket is not connected');
			return;
		}

		ws.send(
			JSON.stringify({
				type: 'message',
				data: {
					content,
					session_id: sessionId,
					enable_hitl: enableHitl
				}
			})
		);
	}

	// Send approval response
	function sendApprovalResponse(decisions: ApprovalDecision[]) {
		if (!ws || ws.readyState !== WebSocket.OPEN) {
			console.error('WebSocket is not connected');
			return;
		}

		ws.send(
			JSON.stringify({
				type: 'approval_response',
				data: { decisions }
			})
		);
	}

	// Clear events
	function clearEvents() {
		update((state) => ({ ...state, events: [] }));
	}

	// Disconnect
	function disconnect() {
		if (ws) {
			ws.close();
			ws = null;
		}
		set({ connected: false, events: [], error: null, isExecuting: false });
	}

	// Auto-connect on creation
	connect();

	return {
		subscribe,
		sendMessage,
		sendApprovalResponse,
		clearEvents,
		disconnect,
		reconnect: connect
	};
}

// ============================================================================
// WebSocket Manager
// ============================================================================

class WebSocketManager {
	private stores: Map<string, ReturnType<typeof createWebSocketStore>> = new Map();

	getOrCreate(chatId: string) {
		if (!this.stores.has(chatId)) {
			this.stores.set(chatId, createWebSocketStore(chatId));
		}
		return this.stores.get(chatId)!;
	}

	disconnect(chatId: string) {
		const store = this.stores.get(chatId);
		if (store) {
			store.disconnect();
			this.stores.delete(chatId);
		}
	}

	disconnectAll() {
		this.stores.forEach((store) => store.disconnect());
		this.stores.clear();
	}
}

export const wsManager = new WebSocketManager();
