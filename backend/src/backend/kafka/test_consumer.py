
from backend.kafka.consumer import KafkaConsumer


consumer = KafkaConsumer(
    group_id="agentflow-consumer-test"
)

try:
    consumer.subscribe(["agentflow.tasks"])

    print("Waiting for Kafka messages...")

    while True:
        result = consumer.consume(timeout=1.0)

        if result is None:
            continue

        message, event = result

        print("\nMessage received:")
        print("Topic:", message.topic())
        print("Partition:", message.partition())
        print("Offset:", message.offset())
        print("Event:", event)

        consumer.commit(message)

        print("Offset committed successfully!")

finally:
    consumer.close()
