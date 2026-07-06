# prefect/flows/kafka_to_delta.py
try:
    from prefect import flow, task
except ModuleNotFoundError:
    def flow(*_args, **_kwargs):
        def decorator(fn):
            return fn
        return decorator

    def task(fn):
        return fn
from kafka import KafkaConsumer
import json, os
import pandas as pd
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DELTA_LAKE_PATH = os.environ.get("DELTA_LAKE_PATH", "delta-lake/raw")

@task
def consume_and_process():
    """Consume data from Kafka topic"""
    consumer = KafkaConsumer(
        "data.raw",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,
        value_deserializer=lambda m: json.loads(m.decode())
    )
    records = []
    for msg in consumer:
        records.append(msg.value)

    print(f"Consumed {len(records)} records from Kafka")
    return records

@task
def save_to_delta(records):
    """Save records to Delta Lake (parquet format)"""
    if not records:
        print("No records to save")
        return
    
    df = pd.DataFrame(records)
    # Giả lập Delta Lake bằng parquet (local volume)
    path = DELTA_LAKE_PATH
    os.makedirs(path, exist_ok=True)
    df.to_parquet(f"{path}/batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet")
    print(f"Saved {len(df)} records to Delta Lake")

@flow(name="Kafka to Delta Pipeline", schedule="* */5 * * *")
def kafka_to_delta_flow():
    """Main flow: consume from Kafka and save to Delta Lake"""
    records = consume_and_process()
    save_to_delta(records)

if __name__ == "__main__":
    if os.environ.get("PREFECT_DEPLOY_FLOW") == "1":
        kafka_to_delta_flow.deploy(
            name="kafka-to-delta",
            work_queue_name="lab28-worker"
        )
    else:
        kafka_to_delta_flow()
