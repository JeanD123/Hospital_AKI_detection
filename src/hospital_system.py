import socket
import argparse
import time
from xgboost import XGBClassifier
from hospital_communication import *
from config import MLLP_SOCKET, BUFFER_SIZE, MODEL, TIME_TO_RETRY_SOCKET_CONNECTION, HISTORY_FILE, RESULTS_FILE, PATIENTS_FILE, UNPAGED_FILE, MESSAGES_COUNTER, SOCKET_COUNTER, RUNNING_LATENCY_MEAN, RESULTS_COUNTER, EXIT_RECEIVED, ERRORS
from message_distributor import MessageProcessor
import signal
import time
import logging
from prometheus_client import start_http_server

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GracefulAKIKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    self.kill_now = True
    raise KeyboardInterrupt("Received SIGINT or SIGTERM. Graceful shutdown:)")
  

def main(flags):
    # Initial states
    message_received = True

    loaded_model = XGBClassifier()
    loaded_model.load_model(MODEL)

    while True:
        try:
            # Connect to input socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as input_socket:
                host, num = MLLP_SOCKET.split(':')
                input_socket.connect((host, int(num)))

                message_processor = MessageProcessor(loaded_model, flags.patients, flags.results, flags.history, flags.unpaged)
                
                # Listen until messages are empty
                while True:
                
                        # Receive message
                        buffer = input_socket.recv(BUFFER_SIZE)

                        start_time = time.time()
                        
                        # If message is empty break loop - no message
                        if len(buffer) == 0:
                            break
                        
                        # Extract and parse message from MLLP protocol
                        message = from_mllp(buffer)
                        MESSAGES_COUNTER.inc() 
                        is_result = message_processor.process_message(message)

                        # If message_received respond AA for a new message, else AR
                        acknowledged = [message[0], 'MSA|AA'] if message_received else [message[0], 'MSA|AR']

                        # Respond
                        input_socket.sendall(to_mllp(acknowledged))

                        # Store result into HDD after inference
                        if is_result:
                            end_time = time.time()
                            latency = end_time - start_time
                            running_mean = RUNNING_LATENCY_MEAN._value.get()
                            num_results = RESULTS_COUNTER._value.get()
                            RUNNING_LATENCY_MEAN.set((running_mean * (num_results - 1) + latency) / num_results)
                            message_processor.store_creatine()

        except socket.error as e:
            SOCKET_COUNTER.inc()
            logging.error("Socket error: %s. Retrying in 1 seconds...", e)
            time.sleep(TIME_TO_RETRY_SOCKET_CONNECTION)
            continue
        except Exception as ex:
            ERRORS.inc()
            logging.error("Unexpected error: %s", ex)
        finally:
            if input_socket:
                input_socket.close()
        

if __name__ == "__main__":
    start_http_server(8000)  
    killer = GracefulAKIKiller()
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default=HISTORY_FILE)
    parser.add_argument("--results", default=RESULTS_FILE)
    parser.add_argument("--patients", default=PATIENTS_FILE)
    parser.add_argument("--unpaged", default=UNPAGED_FILE)
    flags = parser.parse_args()
    while not killer.kill_now:
        try:
            main(flags)
        except KeyboardInterrupt:
            EXIT_RECEIVED.inc()
            print("Received SIGINT or SIGTERM. Graceful shutdown:)")
            break