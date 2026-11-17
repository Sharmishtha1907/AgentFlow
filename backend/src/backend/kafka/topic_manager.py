
from confluent_kafka.admin import AdminClient, NewTopic

from backend import config

TOPICS = [
    {
        "name": "agentflow.tasks",
        "partitions": 3,
        "replication_factor": 1,
    },
    {
        "name": "agentflow.task-results",
        "partitions": 3,
        "replication_factor": 1,
    },
    {
        "name": "agentflow.tasks.dlq",
        "partitions": 3,
        "replication_factor": 1,
    },
]


def create_topics():
    admin_client = AdminClient({
        "bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS
    })

    new_topics = [
        NewTopic(
            topic["name"],
            num_partitions=topic["partitions"],
            replication_factor=topic["replication_factor"],
        )
        for topic in TOPICS
    ]

    futures = admin_client.create_topics(
        new_topics,
        validate_only=False,
    )

    for topic_name, future in futures.items():
        try:
            future.result()
            print(f"Created topic: {topic_name}")

        except Exception as error:
            if "TOPIC_ALREADY_EXISTS" in str(error):
                print(f"Topic already exists: {topic_name}")
            else:
                print(f"Failed to create {topic_name}: {error}")


if __name__ == "__main__":
    create_topics()
