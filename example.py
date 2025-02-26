from vqueue import Queue, Consumer, Mode, MsgType
import tempfile
import os
import json

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

def test_individual_to_json_conversion():
    print("\nTesting Individual to JSON conversion...")
    
    with tempfile.TemporaryDirectory() as base_path:
        queue_name = "individual_queue"
        
        # Create a queue
        queue = Queue(base_path, queue_name, Mode.READ_WRITE)
        
        # Sample data that represents a serialized Individual
        # In a real application, this would be created by a Rust program using the Individual model
        individual_data = b'''
        {
          "@": "example:person1",
          "rdf:type": [{"data": "Person", "type": "Uri"}],
          "name": [{"data": "John Doe", "type": "String"}],
          "age": [{"data": 30, "type": "Integer"}],
          "active": [{"data": true, "type": "Boolean"}]
        }
        '''
        
        # Push the Individual data to the queue
        queue.push(individual_data, MsgType.OBJECT)
        print("Pushed Individual data to queue")
        
        # Create a consumer
        consumer = Consumer(base_path, "individual_consumer", queue_name)
        
        # Read the message and convert to JSON
        if consumer.pop_header():
            binary_data = consumer.pop_body()
            if binary_data is not None:
                print(f"Received binary data, length: {len(binary_data)} bytes")
                
                try:
                    # Convert binary data to JSON using the static method
                    json_str = Consumer.convert_individual_to_json(binary_data)
                    print("Successfully converted Individual to JSON")
                    
                    # Parse JSON to Python object
                    data = json.loads(json_str)
                    
                    # Verify the content
                    assert "@" in data, "Missing URI in converted data"
                    assert data["@"] == "example:person1", "URI doesn't match expected value"
                    assert "name" in data, "Missing 'name' predicate"
                    assert "age" in data, "Missing 'age' predicate"
                    assert "active" in data, "Missing 'active' predicate"
                    
                    # Print Individual structure
                    print(f"Individual URI: {data['@']}")
                    for predicate, values in data.items():
                        if predicate != '@':
                            print(f"Predicate: {predicate}, Values: {values}")
                    
                    consumer.commit()
                    print("Individual conversion test passed")
                    
                except Exception as e:
                    print(f"Error converting to JSON: {e}")
                    assert False, f"JSON conversion failed: {e}"
            else:
                assert False, "Failed to read message body"
        else:
            assert False, "Failed to read message header"
        
    # Test direct conversion without using a queue
    print("\nTesting direct conversion of binary data...")
    
    # This could be binary data from any source
    direct_binary_data = b'''
    {
      "@": "example:direct1",
      "rdf:type": [{"data": "DirectTest", "type": "Uri"}],
      "description": [{"data": "Test of direct conversion", "type": "String"}],
      "value": [{"data": 42, "type": "Integer"}]
    }
    '''
    
    try:
        # Convert directly without going through the queue
        json_str = Consumer.convert_individual_to_json(direct_binary_data)
        print("Successfully converted direct binary data to JSON")
        
        # Parse the JSON
        data = json.loads(json_str)
        
        # Verify the content
        assert "@" in data, "Missing URI in directly converted data"
        assert data["@"] == "example:direct1", "URI doesn't match expected value"
        assert "description" in data, "Missing 'description' predicate"
        assert "value" in data, "Missing 'value' predicate"
        
        print(f"Direct Individual URI: {data['@']}")
        print(f"Found {len(data) - 1} predicates")  # -1 for the '@' field
        print("Direct conversion test passed")
        
    except Exception as e:
        print(f"Error in direct conversion: {e}")
        assert False, f"Direct JSON conversion failed: {e}"

if __name__ == "__main__":
    test_queue_consumer_interaction()
    print("\n---\n")
    test_multiple_consumers()
    print("\n---\n")
    test_queue_parts()
    print("\n---\n")
    test_individual_to_json_conversion()
