
import json

from confluent_kafka import Consumer, KafkaError

from backend import config


class KafkaConsumer:

    def __init__(self, group_id: str):

        self.consumer = Consumer({
            "bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })

    def subscribe(self, topics: list[str]):
        self.consumer.subscribe(topics)

    def consume(self, timeout: float = 1.0):
        message = self.consumer.poll(timeout)

        if message is None:
            return None

        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                return None

            raise RuntimeError(
                f"Kafka consumer error: {message.error()}"
            )

        try:
            value = json.loads(message.value().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Invalid Kafka message: {error}"
            ) from error

        return message, value

    def commit(self, message):
        self.consumer.commit(
            message=message,
            asynchronous=False,
        )

    def close(self):
        self.consumer.close()
