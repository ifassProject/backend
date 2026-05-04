from fastapi import FastAPI
from controllers.report_controller import router as report_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()



origins = [
    "https://api.usoapnote.com",       
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(report_router)