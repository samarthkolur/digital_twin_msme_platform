from fastapi import FastAPI

app = FastAPI(title="Digital Cousin Copilot")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
