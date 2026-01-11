/**
 * WebSocket Hook for Real-Time Collaboration
 * Uses native WebSocket API (FastAPI WebSocket endpoint)
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
    type: string;
    [key: string]: any;
}

export function useWebSocket(modelId: string | null, userId?: string) {
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [activeUsers, setActiveUsers] = useState<string[]>([]);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const messageHandlers = useRef<Map<string, (message: WebSocketMessage) => void>>(new Map());
    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

    useEffect(() => {
        if (!modelId) return;

        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        // Handle both http and https URLs for WebSocket
        const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
        const wsBase = API_BASE_URL.replace(/^https?:\/\//, '');
        const wsUrl = `${wsProtocol}://${wsBase}/ws/${modelId}${userId ? `?user_id=${userId}` : ''}`;

        console.log('Connecting to WebSocket:', wsUrl);
        const newWs = new WebSocket(wsUrl);

        newWs.onopen = () => {
            console.log('WebSocket connected');
            setIsConnected(true);
            setWs(newWs);

            // Clear any reconnect timeout
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };

        newWs.onclose = () => {
            console.log('WebSocket disconnected');
            setIsConnected(false);
            setWs(null);

            // Attempt reconnection after 3 seconds
            reconnectTimeoutRef.current = setTimeout(() => {
                if (modelId) {
                    console.log('Attempting WebSocket reconnection...');
                }
            }, 3000);
        };

        newWs.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        newWs.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                setLastMessage(message);

                // Handle specific message types
                if (message.type === 'connected') {
                    setActiveUsers(message.active_users || []);
                }

                if (message.type === 'user_joined' || message.type === 'user_left') {
                    // Refresh active users list (would need to request or track)
                }

                if (message.type === 'edit_event') {
                    // Handle real-time edit events
                    console.log('Edit event from collaborator:', message);
                }

                if (message.type === 'position_update') {
                    // Handle node position updates
                    console.log('Position update from collaborator:', message);
                }

                if (message.type === 'sync_response') {
                    // Handle full model sync
                    console.log('Sync response received:', message);
                }

                // Call registered handlers
                const handler = messageHandlers.current.get(message.type);
                if (handler) {
                    handler(message);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        setWs(newWs);

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (newWs.readyState === WebSocket.OPEN || newWs.readyState === WebSocket.CONNECTING) {
                newWs.close();
            }
            setIsConnected(false);
        };
    }, [modelId, userId]);

    const sendMessage = useCallback(
        (type: string, data: any) => {
            if (ws && isConnected && ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(JSON.stringify({ type, ...data }));
                } catch (error) {
                    console.error('Error sending WebSocket message:', error);
                }
            }
        },
        [ws, isConnected]
    );

    const sendEditEvent = useCallback(
        (event: any) => {
            sendMessage('edit_event', { event });
        },
        [sendMessage]
    );

    const sendPositionUpdate = useCallback(
        (resourceId: string, position: { x: number; y: number }) => {
            sendMessage('position_update', { resource_id: resourceId, position });
        },
        [sendMessage]
    );

    const sendCursorUpdate = useCallback(
        (position: { x: number; y: number; type: 'diagram' | 'terraform' }) => {
            sendMessage('cursor_update', { position });
        },
        [sendMessage]
    );

    const requestSync = useCallback(() => {
        sendMessage('sync_request', {});
    }, [sendMessage]);

    const registerHandler = useCallback((type: string, handler: (message: WebSocketMessage) => void) => {
        messageHandlers.current.set(type, handler);
        return () => {
            messageHandlers.current.delete(type);
        };
    }, []);

    return {
        socket: ws,
        isConnected,
        activeUsers,
        lastMessage,
        sendMessage,
        sendEditEvent,
        sendPositionUpdate,
        sendCursorUpdate,
        requestSync,
        registerHandler,
    };
}
