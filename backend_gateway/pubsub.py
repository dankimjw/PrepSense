"""Simple helper for publishing messages to Google Pub/Sub."""

from google.cloud import pubsub_v1


def publish_message(topic_name, message):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("your-project-id", topic_name)
    publisher.publish(topic_path, data=message.encode("utf-8"))
