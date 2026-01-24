# Corrected main.py

# Assuming SERVICOS is a list or dictionary of services
SERVICOS = {"service1": "details1", "service2": "details2"}

# Function that uses SERVICOS consistently

def perform_service(service_name):
    if service_name in SERVICOS:
        return f"Performing {service_name} with details: {SERVICOS[service_name]}"
    else:
        raise NameError(f"Service {service_name} not found.")

# Function to reset the database

def reset_db():
    print("Database reset button clicked!")
    # Logic for resetting DB here

# Additional minor fixes can go here
