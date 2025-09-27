import logging
import contextvars
import azure.functions as func

# Create a context variable for correlation ID
correlation_id_var = contextvars.ContextVar("correlation_id", default="unknown")

def set_current_correlation_id(correlation_id: str):
    correlation_id_var.set(correlation_id)

def get_current_correlation_id() -> str:
    return correlation_id_var.get()

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        # Inject correlationId into every log record automatically
        record.correlationId = get_current_correlation_id()
        return True

# Setup logger and add the filter once
logger = logging.getLogger("azure")
logger.setLevel(logging.INFO)

correlation_filter = CorrelationIdFilter()
logger.addFilter(correlation_filter)

# Optionally add a StreamHandler if running locally for console output
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(correlationId)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

app = func.FunctionApp()

@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="mysbqueue",
    connection="sbconnstring"
)
def servicebus_queue_trigger(msg: func.ServiceBusMessage):
    # Set correlationId from message properties into context var
    correlation_id = msg.user_properties.get("correlationId", "unknown")
    set_current_correlation_id(correlation_id)

    # Now every log message will have correlationId automatically injected
    logger.info(f"Processing ServiceBus message: {msg.get_body().decode('utf-8')}")
