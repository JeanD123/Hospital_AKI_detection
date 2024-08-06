import os
from prometheus_client import Counter, Gauge

# Configure the database file names
DATA_DIRECTORY = '../data/'

PATIENTS_FILE = os.path.join(DATA_DIRECTORY, 'patients.csv')
RESULTS_FILE = os.path.join(DATA_DIRECTORY, 'results.csv')
HISTORY_FILE = os.path.join(DATA_DIRECTORY, 'history.csv')
UNPAGED_FILE = os.path.join(DATA_DIRECTORY, 'unpaged_patients.csv')

# Configure the MLLP and socket
MLLP_SOCKET = os.getenv("MLLP_ADDRESS")
PAGER_SOCKET = os.getenv("PAGER_ADDRESS")

MLLP_START_OF_BLOCK = 0x0b
MLLP_END_OF_BLOCK = 0x1c
MLLP_CARRIAGE_RETURN = 0x0d

BUFFER_SIZE = 1024
MAX_PAGE_ATTEMPTS = 100

# Model
MODEL_DIRECTORY = '../model/'
MODEL = os.path.join(MODEL_DIRECTORY, 'xgboost_model.model')

# Dictionary maps
MAP_SEX = {'M': 1, 'F': 0}

# Others
VERBOSE = False

# Error Handling
TIME_TO_RETRY_SOCKET_CONNECTION = 1 # seconds

# Metrics
MAX_LENGTH_RESULTS = 1000

MESSAGES_COUNTER = Counter('total_number_of_messages_received', 'Number of messages received')
SOCKET_COUNTER = Counter('MLP_socket_reconnections_counter', 'Number of reconnections to the MLLP socket')
RESULTS_COUNTER = Counter('total_number_of_results_received', 'Number of blood test results received')
ADMITTED_PATIENTS = Counter('admitted_number_of_patients', 'Number of admitted patients')
DISCHARGED_PATIENTS = Counter('discharged_number_of_patients', 'Number of discharged patients')
FLAG_COUNT = Counter('flagged_results', 'Number of flagged results')
HTTP_RECONNECTIONS = Counter('http_errors_metric', 'The number of times the pager HTTP request returned anything other than status 200 (UK)')
POSITIVE_RATE = Gauge('positive_rate_prediction', 'Positive rate prediction of AKI')
RUNNING_LATENCY_MEAN = Gauge('running_latency_mean', 'Running mean of the latency')
MEDIAN_CREATINE = Gauge('median_creatine_result', 'median creatine result')
WARNINGS = Counter('number_of_warnings', 'Number_of_warnings_received')
EXIT_RECEIVED = Counter('number_of_exits', 'number_of_exits_received')
ERRORS = Counter('number_of_errors', 'Number_of_errors_received')