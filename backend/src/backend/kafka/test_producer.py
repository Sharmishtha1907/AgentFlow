
from backend.kafka.producer import KafkaProducer

producer = KafkaProducer()

try:
    message = producer.publish(
        topic="agentflow.tasks",
        key="test-task-001",
        value={
            "event_id": "test-event-001",
            "event_type": "TASK_READY",
            "payload": {
                "task_id": "test-task-001",
                "description": "Test Kafka connectivity",
            },
        },
    )

    print("Message delivered successfully!")
    print("Topic:", message.topic())
    print("Partition:", message.partition())
    print("Offset:", message.offset())

finally:
    producer.close()
