"""WebSocket connection manager with HITL event support."""

import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections and channels for real-time updates.

    Supports:
    - User-specific connections
    - Channel-based subscriptions
    - HITL event broadcasting
    - Automatic reconnection handling
    """

    def __init__(self):
        # user_id -> Set[WebSocket]
        self.user_connections: Dict[str, Set[WebSocket]] = {}

        # channel -> Set[user_id]
        self.channel_subscriptions: Dict[str, Set[str]] = {}

        # websocket -> user_id (reverse lookup)
        self.connection_users: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept WebSocket connection for a user.

        Args:
            websocket: WebSocket connection
            user_id: User ID to associate with this connection
        """
        await websocket.accept()

        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        # Add reverse lookup
        self.connection_users[websocket] = user_id

        # Auto-subscribe to user's personal notification channel
        await self.subscribe(user_id, [f"user:{user_id}:notifications"])

        logger.info(f"WebSocket connected: user_id={user_id}")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {
                "user_id": user_id,
                "timestamp": self._get_timestamp(),
            }
        })

    async def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket and clean up subscriptions.

        Args:
            websocket: WebSocket connection to disconnect
        """
        if websocket not in self.connection_users:
            return

        user_id = self.connection_users[websocket]

        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove from reverse lookup
        del self.connection_users[websocket]

        # Clean up channel subscriptions
        for channel, subscribers in list(self.channel_subscriptions.items()):
            subscribers.discard(user_id)
            if not subscribers:
                del self.channel_subscriptions[channel]

        logger.info(f"WebSocket disconnected: user_id={user_id}")

    async def subscribe(self, user_id: str, channels: list[str]) -> None:
        """Subscribe user to channels.

        Args:
            user_id: User ID to subscribe
            channels: List of channel names to subscribe to
        """
        for channel in channels:
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(user_id)

        logger.debug(f"User {user_id} subscribed to channels: {channels}")

    async def unsubscribe(self, user_id: str, channels: list[str]) -> None:
        """Unsubscribe user from channels.

        Args:
            user_id: User ID to unsubscribe
            channels: List of channel names to unsubscribe from
        """
        for channel in channels:
            if channel in self.channel_subscriptions:
                self.channel_subscriptions[channel].discard(user_id)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]

        logger.debug(f"User {user_id} unsubscribed from channels: {channels}")

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Send message to all connections for a specific user.

        Args:
            user_id: User ID to send message to
            message: Message dict to send (will be JSON serialized)
        """
        if user_id not in self.user_connections:
            logger.warning(f"No active connections for user {user_id}")
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = self._get_timestamp()

        dead_connections = set()

        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                dead_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(websocket)

    async def send_to_channel(self, channel: str, message: Dict[str, Any]) -> None:
        """Send message to all users subscribed to a channel.

        Args:
            channel: Channel name
            message: Message dict to send (will be JSON serialized)
        """
        if channel not in self.channel_subscriptions:
            logger.debug(f"No subscribers for channel {channel}")
            return

        # Add channel to message
        message["channel"] = channel

        subscribers = self.channel_subscriptions[channel].copy()
        for user_id in subscribers:
            await self.send_to_user(user_id, message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected users.

        Args:
            message: Message dict to send (will be JSON serialized)
        """
        user_ids = list(self.user_connections.keys())
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    # ========================================================================
    # HITL-SPECIFIC EVENT HELPERS
    # ========================================================================

    async def send_execution_awaiting_approval(
        self,
        user_id: str,
        execution_id: str,
        plan: Dict[str, Any],
    ) -> None:
        """Send HITL approval request event.

        Args:
            user_id: User to notify
            execution_id: Agent execution ID
            plan: The plan awaiting approval
        """
        await self.send_to_user(
            user_id=user_id,
            message={
                "type": "agent.execution.awaiting_approval",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": execution_id,
                    "status": "paused",
                    "plan": plan,
                    "approval_required": True,
                },
            }
        )

    async def send_execution_approved(
        self,
        user_id: str,
        execution_id: str,
        approved_by: str,
    ) -> None:
        """Send execution approved event.

        Args:
            user_id: User to notify
            execution_id: Agent execution ID
            approved_by: User ID who approved
        """
        await self.send_to_user(
            user_id=user_id,
            message={
                "type": "agent.execution.approved",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": execution_id,
                    "status": "running",
                    "approved_by": approved_by,
                },
            }
        )

    async def send_execution_progress(
        self,
        user_id: str,
        execution_id: str,
        current_step: Dict[str, Any],
    ) -> None:
        """Send execution progress update.

        Args:
            user_id: User to notify
            execution_id: Agent execution ID
            current_step: Current step information
        """
        await self.send_to_user(
            user_id=user_id,
            message={
                "type": "agent.execution.progress",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": execution_id,
                    "status": "running",
                    "current_step": current_step,
                },
            }
        )

    async def send_execution_completed(
        self,
        user_id: str,
        execution_id: str,
        message_id: str,
        stats: Dict[str, Any],
    ) -> None:
        """Send execution completed event.

        Args:
            user_id: User to notify
            execution_id: Agent execution ID
            message_id: Created message ID
            stats: Execution statistics
        """
        await self.send_to_user(
            user_id=user_id,
            message={
                "type": "agent.execution.completed",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": execution_id,
                    "message_id": message_id,
                    "status": "completed",
                    "stats": stats,
                },
            }
        )

    async def send_execution_failed(
        self,
        user_id: str,
        execution_id: str,
        error: Dict[str, str],
    ) -> None:
        """Send execution failed event.

        Args:
            user_id: User to notify
            execution_id: Agent execution ID
            error: Error information
        """
        await self.send_to_user(
            user_id=user_id,
            message={
                "type": "agent.execution.failed",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": error,
                },
            }
        )

    async def send_document_processing_update(
        self,
        user_id: str,
        document_id: str,
        status: str,
        progress: Dict[str, Any] = None,
    ) -> None:
        """Send document processing update.

        Args:
            user_id: User to notify
            document_id: Document being processed
            status: Processing status
            progress: Optional progress information
        """
        data = {
            "document_id": document_id,
            "status": status,
        }

        if progress:
            data["progress"] = progress

        await self.send_to_user(
            user_id=user_id,
            message={
                "type": f"document.processing.{status}",
                "channel": "document:processing",
                "data": data,
            }
        )

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        action: Dict[str, str] = None,
    ) -> None:
        """Send general notification to user.

        Args:
            user_id: User to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification (success, info, warning, error)
            action: Optional action with url and label
        """
        data = {
            "title": title,
            "message": message,
            "notification_type": notification_type,
        }

        if action:
            data["action"] = action

        await self.send_to_user(
            user_id=user_id,
            message={
                "type": "notification",
                "channel": f"user:{user_id}:notifications",
                "data": data,
            }
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.

        Returns:
            ISO formatted timestamp string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active connections
        """
        return len(self.user_connections.get(user_id, set()))

    def get_channel_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers for a channel.

        Args:
            channel: Channel name

        Returns:
            Number of subscribers
        """
        return len(self.channel_subscriptions.get(channel, set()))

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics.

        Returns:
            Dict with connection and subscription stats
        """
        return {
            "total_users_connected": len(self.user_connections),
            "total_connections": sum(len(conns) for conns in self.user_connections.values()),
            "total_channels": len(self.channel_subscriptions),
            "total_subscriptions": sum(len(subs) for subs in self.channel_subscriptions.values()),
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()
