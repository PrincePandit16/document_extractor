from dependency_injector import containers, providers
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
from app.services.file_service import FileService
from app.db.database import SessionLocal


class Container(containers.DeclarativeContainer):
    """DI container for application services."""

    wiring_config = containers.WiringConfiguration(
        modules=["app.api.routes"]
    )

    ocr_service = providers.Singleton(OCRService)
    llm_service = providers.Singleton(LLMService)
    file_service = providers.Singleton(FileService)
    db_session = providers.Factory(SessionLocal)


container = Container()
