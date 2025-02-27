# =============================================================================
# Sample for client to access AI server on cloud
#
# How to use
# $ python sample_cloud_ai_serving_infrastructure.py <ai_type> <model_spec>
#     <model_spec> is a value of model specs below.
# =============================================================================
"""
This module provides a sample for client to access AI server on cloud.
"""
import sys
import traceback
import logging
# import os

import forxai_base
import forxai_recognition


# Change path as your cloud environment
CRT_FILE_PATH = 'ca/private-server.crt'

# Change URI as your ELB's endpoint
HOST_SERVER_URI = "iap-elb-1384164427.ap-northeast-1.elb.amazonaws.com"

# Change json of auth info as your authenticate information
AUTH_INFO = '{"user_id":"user-id", "user_key":"user-key"}'

HOST_SERVER_PORT = 52001

IMAGE_FILE = 'data/test_image.jpg'


# =============================================================================
# functions
# =============================================================================
def exec_infer(client_obj: forxai_recognition.Client,
               image_path: str, logger_obj: logging.Logger):
    '''
    Execute inference and log the results.
    '''
    # Exec inference
    results = client_obj.input(image_path)

    if results is None:
        logger_obj.debug("inference results is None")
        return

    # Print result
    for result in results:
        logger_obj.debug(result)


# =============================================================================
# main
# =============================================================================
if __name__ == "__main__":
    # Set proxy on windows
    # os.environ['http_proxy'] = 'http://g3.konicaminolta.jp:8080'
    # os.environ['https_proxy'] = 'http://g3.konicaminolta.jp:8080'

    # Prepare Logger to print debug log with time
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s  %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Get arguments
    args = sys.argv
    if len(args) != 3:
        logger.debug("argument num error")
        sys.stdout.write("NG_arg_num_err")
        sys.exit(1)

    ai_type_val = args[1]
    model_spec_val = args[2]

    # Start
    logger.debug("start")
    try:
        # Open & read certificate file to connect server on cloud
        with open(CRT_FILE_PATH, 'rb') as f:
            crt = f.read()

        logger.debug("ai type: %s", ai_type_val)
        logger.debug("model spec: %s", model_spec_val)

        # Open session to server
        client = forxai_base.Client(
            host=HOST_SERVER_URI, port=HOST_SERVER_PORT,
            type_name=ai_type_val, model_spec=model_spec_val,
            tls=True, root_certificates=crt,
            auth_info=AUTH_INFO)
        # If there is no server available, exception occurs.
        # After that it goes except section,
        # then it starts launch server & open session.

        # Execute inference & print result
        exec_infer(client, IMAGE_FILE, logger)

    except forxai_base.ServerError as e:
        logger.debug(e)
        # If error of "NO_SERVER_AVAILABLE" happens, launch AI server
        if e.error.value == forxai_base.Error.NO_SERVER_AVAILABLE:
            try:
                logger.debug("launch server & open session")
                # Launch server & open session to the server
                obj = forxai_base.Client.obtain_session(
                    host=HOST_SERVER_URI, port=HOST_SERVER_PORT,
                    type_name=ai_type_val,
                    model_spec=model_spec_val,
                    tls=True, root_certificates=crt,
                    auth_info=AUTH_INFO)
                # Wait until server has started, this may take several minutes
                for p in obj:
                    logger.debug("now connecting: %d / %d",
                                 p.current_count, p.scheduled_count)
                cli = obj.client()
                client = forxai_recognition.Client(client=cli)

                # Execute inference & print result
                exec_infer(client, IMAGE_FILE, logger)

            except forxai_base.ServerError as e_launch:
                logger.debug(e_launch)
                logger.debug(traceback.format_exc())
                sys.stdout.write("NG_launch_server")
                sys.exit(1)
        else:
            logger.debug(traceback.format_exc())
            sys.stdout.write("NG_open_session")
            sys.exit(1)
    finally:
        try:
            # Close session
            client.close()
            logger.debug("close_session")
        except Exception as e:
            logger.debug(e)
            sys.stdout.write("NG_close_session")
            sys.exit(1)
