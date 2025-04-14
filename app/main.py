from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import context, langchain, reason, freeform

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
      "http://localhost:3000",
      "https://sessionm-loyaltyagent-142hz7s31-wt-mastercard.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(context.router, prefix="/context")
app.include_router(langchain.router)
app.include_router(reason.router)
app.include_router(freeform.router)