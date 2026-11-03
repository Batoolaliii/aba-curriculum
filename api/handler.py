from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from controllers import employee_controller

app = FastAPI(title="HR Leave Portal")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.include_router(employee_controller.router)

lambda_handler = Mangum(app)

@app.get("/public/health")
def health():
    return {"status": "ok"}