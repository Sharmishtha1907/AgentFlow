
import time
import uuid

from backend.database.session import SessionLocal
from backend.database.crud.outbox_event_crud import (
    claim_unpublished_events,
    mark_event_as_published,
    update_event_failure,
)
from backend.kafka.producer import KafkaProducer


class OutboxPublisher:

    def __init__(
        self,
        batch_size: int = 10,
        lease_seconds: int = 60,
        poll_interval: int = 2,
    ):
        self.publisher_id = str(uuid.uuid4())
        self.batch_size = batch_size
        self.lease_seconds = lease_seconds
        self.poll_interval = poll_interval

        self.producer = KafkaProducer()

    def close(self):
        self.producer.close()

    
    def publish_batch(self):

        # Step 1: Claim events
        db = SessionLocal()

        try:
            events = claim_unpublished_events(
                publisher_id=self.publisher_id,
                batch_size=self.batch_size,
                lease_seconds=self.lease_seconds,
                db=db,
            )
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        # Step 2: Process claimed events
        for event in events:

            # Publish to Kafka
            try:
                self.publish_event(event)

            except Exception as error:

                # Kafka publishing failed
                db = SessionLocal()

                try:
                    update_event_failure(
                        event_id=event.id,
                        publisher_id=self.publisher_id,
                        error_message=str(error),
                        db=db,
                    )
                    db.commit()

                except Exception:
                    db.rollback()
                    raise

                finally:
                    db.close()

                continue

            # Kafka acknowledged delivery.
            # Now update PostgreSQL separately.
            db = SessionLocal()

            try:
                mark_event_as_published(
                    event_id=event.id,
                    publisher_id=self.publisher_id,
                    db=db,
                )
                db.commit()

            except Exception:
                db.rollback()
                raise

            finally:
                db.close()

        return len(events)

        
    def get_topic(self, event_type: str) -> str:
        topic_mapping = {
            "TASK_CREATED": "agentflow.tasks",
            "TASK_READY": "agentflow.tasks",
            "TASK_COMPLETED": "agentflow.task-results",
            "TASK_CANCELLED": "agentflow.tasks"
        }

        topic = topic_mapping.get(event_type)

        if topic is None:
            raise ValueError(f"Unsupported event type: {event_type}")

        return topic


    def publish_event(self, event):

        topic = self.get_topic(event.event_type)

        key = str(event.aggregate_id)

        value = {
            "event_id": str(event.id),
            "aggregate_type": event.aggregate_type,
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }

        self.producer.publish(
            topic=topic,
            key=key,
            value=value,
        )

    
    def run_forever(self):

        print(f"Outbox Publisher started: {self.publisher_id}")

        try:
            while True:

                try:
                    published_count = self.publish_batch()

                    if published_count == 0:
                        time.sleep(self.poll_interval)

                except Exception as error:
                    print(f"Publisher error: {error}")
                    time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("Outbox Publisher shutting down...")

        finally:
            self.close()



if __name__ == "__main__":
    publisher = OutboxPublisher()
    publisher.run_forever()
