from fastapi import FastAPI

app: FastAPI = FastAPI(title="AI Auto Job Applier", version="0.1.0")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
