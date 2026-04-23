import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(file_name: str, logger_name: str = "app_logger", file_size_mb: int = 10, backup_count: int = 3):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, file_name)

    # --- Formato de logs ---
    log_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s(%(lineno)d) | %(message)s'
    )

    # --- Handler de archivo con rotación ---
    _file_handler = RotatingFileHandler(
        log_filename,
        maxBytes = file_size_mb * 1024 * 1024,  # 10 MB
        backupCount=backup_count,
        encoding='utf-8'
    )
    _file_handler.setFormatter(log_formatter)

    # --- Logger principal ---
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.DEBUG)
    if not _logger.hasHandlers():
        _logger.addHandler(_file_handler)

    return _logger, _file_handler


# --- Configuración de directorio y archivo de logs ---
logger, file_handler = setup_logger('app.log')

# --- Sobrescribir loggers de Uvicorn para que también escriban en archivo ---
for uvicorn_logger_name in ["uvicorn.access", "uvicorn.error"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.handlers = []  # eliminamos handlers por defecto
    uvicorn_logger.addHandler(file_handler)
    uvicorn_logger.propagate = False
