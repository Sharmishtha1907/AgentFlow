
import os

from dotenv import load_dotenv


load_dotenv()

DB_USER=os.getenv('DB_USER')
DB_PASSWORD=os.getenv('DB_PASSWORD')
DB_HOST=os.getenv('DB_HOST')
DB_PORT=os.getenv('DB_PORT')
DB_NAME=os.getenv('DB_NAME')
KAFKA_BOOTSTRAP_SERVERS =str("localhost:9092")
