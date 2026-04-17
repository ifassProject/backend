from fastapi import FastAPI
from controllers.report_controller import router as report_router

app = FastAPI()


app.include_router(report_router)