#!/usr/bin/env python
from flask_login import current_user

import os
import sys
from app import create_app
from dmutils import init_manager
from context_processors import user_context

port = int(os.getenv('PORT', '5002'))
application = create_app(os.getenv('DM_ENVIRONMENT') or 'development')
manager = init_manager(application, port, ['./app/content/frameworks'])

application.logger.info('Command line: {}'.format(sys.argv))
application.context_processor(user_context)

if __name__ == '__main__':
    try:
        application.logger.info('Running manager')
        manager.run()
    finally:
        application.logger.info('Manager finished')
