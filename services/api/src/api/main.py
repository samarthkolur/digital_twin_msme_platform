from fastapi import FastAPI

app = FastAPI(title="Digital Cousin API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
