import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine
from .db.models.base import Base
from .api.router import api_router
from .api.v1.endpoints import auth as auth_endpoints
from .api.v1.endpoints import websockets as websockets_endpoints
from .api.v1.endpoints import identities as identities_endpoints
from .core.kafka_consumer import EventConsumer
from .core.logging_config import configure_logging


from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

                                                             
from .db.models import risk              
from .db.models import security_alert              


@asynccontextmanager
async def lifespan(app: FastAPI):
             
    enable_consumer = os.getenv("ENABLE_KAFKA_CONSUMER", "true").lower() not in {
        "0",
        "false",
        "no",
    }
    consumer = None
    consumer_task = None
    if enable_consumer:
        try:
            consumer = EventConsumer()
            await consumer.start()
            consumer_task = asyncio.create_task(consumer.consume_loop())
            app.state.kafka_consumer = consumer
            app.state.kafka_consumer_task = consumer_task
        except Exception as exc:
                                                            
            app.state.kafka_consumer = None
            app.state.kafka_consumer_task = None
            try:
                if consumer is not None:
                    await consumer.stop()
            except Exception:
                pass
            logging.getLogger("risk_analysis.kafka").warning(
                "Kafka consumer disabled due to startup error: %s", exc
            )
    else:
        app.state.kafka_consumer = None
        app.state.kafka_consumer_task = None
    try:
        yield
    finally:
                  
        try:
            if app.state.kafka_consumer is not None:
                await app.state.kafka_consumer.stop()
        except Exception:
            pass
        try:
            if app.state.kafka_consumer_task is not None:
                                                                          
                app.state.kafka_consumer_task.cancel()
                try:
                    await app.state.kafka_consumer_task
                except Exception:
                    pass
        except Exception:
            pass


app = FastAPI(
    title="Risk Analysis Service",
    description="Сервіс для аналізу ризиків конфігурацій хмарних ресурсів.",
    version="1.0.0",
    lifespan=lifespan,
)


                                               
configure_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def create_tables_on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(api_router)
app.include_router(auth_endpoints.router, prefix="/v1")
                                                                             
app.include_router(auth_endpoints.router, prefix="/api/v1")
app.include_router(websockets_endpoints.router, prefix="/v1")
app.include_router(websockets_endpoints.router, prefix="/api/v1")
app.include_router(identities_endpoints.router, prefix="/v1")
app.include_router(identities_endpoints.router, prefix="/api/v1")

logger = logging.getLogger("risk_analysis.api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = (await request.body()).decode("utf-8", "ignore")
    logger.exception("Validation error: %s body=%s", exc.errors(), body)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
