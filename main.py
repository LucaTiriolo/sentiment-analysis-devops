from fastapi import FastAPI

# Creo l'applicazione FastAPI.
app = FastAPI()


# Endpoint base dell'applicazione.
@app.get("/")
def hello_world():
    return {"message": "Hello World"}