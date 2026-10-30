from fastapi import FastAPI

app = FastAPI(title="SE 480 hello service")


@app.get("/")
def hello():
    return {"message": "Hello to you as well. Tomorrow is the Halloween!"}


@app.get("/health")
def health():
    return {"status": "ok"}
