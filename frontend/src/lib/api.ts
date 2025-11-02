/**
 * REST API client for backend communication
 */

import type { Chat, ChatListResponse, ChatHistoryResponse, FileListResponse } from './types';

const API_BASE = 'http://localhost:8000/api';

// ============================================================================
// Chat API
// ============================================================================

export async function createChat(title?: string, loadPortfolio = true): Promise<Chat> {
	const response = await fetch(`${API_BASE}/chat/new`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ title, load_portfolio: loadPortfolio })
	});

	if (!response.ok) {
		throw new Error(`Failed to create chat: ${response.statusText}`);
	}

	return response.json();
}

export async function getChat(chatId: string): Promise<ChatHistoryResponse> {
	const response = await fetch(`${API_BASE}/chat/${chatId}`);

	if (!response.ok) {
		throw new Error(`Failed to get chat: ${response.statusText}`);
	}

	return response.json();
}

export async function updateChat(
	chatId: string,
	updates: { title?: string; pinned?: boolean; archived?: boolean }
): Promise<Chat> {
	const response = await fetch(`${API_BASE}/chat/${chatId}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(updates)
	});

	if (!response.ok) {
		throw new Error(`Failed to update chat: ${response.statusText}`);
	}

	return response.json();
}

export async function deleteChat(chatId: string): Promise<void> {
	const response = await fetch(`${API_BASE}/chat/${chatId}`, {
		method: 'DELETE'
	});

	if (!response.ok) {
		throw new Error(`Failed to delete chat: ${response.statusText}`);
	}
}

export async function listChats(
	archived = false,
	limit = 100,
	offset = 0
): Promise<ChatListResponse> {
	const params = new URLSearchParams({
		archived: String(archived),
		limit: String(limit),
		offset: String(offset)
	});

	const response = await fetch(`${API_BASE}/chat/?${params}`);

	if (!response.ok) {
		throw new Error(`Failed to list chats: ${response.statusText}`);
	}

	return response.json();
}

export async function searchChats(query: string, limit = 50): Promise<ChatListResponse> {
	const params = new URLSearchParams({ q: query, limit: String(limit) });

	const response = await fetch(`${API_BASE}/chat/search/?${params}`);

	if (!response.ok) {
		throw new Error(`Failed to search chats: ${response.statusText}`);
	}

	return response.json();
}

export async function clearChatMessages(chatId: string): Promise<void> {
	const response = await fetch(`${API_BASE}/chat/${chatId}/messages`, {
		method: 'DELETE'
	});

	if (!response.ok) {
		throw new Error(`Failed to clear messages: ${response.statusText}`);
	}
}

// ============================================================================
// File API
// ============================================================================

export async function listSessionFiles(sessionId: string): Promise<FileListResponse> {
	const response = await fetch(`${API_BASE}/files/${sessionId}`);

	if (!response.ok) {
		throw new Error(`Failed to list files: ${response.statusText}`);
	}

	return response.json();
}

export async function getFileContent(sessionId: string, path: string): Promise<string> {
	const params = new URLSearchParams({ path });
	const response = await fetch(`${API_BASE}/files/${sessionId}/content?${params}`);

	if (!response.ok) {
		throw new Error(`Failed to get file content: ${response.statusText}`);
	}

	const data = await response.json();
	return data.content;
}

export async function downloadFile(sessionId: string, path: string): Promise<void> {
	const params = new URLSearchParams({ path });
	const response = await fetch(`${API_BASE}/files/${sessionId}/download?${params}`);

	if (!response.ok) {
		throw new Error(`Failed to download file: ${response.statusText}`);
	}

	// Trigger download
	const blob = await response.blob();
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = path.split('/').pop() || 'download';
	document.body.appendChild(a);
	a.click();
	window.URL.revokeObjectURL(url);
	document.body.removeChild(a);
}

// ============================================================================
// Health Check
// ============================================================================

export async function checkHealth(): Promise<{ status: string }> {
	const response = await fetch('http://localhost:8000/health');

	if (!response.ok) {
		throw new Error('Backend is not responding');
	}

	return response.json();
}
