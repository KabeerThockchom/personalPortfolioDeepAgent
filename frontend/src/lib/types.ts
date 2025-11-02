/**
 * TypeScript types for the Finance Chat UI
 */

// ============================================================================
// Chat & Message Types
// ============================================================================

export interface Chat {
	id: string;
	title: string;
	created_at: string;
	updated_at: string;
	message_count: number;
	pinned: boolean;
	archived: boolean;
	preview?: string;
	session_id?: string;
}

export interface Message {
	id: string;
	role: 'user' | 'assistant' | 'system' | 'tool';
	content: string;
	created_at: string;
	tool_calls?: ToolCall[];
	tool_results?: ToolResult[];
	metadata?: Record<string, any>;
}

export interface ToolCall {
	id: string;
	name: string;
	args: Record<string, any>;
}

export interface ToolResult {
	tool_call_id: string;
	name: string;
	result: any;
	success: boolean;
	error?: string;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

export type EventType =
	| 'start'
	| 'step'
	| 'tool_call'
	| 'tool_result'
	| 'message'
	| 'todo_update'
	| 'file_update'
	| 'approval_request'
	| 'complete'
	| 'error';

export interface StreamEvent {
	type: EventType;
	data: any;
	timestamp: string;
}

export interface StartEvent extends StreamEvent {
	type: 'start';
	data: {
		chat_id: string;
		message_id: string;
	};
}

export interface StepEvent extends StreamEvent {
	type: 'step';
	data: {
		step_number: number;
		node_name: string;
		friendly_name: string;
		is_subagent: boolean;
		subagent_name?: string;
	};
}

export interface ToolCallEvent extends StreamEvent {
	type: 'tool_call';
	data: {
		tool_call_id: string;
		name: string;
		args: Record<string, any>;
		is_subagent: boolean;
	};
}

export interface ToolResultEvent extends StreamEvent {
	type: 'tool_result';
	data: {
		tool_call_id: string;
		name: string;
		result: any;
		success: boolean;
		error?: string;
		is_subagent: boolean;
	};
}

export interface TodoUpdateEvent extends StreamEvent {
	type: 'todo_update';
	data: {
		todos: Todo[];
	};
}

export interface FileUpdateEvent extends StreamEvent {
	type: 'file_update';
	data: {
		files: string[];
	};
}

export interface ApprovalRequestEvent extends StreamEvent {
	type: 'approval_request';
	data: {
		requests: ApprovalRequest[];
	};
}

export interface CompleteEvent extends StreamEvent {
	type: 'complete';
	data: {
		message: Message;
	};
}

export interface ErrorEvent extends StreamEvent {
	type: 'error';
	data: {
		error: string;
		details?: string;
	};
}

// ============================================================================
// Other Types
// ============================================================================

export interface Todo {
	content: string;
	status: 'pending' | 'in_progress' | 'completed';
	activeForm: string;
}

export interface ApprovalRequest {
	action_request: {
		name: string;
		args: Record<string, any>;
		description?: string;
	};
	review_config: {
		allowed_decisions: string[];
	};
}

export interface ApprovalDecision {
	type: 'approve' | 'reject' | 'edit';
	modified_args?: Record<string, any>;
}

export interface FileInfo {
	path: string;
	size: number;
	modified: string;
	is_directory: boolean;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ChatListResponse {
	chats: Chat[];
	total: number;
}

export interface ChatHistoryResponse {
	chat_id: string;
	title: string;
	session_id: string;
	messages: Message[];
	files: Record<string, string>;
	todos: Todo[];
}

export interface FileListResponse {
	files: FileInfo[];
	session_id: string;
}
