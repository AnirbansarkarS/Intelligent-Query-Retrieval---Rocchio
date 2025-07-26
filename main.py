# This is the main entry point of the project.
# All core execution logic should be placed here.

# TODO: Soumabha will handle the FastAPI logic separately.
# If that code uses a different main file, we may need to merge it with this one.

def main():
	# Main application logic starts here
	print("hello world")

# Ensures this script only runs when executed directly,
# preventing accidental execution from other file
if __name__ == "__main__":
	main()
	from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}


from fastapi import FastAPI
from app.api import router

app = FastAPI()

app.include_router(router)
