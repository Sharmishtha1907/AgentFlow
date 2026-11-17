
import json

from confluent_kafka import Producer

from backend import config 


class KafkaProducer:

    def __init__(self):
        self.producer = Producer({
            "bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "agentflow-outbox-publisher",
            "acks": "all",
            "enable.idempotence": True,
            "message.timeout.ms": 10000,
        })

    def publish(
        self,
        topic: str,
        key: str,
        value: dict,
    ):
        delivery_result = {}

        def delivery_callback(error, message):
            if error:
                delivery_result["error"] = str(error)
            else:
                delivery_result["message"] = message

        self.producer.produce(
            topic=topic,
            key=key,
            value=json.dumps(value),
            callback=delivery_callback,
        )

        remaining = self.producer.flush(timeout=15)

        if remaining > 0:
            raise TimeoutError(
                f"Kafka delivery timed out for topic: {topic}"
            )

        if "error" in delivery_result:
            raise RuntimeError(delivery_result["error"])

        if "message" not in delivery_result:
            raise RuntimeError("Kafka delivery was not confirmed")

        return delivery_result["message"]

    def close(self):
        remaining = self.producer.flush(timeout=15)

        if remaining > 0:
            raise RuntimeError(
                f"{remaining} Kafka messages were not delivered during shutdown"
            )
