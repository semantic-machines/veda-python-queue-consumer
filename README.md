# v-queue-python

Python bindings for [v-queue](https://github.com/semantic-machines/v-queue) - a persistent queue implementation in Rust.

## Features

- Queue creation and management
- Message publishing and consuming
- Support for multiple consumers
- Queue partitioning
- String and Object message types
- Read-only and read-write modes

## Installation

```bash
pip install v-queue-python
```

## Usage

### Basic Example

```python
from vqueue import Queue, Consumer, Mode, MsgType
import tempfile

# Create a queue
base_path = "./queue-data"
queue_name = "my_queue"
queue = Queue(base_path, queue_name, Mode.READ_WRITE)

# Push some messages
for i in range(5):
    msg = str(i).encode('utf-8')
    queue.push(msg, MsgType.STRING)

# Create a consumer and read messages
consumer = Consumer(base_path, "consumer1", queue_name)

while consumer.pop_header():
    message = consumer.pop_body()
    if message is not None:
        print(f"Received: {message.decode('utf-8')}")
        consumer.commit()
```

### Multiple Consumers

Each consumer receives all messages in the queue:

```python
# Create multiple consumers
consumer1 = Consumer(base_path, "consumer1", queue_name)
consumer2 = Consumer(base_path, "consumer2", queue_name)

# Each consumer will receive all messages
for consumer in [consumer1, consumer2]:
    while consumer.pop_header():
        message = consumer.pop_body()
        if message is not None:
            print(f"Consumer {consumer.name} received: {message.decode('utf-8')}")
            consumer.commit()
```

### Queue Partitioning

Queue can be partitioned by creating new Queue instances:

```python
# Create first part and write messages
queue1 = Queue(base_path, queue_name, Mode.READ_WRITE)
queue1.push(b"message1", MsgType.STRING)
queue1.push(b"message2", MsgType.STRING)

# Create second part
queue2 = Queue(base_path, queue_name, Mode.READ_WRITE)
queue2.push(b"message3", MsgType.STRING)
queue2.push(b"message4", MsgType.STRING)

# Existing consumers will read messages from all parts
# New consumers will start reading from the current part
```

## API Reference

### Queue

- `Queue(base_path: str, queue_name: str, mode: Mode)` - Create a new queue
- `push(data: bytes, msg_type: MsgType) -> int` - Push a message to the queue
- `count_pushed: int` - Number of messages pushed to the current part
- `name: str` - Queue name
- `is_ready: bool` - Queue status

### Consumer

- `Consumer(base_path: str, consumer_name: str, queue_name: str)` - Create a new consumer
- `Consumer.new_with_mode(base_path: str, consumer_name: str, queue_name: str, mode: Mode)` - Create a new consumer with specific mode
- `pop_header() -> bool` - Read message header
- `pop_body() -> Optional[bytes]` - Read message body
- `commit() -> bool` - Commit message read
- `get_batch_size() -> int` - Get number of available messages
- `count_popped: int` - Number of messages popped by this consumer
- `name: str` - Consumer name

### Enums

```python
class Mode:
    READ = 0
    READ_WRITE = 1
    DEFAULT = 2

class MsgType:
    STRING = b'S'
    OBJECT = b'O'
```

## Building from Source

Requirements:
- Python 3.7+
- Rust toolchain
- setuptools-rust

```bash
pip install setuptools-rust
pip install -e .
```

## License

MIT License - see [LICENSE](LICENSE) file for details. This project is a Python binding for [v-queue](https://github.com/semantic-machines/v-queue) which is also distributed under the MIT License.
