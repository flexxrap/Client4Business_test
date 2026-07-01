import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("app.events")


class EventPublisher(ABC):
    @abstractmethod
    def publish(
        self, event_type: str, request_id: str, workspace_id: str, actor_user_id: str
    ) -> None:
        raise NotImplementedError


class NoOpEventPublisher(EventPublisher):
    def publish(
        self, event_type: str, request_id: str, workspace_id: str, actor_user_id: str
    ) -> None:
        logger.info(
            "event_type=%s request_id=%s workspace_id=%s actor_user_id=%s",
            event_type,
            request_id,
            workspace_id,
            actor_user_id,
        )


event_publisher = NoOpEventPublisher()


def get_event_publisher() -> EventPublisher:
    return event_publisher
