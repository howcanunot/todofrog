import logging
from datetime import datetime
from src.settings import get_settings

# ANSI escape codes for colors
COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
}

class ColoredFormatter(logging.Formatter):
    LEVEL_COLORS = {
        'DEBUG': COLORS['BLUE'],
        'INFO': COLORS['GREEN'],
        'WARNING': COLORS['YELLOW'],
        'ERROR': COLORS['RED'],
        'CRITICAL': COLORS['MAGENTA'],
    }

    def __init__(self, use_colors=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors

    def format(self, record):
        if self.use_colors:
            level_color = self.LEVEL_COLORS.get(record.levelname, COLORS['WHITE'])
            record.levelname = f"{level_color}{record.levelname:<5}{COLORS['RESET']}"
            
            record_name = record.filename + ":" + str(record.lineno)
            record.name = f"{COLORS['CYAN']}{record_name:<12}{COLORS['RESET']}"
        else:
            record.levelname = f"{record.levelname:<5}"
            record.name = f"{record.filename}:{record.lineno:<12}"

        return super().format(record)

def setup_logger():
    settings = get_settings()
    formatter = ColoredFormatter(
        use_colors=settings.dev_mode,
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    return logger

logger = setup_logger()
