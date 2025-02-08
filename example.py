from vqueue import Queue, Consumer, Mode, MsgType
import tempfile
import os

def test_queue_consumer_interaction():
    # Create a temporary directory for the queue
    with tempfile.TemporaryDirectory() as base_path:
        queue_name = "test_queue"
        
        # Create a queue and write some messages
        queue = Queue(base_path, queue_name, Mode.READ_WRITE)
        num_messages = 10
        
        for i in range(num_messages):
            msg = str(i).encode('utf-8')
            queue.push(msg, MsgType.STRING)
            
        print(f"Pushed {queue.count_pushed} messages")
        
        # Create a consumer and read messages
        consumer_name = "consumer1"
        consumer = Consumer(base_path, consumer_name, queue_name)
        
        received_messages = []
        while consumer.pop_header():
            message = consumer.pop_body()
            if message is not None:
                received_messages.append(int(message.decode('utf-8')))
                consumer.commit()
                
        print(f"Received {len(received_messages)} messages")
        print(f"Messages: {received_messages}")
        
        # Verify message integrity
        assert len(received_messages) == num_messages
        assert received_messages == list(range(num_messages))
        
        print("All messages received correctly")

def test_multiple_consumers():
    with tempfile.TemporaryDirectory() as base_path:
        queue_name = "test_queue"
        queue = Queue(base_path, queue_name, Mode.READ_WRITE)
        
        # Push some messages
        num_messages = 20
        for i in range(num_messages):
            msg = str(i).encode('utf-8')
            queue.push(msg, MsgType.STRING)
            
        # Create multiple consumers
        num_consumers = 3
        consumers = []
        received_messages = []
        
        for i in range(num_consumers):
            consumer = Consumer(base_path, f"consumer{i}", queue_name)
            consumers.append(consumer)
            received_messages.append([])
            
        # Each consumer reads all messages
        for i, consumer in enumerate(consumers):
            while consumer.pop_header():
                message = consumer.pop_body()
                if message is not None:
                    received_messages[i].append(int(message.decode('utf-8')))
                    consumer.commit()
                    
        # Print results
        for i, messages in enumerate(received_messages):
            print(f"Consumer {i} received: {sorted(messages)}")
            
        # Verify that each consumer received all messages
        expected_messages = list(range(num_messages))
        for messages in received_messages:
            assert sorted(messages) == expected_messages, "Consumer did not receive all messages"
        
        print("All consumers received all messages correctly")

def test_queue_parts():
    with tempfile.TemporaryDirectory() as base_path:
        queue_name = "test_queue"
        print("\nTesting queue parts...")
        
        # Create first part of the queue and write messages
        print("Writing to part 1...")
        queue1 = Queue(base_path, queue_name, Mode.READ_WRITE)
        num_messages_part1 = 5
        
        for i in range(num_messages_part1):
            msg = str(i).encode('utf-8')
            queue1.push(msg, MsgType.STRING)
        
        print(f"Part 1 created with {queue1.count_pushed} messages")
        
        # Create consumer and start reading from part 1
        consumer = Consumer(base_path, "consumer1", queue_name)
        
        # Read messages from part 1
        messages_part1 = []
        while consumer.pop_header():
            message = consumer.pop_body()
            if message is not None:
                messages_part1.append(int(message.decode('utf-8')))
                consumer.commit()
        
        print(f"Read from part 1: {messages_part1}")
        assert len(messages_part1) == num_messages_part1
        assert messages_part1 == list(range(num_messages_part1))
        
        # Create second part by creating new Queue instance
        print("\nWriting to part 2...")
        queue2 = Queue(base_path, queue_name, Mode.READ_WRITE)
        num_messages_part2 = 7
        
        for i in range(num_messages_part2):
            msg = str(i + num_messages_part1).encode('utf-8')
            queue2.push(msg, MsgType.STRING)
            
        print(f"Part 2 created with {queue2.count_pushed} messages")
        
        # Existing consumer should read new messages from part 2
        messages_part2 = []
        while consumer.pop_header():
            message = consumer.pop_body()
            if message is not None:
                messages_part2.append(int(message.decode('utf-8')))
                consumer.commit()
        
        print(f"Same consumer read from part 2: {messages_part2}")
        assert len(messages_part2) == num_messages_part2
        assert messages_part2 == list(range(num_messages_part1, num_messages_part1 + num_messages_part2))
        
        # Create new consumer
        print("\nReading with new consumer...")
        new_consumer = Consumer(base_path, "consumer2", queue_name)
        all_messages = []
        
        while new_consumer.pop_header():
            message = new_consumer.pop_body()
            if message is not None:
                all_messages.append(int(message.decode('utf-8')))
                new_consumer.commit()
        
        print(f"New consumer messages: {all_messages}")
        # New consumer should read messages from the current part
        assert len(all_messages) == num_messages_part2
        assert all_messages == list(range(num_messages_part1, num_messages_part1 + num_messages_part2))
        
        print("Queue parts test completed successfully!")

if __name__ == "__main__":
    test_queue_consumer_interaction()
    print("\n---\n")
    test_multiple_consumers()
    print("\n---\n")
    test_queue_parts()
